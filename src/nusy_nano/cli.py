"""
Command-line interface for NuSy-nano.
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for the nusy CLI."""
    parser = argparse.ArgumentParser(
        description="NuSy-nano: Human-readable knowledge graphs with hybrid search"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Semantic search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-p", "--path", default=".", help="Path to knowledge base"
    )
    search_parser.add_argument(
        "-n", "--top-k", type=int, default=5, help="Number of results"
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="SPARQL query")
    query_parser.add_argument("sparql", help="SPARQL query string")
    query_parser.add_argument(
        "-p", "--path", default=".", help="Path to knowledge base"
    )

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat")
    chat_parser.add_argument(
        "-p", "--path", default=".", help="Path to knowledge base"
    )
    chat_parser.add_argument(
        "-m", "--model", default="claude-sonnet-4-20250514", help="LLM model"
    )

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question (RAG)")
    ask_parser.add_argument("question", help="Question to ask")
    ask_parser.add_argument(
        "-p", "--path", default=".", help="Path to knowledge base"
    )
    ask_parser.add_argument(
        "-m", "--model", default="claude-sonnet-4-20250514", help="LLM model"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Knowledge base info")
    info_parser.add_argument(
        "-p", "--path", default=".", help="Path to knowledge base"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Import here to avoid slow startup
    from nusy_nano import KnowledgeGraph, ask, chat

    # Execute command
    if args.command == "search":
        kg = KnowledgeGraph(args.path)
        results = kg.search(args.query, top_k=args.top_k)
        for r in results:
            print(f"{r.score:.3f}: {r.title}")
            print(f"        {r.path}")

    elif args.command == "query":
        kg = KnowledgeGraph(args.path)
        results = kg.query(args.sparql)
        for row in results:
            print(row)

    elif args.command == "chat":
        kg = KnowledgeGraph(args.path)
        chat(kg, model=args.model)

    elif args.command == "ask":
        kg = KnowledgeGraph(args.path)
        answer = ask(kg, args.question, model=args.model)
        print(answer)

    elif args.command == "info":
        kg = KnowledgeGraph(args.path)
        print(f"Knowledge Base: {kg.workspace}")
        print(f"Documents: {len(kg)}")
        print(f"Triples: {len(kg.graph)}")


if __name__ == "__main__":
    main()
