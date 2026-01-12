"""
NuSy-nano: A tiny framework for human-readable knowledge graphs with hybrid search.

Combines Yurtle (markdown knowledge graphs), RDFlib (SPARQL queries),
and txtai (semantic search) into one simple interface.

Example:
    from nusy_nano import KnowledgeGraph

    kg = KnowledgeGraph("knowledge/")
    results = kg.hybrid_search("blood sugar", filters={"type": "lab-test"})
"""

from nusy_nano.graph import KnowledgeGraph, SearchResult
from nusy_nano.rag import ask, chat

__version__ = "0.1.0"
__all__ = ["KnowledgeGraph", "SearchResult", "ask", "chat"]
