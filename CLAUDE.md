# NuSy Nano — Claude Code Instructions

Educational knowledge graph framework — a lightweight version of NuSy that combines graph tools into a simple, readable pattern for learning and prototyping.

## Project Overview

- **Language:** Python 3.11+
- **Build:** `pip install -e .`
- **Tests:** `pytest` (if available)

## Development Practices

### Branch + PR Pattern (Required)

All implementation work goes through feature branches and pull requests:

1. Create a feature branch: `git checkout -b feat-short-description`
2. Do all implementation work on the branch — **never push directly to main**
3. Run tests if available: `pytest`
4. Push and create PR: `gh pr create`
5. Get review from another developer/agent before merging

After merge, clean up:
```bash
git branch -d feat-short-description
git push origin --delete feat-short-description
```

### Code Quality

- Always use type hints
- Prefer editing existing files over creating new ones
- Don't create files unless necessary
- Keep the codebase simple and educational — this is a learning tool

## Multi-Agent Coordination

| Agent | GitHub | Platform |
|-------|--------|----------|
| **M5** | hankh95 | MacBook Pro M5 |
| **DGX** | hankh959 | DGX Spark |
| **Mini** | hankh1844 | Mac Mini M4 |

## Related Projects

- **nusy-product-team** — The full NuSy platform
- **yurtle-rdflib** — RDF parsing library used for knowledge graphs
