"""
KnowledgeGraph: The core class for NuSy-nano.

Provides hybrid search over Yurtle markdown files, combining:
- Semantic search via txtai embeddings
- Structured queries via RDFlib SPARQL
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union
import yurtle_rdflib
from rdflib import Namespace

try:
    from txtai.embeddings import Embeddings
except ImportError:
    raise ImportError(
        "txtai is required. Install with: pip install nusy-nano\n"
        "Or: pip install txtai[pipeline]"
    )


# Standard namespaces
YURTLE = Namespace("https://yurtle.dev/schema/")
PROV = Namespace("https://yurtle.dev/provenance/")


@dataclass
class SearchResult:
    """A search result from the knowledge graph."""

    title: str
    path: str
    score: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __repr__(self):
        return f"SearchResult('{self.title}', score={self.score:.3f})"

    def read(self) -> str:
        """Read the full content of this document."""
        return Path(self.path).read_text()

    def read_prose(self) -> str:
        """Read just the prose content (no frontmatter)."""
        content = self.read()
        return _extract_prose(content)


def _extract_prose(content: str) -> str:
    """Extract prose from markdown, skipping frontmatter and code blocks."""
    lines = []
    in_frontmatter = False
    in_code_block = False
    frontmatter_count = 0

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped == "---":
            frontmatter_count += 1
            if frontmatter_count <= 2:
                in_frontmatter = not in_frontmatter
                continue

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if not in_frontmatter and not in_code_block:
            lines.append(line)

    return "\n".join(lines).strip()


class KnowledgeGraph:
    """
    A knowledge graph backed by Yurtle markdown files.

    Provides both semantic search (via txtai) and structured queries
    (via SPARQL/RDFlib) over the same set of documents.

    Example:
        kg = KnowledgeGraph("knowledge/")

        # Semantic search
        results = kg.search("blood sugar")

        # Structured query
        results = kg.query("SELECT ?x WHERE { ?x a :lab-test }")

        # Hybrid search
        results = kg.hybrid_search("diabetes", filters={"type": "lab-test"})
    """

    def __init__(
        self,
        path: Union[str, Path],
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        glob_pattern: str = "**/*.md",
    ):
        """
        Initialize a knowledge graph from a directory of Yurtle files.

        Args:
            path: Path to directory containing .md files
            model: Sentence transformer model for embeddings
            glob_pattern: Pattern for finding markdown files
        """
        self.workspace = Path(path)
        if not self.workspace.exists():
            raise ValueError(f"Path not found: {path}")

        self.glob_pattern = glob_pattern

        # Load structured graph via yurtle-rdflib
        self.graph = yurtle_rdflib.load_workspace(str(self.workspace))

        # Build semantic index
        self.embeddings = Embeddings({"path": model})
        self._index_documents()

    def _index_documents(self):
        """Index all markdown files for semantic search."""
        documents = []

        for md_file in self.workspace.glob(self.glob_pattern):
            # Skip README files
            if md_file.name.upper().startswith("README"):
                continue

            try:
                content = md_file.read_text()
                prose = _extract_prose(content)

                if prose and len(prose) > 20:
                    documents.append((str(md_file), prose))
            except Exception as e:
                print(f"Warning: Could not index {md_file}: {e}")

        if documents:
            self.embeddings.index(documents)

        self._document_count = len(documents)

    def __len__(self) -> int:
        """Number of documents in the knowledge graph."""
        return self._document_count

    def __repr__(self) -> str:
        return f"KnowledgeGraph('{self.workspace}', documents={len(self)})"

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        Semantic search over document prose content.

        Args:
            query: Natural language search query
            top_k: Number of results to return

        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not self._document_count:
            return []

        results = self.embeddings.search(query, top_k)
        return [
            SearchResult(
                title=self._path_to_title(path),
                path=path,
                score=score,
            )
            for score, path in results
        ]

    def query(self, sparql: str) -> list[dict]:
        """
        Execute a SPARQL query over the structured graph.

        Args:
            sparql: SPARQL query string (prefixes added automatically)

        Returns:
            List of result dictionaries
        """
        # Add common prefixes if not present
        if "PREFIX" not in sparql.upper():
            sparql = f"""
                PREFIX yurtle: <https://yurtle.dev/schema/>
                PREFIX prov: <https://yurtle.dev/provenance/>
                PREFIX : <https://yurtle.dev/schema/>
                {sparql}
            """

        results = self.graph.query(sparql)
        return [dict(zip(results.vars, row)) for row in results]

    def hybrid_search(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Hybrid search: semantic similarity with structured filters.

        Args:
            query: Natural language search query
            filters: Dict of property filters (e.g., {"type": "lab-test"})
            top_k: Number of results to return

        Returns:
            List of SearchResult objects matching both criteria
        """
        if not self._document_count:
            return []

        # Get semantic candidates
        candidates = self.embeddings.search(query, top_k * 3)

        if not filters:
            # No filters, just return top semantic results
            return [
                SearchResult(
                    title=self._path_to_title(path),
                    path=path,
                    score=score,
                )
                for score, path in candidates
            ][:top_k]

        # Apply structured filters
        results = []
        for score, path in candidates:
            # Check if document matches filters
            if self._matches_filters(path, filters):
                metadata = self._get_metadata(path)
                results.append(
                    SearchResult(
                        title=self._path_to_title(path),
                        path=path,
                        score=score,
                        metadata=metadata,
                    )
                )
                if len(results) >= top_k:
                    break

        return results

    def find_related(self, doc_path: str, top_k: int = 5) -> list[SearchResult]:
        """
        Find documents related to a given document.

        Args:
            doc_path: Path to the source document
            top_k: Number of related documents to return

        Returns:
            List of related SearchResult objects
        """
        path = Path(doc_path)
        if not path.exists():
            raise ValueError(f"Document not found: {doc_path}")

        content = path.read_text()
        prose = _extract_prose(content)

        if not prose:
            return []

        results = self.embeddings.search(prose, top_k + 1)

        return [
            SearchResult(
                title=self._path_to_title(p),
                path=p,
                score=s,
            )
            for s, p in results
            if Path(p).resolve() != path.resolve()
        ][:top_k]

    def get(self, doc_id: str) -> Optional[SearchResult]:
        """
        Get a specific document by ID.

        Args:
            doc_id: Document ID (from frontmatter)

        Returns:
            SearchResult if found, None otherwise
        """
        results = self.query(f"""
            SELECT ?file ?title WHERE {{
                ?doc yurtle:id "{doc_id}" ;
                     yurtle:title ?title ;
                     prov:definedIn ?file .
            }}
        """)

        if results:
            row = results[0]
            return SearchResult(
                title=str(row.get("title", doc_id)),
                path=str(row.get("file", "")),
                metadata={"id": doc_id},
            )
        return None

    def _matches_filters(self, path: str, filters: dict) -> bool:
        """Check if a document matches the given filters."""
        for key, value in filters.items():
            # Build SPARQL ASK query
            query = f"""
                ASK {{
                    ?doc prov:definedIn ?file ;
                         yurtle:{key} "{value}" .
                    FILTER(CONTAINS(STR(?file), "{Path(path).name}"))
                }}
            """
            try:
                result = self.graph.query(query)
                if not bool(result):
                    return False
            except Exception:
                return False

        return True

    def _get_metadata(self, path: str) -> dict:
        """Get structured metadata for a document."""
        query = f"""
            SELECT ?p ?o WHERE {{
                ?doc prov:definedIn ?file ;
                     ?p ?o .
                FILTER(CONTAINS(STR(?file), "{Path(path).name}"))
                FILTER(STRSTARTS(STR(?p), "https://yurtle.dev/"))
            }}
        """
        try:
            results = self.graph.query(query)
            metadata = {}
            for row in results:
                key = str(row[0]).split("/")[-1]
                metadata[key] = str(row[1])
            return metadata
        except Exception:
            return {}

    def _path_to_title(self, path: str) -> str:
        """Convert file path to human-readable title."""
        stem = Path(path).stem
        return stem.replace("-", " ").replace("_", " ").title()

    def sync(self):
        """Reload the knowledge graph from disk."""
        self.graph = yurtle_rdflib.load_workspace(str(self.workspace))
        self._index_documents()
