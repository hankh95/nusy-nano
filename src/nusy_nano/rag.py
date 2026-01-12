"""
RAG (Retrieval Augmented Generation) utilities for NuSy-nano.

Provides functions to use the knowledge graph with LLMs like Claude or GPT.
"""

import os
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from nusy_nano.graph import KnowledgeGraph, SearchResult


def _format_context(results: list["SearchResult"]) -> str:
    """Format search results as context for the LLM."""
    parts = []

    for i, result in enumerate(results, 1):
        content = result.read()

        part = f"""
### Document {i}: {result.title}
**Relevance Score:** {result.score:.3f}
**Path:** {result.path}

{content}
"""
        parts.append(part)

    return "\n---\n".join(parts)


def ask(
    kg: "KnowledgeGraph",
    question: str,
    model: str = "claude-sonnet-4-20250514",
    top_k: int = 3,
    provider: str = "auto",
) -> str:
    """
    Ask a question using RAG (Retrieval Augmented Generation).

    Retrieves relevant documents from the knowledge graph and uses them
    as context for an LLM to generate an answer.

    Args:
        kg: KnowledgeGraph instance
        question: The question to answer
        model: Model name (e.g., "claude-sonnet-4-20250514", "gpt-4")
        top_k: Number of documents to retrieve
        provider: "anthropic", "openai", or "auto" (detect from model name)

    Returns:
        The LLM's answer grounded in retrieved documents

    Example:
        kg = KnowledgeGraph("knowledge/")
        answer = ask(kg, "What tests are used for diabetes?")
    """
    # Retrieve relevant documents
    results = kg.hybrid_search(question, top_k=top_k)
    if not results:
        results = kg.search(question, top_k=top_k)

    if not results:
        return "No relevant documents found in the knowledge base."

    # Format context
    context = _format_context(results)

    # Build prompt
    system_prompt = """You are a helpful assistant that answers questions based on
the provided documentation. Always cite which documents you're referencing.
If the context doesn't contain enough information, say so."""

    user_prompt = f"""Based on the following documents, please answer this question:

**Question:** {question}

---

## Retrieved Documents

{context}

---

Please provide a clear, accurate answer based on the documents above."""

    # Detect provider
    if provider == "auto":
        if "claude" in model.lower():
            provider = "anthropic"
        elif "gpt" in model.lower():
            provider = "openai"
        else:
            provider = "anthropic"  # Default

    # Call LLM
    if provider == "anthropic":
        return _ask_anthropic(system_prompt, user_prompt, model)
    elif provider == "openai":
        return _ask_openai(system_prompt, user_prompt, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _ask_anthropic(system: str, user: str, model: str) -> str:
    """Call Anthropic Claude API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return "Error: anthropic package not installed. Run: pip install nusy-nano[anthropic]"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY environment variable not set"

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _ask_openai(system: str, user: str, model: str) -> str:
    """Call OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        return "Error: openai package not installed. Run: pip install nusy-nano[openai]"

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY environment variable not set"

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def chat(
    kg: "KnowledgeGraph",
    model: str = "claude-sonnet-4-20250514",
    provider: str = "auto",
) -> None:
    """
    Interactive chat session with the knowledge graph.

    Args:
        kg: KnowledgeGraph instance
        model: Model name
        provider: "anthropic", "openai", or "auto"

    Example:
        kg = KnowledgeGraph("knowledge/")
        chat(kg)  # Starts interactive session
    """
    print("\n" + "=" * 60)
    print("NuSy-nano Chat")
    print(f"Knowledge base: {kg.workspace}")
    print(f"Documents: {len(kg)}")
    print("Type 'quit' to exit, 'search <query>' for semantic search")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # Handle search command
        if user_input.lower().startswith("search "):
            query = user_input[7:]
            results = kg.search(query, top_k=5)
            print("\nSearch results:")
            for r in results:
                print(f"  {r.score:.3f}: {r.title}")
            print()
            continue

        # Regular question - use RAG
        print("\nSearching knowledge base...")
        answer = ask(kg, user_input, model=model, provider=provider)
        print(f"\nAssistant: {answer}\n")
