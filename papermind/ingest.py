#!/usr/bin/env python3
"""CLI for ingesting PDF papers into PaperMind's vector index."""
import sys
from pathlib import Path

from config import get_settings
from ingestion.chunker import chunk_pages
from ingestion.embedder import Embedder
from ingestion.parser import parse_pdf

settings = get_settings()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <paper.pdf> [paper2.pdf ...]")
        sys.exit(1)

    embedder = Embedder(persist_dir=settings.chroma_db_path)

    for path_str in sys.argv[1:]:
        path = Path(path_str)
        if not path.exists():
            print(f"Not found: {path}")
            continue

        print(f"\nIngesting {path.name}...")
        pages = parse_pdf(path)
        print(f"  Parsed {len(pages)} pages")

        chunks = chunk_pages(pages)
        print(f"  Created {len(chunks)} chunks")

        embedder.embed_chunks(chunks)
        print(f"  Stored in {settings.chroma_db_path} — paper_id: {path.stem}")


if __name__ == "__main__":
    main()
