import os
import sys
import argparse
import logging
from omnimind.rag.pdf_ingestion import PDFIngestionPipeline
from omnimind.rag.chroma_store import ChromaDBManager

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("omnimind.ingest_cli")


def main():
    parser = argparse.ArgumentParser(description="Ingest local PDF into OmniMind AI ChromaDB Vector Store.")
    parser.add_argument("pdf_path", help="Path to local PDF file")
    parser.add_argument("--collection", default="omnimind_pdf_knowledge", help="ChromaDB collection name")
    parser.add_argument("--persist-dir", default="./chroma_db", help="ChromaDB persistence directory")
    parser.add_argument("--chunk-size", type=int, default=500, help="RecursiveCharacterTextSplitter chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap size")

    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: Specified PDF file does not exist: '{args.pdf_path}'")
        sys.exit(1)

    print("=" * 80)
    print(f"Starting OmniMind AI PDF Ingestion Pipeline...")
    print(f"File: {args.pdf_path}")
    print(f"Collection: {args.collection}")
    print(f"Persist Directory: {args.persist_dir}")
    print("=" * 80)

    chroma_mgr = ChromaDBManager(
        collection_name=args.collection,
        persist_directory=args.persist_dir
    )

    pipeline = PDFIngestionPipeline(
        chroma_manager=chroma_mgr,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )

    res = pipeline.ingest_pdf(args.pdf_path)

    print("\n" + "=" * 80)
    print("Ingestion Summary:")
    print(f"- Status: {res['status']}")
    print(f"- Source File: {res['source_file']}")
    print(f"- Total Pages: {res['total_pages']}")
    print(f"- Chunks Ingested into ChromaDB: {res['chunks_ingested']}")
    print(f"- Total Collection Document Count: {chroma_mgr.count()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
