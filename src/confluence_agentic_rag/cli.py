"""
Docstring for confluence_agentic_rag.cli
Command-line interface for Confluence Agentic RAG application.
Supports ingestion of Confluence decision/ADR pages into Weaviate
and asking questions against the indexed data.
"""

import argparse
from rich import print
from confluence_agentic_rag.config import Settings
from confluence_agentic_rag.tools.confluence_client import ConfluenceClient
from confluence_agentic_rag.agent.orchestrator import answer
from confluence_agentic_rag.llm.stub import StubLLM
from vectorstore.weaviate_store import WeaviateStore
from ingest.ingest_confluence import ingest_space_decisions



def main():
    """
    Command-line interface entry point.
    Supports 'ingest' and 'ask' commands.
    """
    parser = argparse.ArgumentParser("carag")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest Confluence decision/ADR pages into Weaviate")
    p_ingest.add_argument("--space", default=None)
    p_ingest.add_argument("--limit", type=int, default=50)

    p_ask = sub.add_parser("ask", help="Ask a question (retrieves from Weaviate)")
    p_ask.add_argument("question")
    p_ask.add_argument("--space", default=None)
    p_ask.add_argument("--topk", type=int, default=8)

    args = parser.parse_args()
    settings = Settings().validate_or_raise()

    store = WeaviateStore("http://localhost:6060")
    llm = StubLLM()

    try:
        if args.cmd == "ingest":
            confluence = ConfluenceClient(
                settings.confluence_base_url,
                settings.confluence_email,
                settings.confluence_api_token,
            )
            space_key = args.space or settings.confluence_space_key
            out = ingest_space_decisions(
                confluence, store, space_key=space_key, limit_pages=args.limit
            )
            pages = out["pages_indexed"]
            chunks = out["chunks_indexed"]
            print(f"[bold green]Done.[/bold green] Pages={pages} Chunks={chunks}")

        elif args.cmd == "ask":
            space_key = args.space or settings.confluence_space_key
            out = answer(args.question, store=store, llm=llm, space_key=space_key, top_k=args.topk)
            print("\n[bold]Answer:[/bold]")
            print(out["answer"])
            print("\n[bold]Top Sources:[/bold]")
            for s in out.get("sources", [])[:5]:
                title = s["title"]
                url = s["url"]
                print(f"- {title} ({url}) distance={s['distance']:.4f}")
    finally:
        store.close()
