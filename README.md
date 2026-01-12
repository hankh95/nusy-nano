# NuSy-nano

**NuSy-nano** = a tiny, educational framework for building **knowledge graphs you can actually read**.

Combines three tools into one simple pattern:

| Tool | What it does |
|------|--------------|
| **[Yurtle](https://github.com/hankh95/yurtle)** | Human-readable markdown files that form a knowledge graph |
| **[yurtle-rdflib](https://github.com/hankh95/yurtle-rdflib)** | SPARQL queries over your markdown files |
| **[txtai](https://github.com/neuml/txtai)** | Semantic search using embeddings |

The result: **hybrid search** that understands both meaning and structure.

```
"Find lab tests about heart disease that are panels with LOINC codes"
      ↓ semantic                    ↓ structured
   (txtai)                        (SPARQL)
```

## Why?

Traditional knowledge graphs are powerful but invisible — locked in databases, requiring specialized query languages.

NuSy-nano keeps everything in **plain markdown files**:
- Edit in Obsidian, VSCode, or vim
- Version control with Git
- LLMs can read them directly
- Humans can read them too

## Installation

```bash
pip install nusy-nano
```

Or install from source:

```bash
git clone https://github.com/hankh95/nusy-nano.git
cd nusy-nano
pip install -e .
```

## Quick Start

### 1. Create some Yurtle files

```markdown
<!-- knowledge/diabetes.md -->
---
id: conditions/diabetes
type: condition
title: Type 2 Diabetes
relates-to:
  - tests/hba1c
  - tests/glucose
---

# Type 2 Diabetes

A metabolic disorder characterized by high blood sugar, insulin resistance,
and relative lack of insulin. Affects millions worldwide.

## Diagnosis

Diagnosed via HbA1c ≥ 6.5% or fasting glucose ≥ 126 mg/dL.
```

```markdown
<!-- knowledge/hba1c.md -->
---
id: tests/hba1c
type: lab-test
title: Hemoglobin A1c
loinc: 4548-4
relates-to:
  - conditions/diabetes
---

# Hemoglobin A1c (HbA1c)

Measures average blood glucose over 2-3 months. Gold standard for
diabetes monitoring and diagnosis.

## Reference Ranges

- Normal: < 5.7%
- Prediabetes: 5.7% - 6.4%
- Diabetes: ≥ 6.5%
```

### 2. Search your knowledge

```python
from nusy_nano import KnowledgeGraph

# Load your markdown files
kg = KnowledgeGraph("knowledge/")

# Semantic search (finds by meaning)
results = kg.search("blood sugar control")
# → [diabetes.md, hba1c.md, ...]

# Structured query (finds by properties)
results = kg.query("""
    SELECT ?test ?loinc WHERE {
        ?test a :lab-test ;
              :loinc ?loinc .
    }
""")
# → [{"test": "hba1c", "loinc": "4548-4"}]

# Hybrid search (both!)
results = kg.hybrid_search(
    "diabetes monitoring",
    filters={"type": "lab-test"}
)
# → [hba1c.md] (semantic match + type filter)
```

### 3. Use with an LLM (RAG)

```python
from nusy_nano import KnowledgeGraph, ask

kg = KnowledgeGraph("knowledge/")

# Ask questions grounded in your knowledge
answer = ask(
    kg,
    "What tests should I order for a patient with suspected diabetes?",
    model="claude-sonnet-4-20250514"  # or any OpenAI/local model
)
```

## Core Concepts

### The Three Layers

Every Yurtle file has three layers of information:

```markdown
---
# Layer 1: YAML Frontmatter (structured)
id: tests/hba1c
type: lab-test
loinc: 4548-4
---

# Layer 2: Prose Content (semantic)
Hemoglobin A1c measures average blood glucose...

# Layer 3: Yurtle Blocks (structured, inline)
` ``yurtle
interpretation:
  normal: "< 5.7%"
  diabetes: ">= 6.5%"
` ``
```

### Hybrid Search

| Search Type | Best For | Example |
|-------------|----------|---------|
| **Semantic** | Open questions, concept discovery | "What affects heart health?" |
| **Structured** | Precise filters, aggregations | "All tests with LOINC codes" |
| **Hybrid** | Natural language + constraints | "Heart tests that are panels" |

### Why Three Tools?

```
┌─────────────────────────────────────┐
│         Your Markdown Files          │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ doc1.md │ │ doc2.md │ │ doc3.md│ │
│  └─────────┘ └─────────┘ └────────┘ │
└─────────────────────────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│  yurtle-rdflib  │  │     txtai       │
│                 │  │                 │
│ Frontmatter →   │  │ Prose →         │
│ RDF Graph       │  │ Embeddings      │
│                 │  │                 │
│ Query: SPARQL   │  │ Query: Vectors  │
└─────────────────┘  └─────────────────┘
         │                   │
         └─────────┬─────────┘
                   ▼
         ┌─────────────────┐
         │  Hybrid Search  │
         │                 │
         │ Meaning +       │
         │ Structure       │
         └─────────────────┘
```

## Examples

See the [examples/](examples/) directory:

- **[lab-tests/](examples/lab-tests/)** - Medical laboratory tests with LOINC codes
- **[recipes/](examples/recipes/)** - Cooking recipes with ingredients and techniques
- **[papers/](examples/papers/)** - Academic papers with citations

## API Reference

### KnowledgeGraph

```python
class KnowledgeGraph:
    def __init__(self, path: str, model: str = "all-MiniLM-L6-v2"):
        """Load a directory of Yurtle files."""

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Semantic search over prose content."""

    def query(self, sparql: str) -> list[dict]:
        """SPARQL query over structured data."""

    def hybrid_search(
        self,
        query: str,
        filters: dict = None,
        top_k: int = 5
    ) -> list[SearchResult]:
        """Hybrid search: semantic + structured filters."""

    def find_related(self, doc_path: str, top_k: int = 5) -> list[SearchResult]:
        """Find documents related to a given document."""

    def add(self, path: str, content: str):
        """Add a new document to the knowledge graph."""

    def sync(self):
        """Sync changes between files and graph."""
```

### SearchResult

```python
@dataclass
class SearchResult:
    title: str
    path: str
    score: float
    metadata: dict
```

### RAG Functions

```python
def ask(
    kg: KnowledgeGraph,
    question: str,
    model: str = "claude-sonnet-4-20250514",
    top_k: int = 3
) -> str:
    """Ask a question using RAG."""

def chat(
    kg: KnowledgeGraph,
    model: str = "claude-sonnet-4-20250514"
) -> None:
    """Interactive chat session."""
```

## Configuration

### Environment Variables

```bash
# For RAG with Claude
export ANTHROPIC_API_KEY=your-key

# For RAG with OpenAI
export OPENAI_API_KEY=your-key
```

### Custom Embeddings Model

```python
kg = KnowledgeGraph(
    "knowledge/",
    model="sentence-transformers/all-mpnet-base-v2"  # Better quality
)
```

## Philosophy

NuSy-nano is intentionally minimal. It's a **teaching tool** and **starting point**, not a production system.

Core principles:

1. **Files are the source of truth** - No database. Just markdown.
2. **Human-readable first** - If a human can't read it, it's not knowledge.
3. **LLM-friendly** - Structure that helps both humans and AI.
4. **Composable** - Use the pieces you need, ignore the rest.

## What NuSy-nano is NOT

- ❌ A production database
- ❌ A replacement for proper knowledge management
- ❌ Suitable for millions of documents
- ❌ The only way to do this

## What NuSy-nano IS

- ✅ A learning tool
- ✅ A prototype framework
- ✅ A starting point for your own system
- ✅ A demonstration of hybrid search
- ✅ Fun to hack on

## Related Projects

- [Yurtle](https://github.com/hankh95/yurtle) - The file format specification
- [yurtle-rdflib](https://github.com/hankh95/yurtle-rdflib) - RDFlib plugin for Yurtle
- [txtai](https://github.com/neuml/txtai) - Semantic search and embeddings
- [RDFlib](https://github.com/RDFLib/rdflib) - Python RDF library

## License

MIT License - do whatever you want with it.

---

*"The best knowledge graph is one you'll actually use."*
