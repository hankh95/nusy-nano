# NuSy-nano Examples

This directory contains example knowledge graphs demonstrating NuSy-nano's hybrid search capabilities.

## Example Workspaces

### [lab-tests/](lab-tests/)

Medical laboratory tests with LOINC codes and clinical reference data.

| Files | Topics | Relationships |
|-------|--------|---------------|
| 4 | Lab panels, components, reference ranges | Clinical uses, components, related tests |

**Good for demonstrating:** Medical vocabularies, structured scientific data

### [great-thinkers/](great-thinkers/)

A knowledge graph of philosophers, scientists, and their ideas spanning 2500 years.

| Files | Topics | Relationships |
|-------|--------|---------------|
| 15+ | People, concepts, works | Influenced-by, student-of, developed, criticized |

**Good for demonstrating:** Rich interconnections, semantic search across domains

## Quick Start

```python
from nusy_nano import KnowledgeGraph

# Load lab tests
lab = KnowledgeGraph("examples/lab-tests/")
results = lab.hybrid_search("blood sugar diabetes")

# Load great thinkers
thinkers = KnowledgeGraph("examples/great-thinkers/")
results = thinkers.search("the nature of reality")
```

## Example Queries

### Semantic Search

```python
# Find documents about a concept
kg.search("free will and determinism")
kg.search("how do we know what we know")
kg.search("cardiovascular risk factors")
```

### Structured Queries

```python
# Find all philosophers
kg.query("""
    SELECT ?name WHERE {
        ?p :type "person" ;
           :title ?name .
    }
""")

# Find who influenced Kant
kg.query("""
    SELECT ?influencer WHERE {
        ?kant :title "Immanuel Kant" ;
              :influenced-by ?influencer .
    }
""")

# Find all lab panels
kg.query("""
    SELECT ?title ?loinc WHERE {
        ?test a lab:Panel ;
              yurtle:title ?title ;
              lab:loincCode ?loinc .
    }
""")
```

### Hybrid Search

```python
# Philosophers who wrote about ethics
kg.hybrid_search("moral philosophy", filters={"type": "person"})

# Lab tests for diabetes
kg.hybrid_search("blood sugar", filters={"type": "lab-test"})

# Works about metaphysics
kg.hybrid_search("the nature of being", filters={"type": "work"})
```

## Adding Your Own Examples

1. Create a new directory for your domain
2. Add Yurtle-formatted `.md` files with:
   - YAML frontmatter (id, type, title, relations)
   - Rich prose content
   - Optional yurtle blocks for structured data
3. Create a README describing your knowledge graph
4. Test with `KnowledgeGraph("your-directory/")`

## License

MIT - use freely for learning and experimentation.
