"""
Command-line interface for Confluence Agentic RAG.

Supports:
- ingest: Ingest Confluence decision/ADR pages into Weaviate
- ask:    Ask questions against indexed Confluence content
"""

from __future__ import annotations

import argparse

from rich.console import Console

from confluence_agentic_rag.config import Settings
from confluence_agentic_rag.tools.confluence_client import ConfluenceClient
from confluence_agentic_rag.agent.orchestrator import _normalize_url, answer
from confluence_agentic_rag.llm.stub import StubLLM
from vectorstore.weaviate_store import WeaviateStore
from ingest.ingest_confluence import ingest_space_decisions


console = Console()


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(prog="carag")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest Confluence decision/ADR pages into Weaviate")
    p_ingest.add_argument("--space", default=None, help="Confluence space key")
    p_ingest.add_argument("--limit", type=int, default=50, help="Max pages to ingest")
    p_ask = sub.add_parser("ask", help="Ask a question (retrieves from Weaviate)")
    p_ask.add_argument("question", help="Question to ask")
    p_ask.add_argument("--space", default=None, help="Confluence space key")
    p_ask.add_argument("--topk", type=int, default=8, help="Top K chunks to retrieve")

    return parser


def _handle_ingest(args: argparse.Namespace, settings: Settings, store: WeaviateStore) -> None:
    """Handle the `ingest` CLI command."""
    confluence = ConfluenceClient(
        settings.confluence_base_url,
        settings.confluence_email,
        settings.confluence_api_token,
    )
    space_key = args.space or settings.confluence_space_key

    out = ingest_space_decisions(confluence, store, space_key=space_key, limit_pages=args.limit)
    pages = out.get("pages_indexed", 0)
    chunks = out.get("chunks_indexed", 0)

    console.print(f"[bold green]Done.[/bold green] Pages={pages} Chunks={chunks}")


def _handle_ask(args: argparse.Namespace, settings: Settings, store: WeaviateStore) -> None:
    """Handle the `ask` CLI command."""
    llm = StubLLM()
    space_key = args.space or settings.confluence_space_key

    out = answer(args.question, store=store, llm=llm, space_key=space_key, top_k=args.topk)

    console.print("\n[bold]Answer:[/bold]")
    console.print(out.get("answer", ""))

    console.print("\n[bold]Top Sources:[/bold]")
    for s in out.get("sources", [])[:5]:
        title = s.get("title", "")
        url = _normalize_url(s.get("url", "") or "")
        distance = s.get("distance", 0.0)
        console.print(f"- {title} ({url}) distance={distance:.4f}")


def main() -> None:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()

    settings = Settings().validate_or_raise()
    store = WeaviateStore("http://localhost:6060")

    try:
        if args.cmd == "ingest":
            _handle_ingest(args, settings, store)
        elif args.cmd == "ask":
            _handle_ask(args, settings, store)
    finally:
        store.close()
