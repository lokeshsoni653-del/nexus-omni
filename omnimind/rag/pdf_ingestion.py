import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Robust PyPDFLoader & TextSplitter imports with fallback
try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    from pypdf import PdfReader

    class Document(BaseModel):
        page_content: str
        metadata: Dict[str, Any]

    class PyPDFLoader:
        def __init__(self, file_path: str):
            self.file_path = file_path

        def load(self) -> List[Document]:
            reader = PdfReader(self.file_path)
            docs = []
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                docs.append(Document(page_content=text, metadata={"source": self.file_path, "page": idx}))
            return docs

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from omnimind.rag.chunking import TextChunker

    class Document(BaseModel):
        page_content: str
        metadata: Dict[str, Any]

    class RecursiveCharacterTextSplitter:
        def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: Optional[List[str]] = None):
            self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        def split_documents(self, documents: List[Any]) -> List[Any]:
            split_docs = []
            for doc in documents:
                chunks = self.chunker.split_text(doc.page_content, doc_id=doc.metadata.get("source", "doc"))
                for idx, c in enumerate(chunks):
                    split_docs.append(
                        Document(
                            page_content=c.content,
                            metadata={**doc.metadata, "chunk_index": idx}
                        )
                    )
            return split_docs

from omnimind.rag.chroma_store import ChromaDBManager

logger = logging.getLogger("omnimind.rag.pdf_ingestion")


class PDFIngestionPipeline:
    """PDF Ingestion Pipeline using PyPDFLoader, RecursiveCharacterTextSplitter, and ChromaDB."""

    def __init__(
        self,
        chroma_manager: Optional[ChromaDBManager] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.chroma_manager = chroma_manager or ChromaDBManager()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def ingest_pdf(
        self,
        pdf_path: str,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Load local PDF, split into chunks with RecursiveCharacterTextSplitter, and save to ChromaDB."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at path: '{pdf_path}'")

        logger.info(f"Loading PDF document from '{pdf_path}' using PyPDFLoader...")
        loader = PyPDFLoader(file_path=pdf_path)
        documents = loader.load()

        if not documents:
            logger.warning(f"No pages extracted from PDF '{pdf_path}'.")
            return {"chunks_ingested": 0, "status": "empty"}

        logger.info(f"Loaded {len(documents)} pages from PDF. Splitting into chunks with RecursiveCharacterTextSplitter...")
        chunks = self.text_splitter.split_documents(documents)

        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        filename = os.path.basename(pdf_path)
        meta_extra = custom_metadata or {}

        for idx, chunk in enumerate(chunks):
            page_num = chunk.metadata.get("page", 0) + 1 if isinstance(chunk.metadata.get("page"), int) else 1
            chunk_id = f"{filename}_page_{page_num}_{idx}_{uuid.uuid4().hex[:6]}"
            texts.append(chunk.page_content)
            
            meta = {
                "source": filename,
                "file_path": pdf_path,
                "page": page_num,
                **meta_extra
            }
            metadatas.append(meta)
            ids.append(chunk_id)

        # Store in ChromaDB
        self.chroma_manager.add_documents(texts=texts, metadatas=metadatas, ids=ids)

        logger.info(f"Successfully ingested {len(texts)} chunks from '{filename}' into ChromaDB.")

        return {
            "source_file": filename,
            "total_pages": len(documents),
            "chunks_ingested": len(texts),
            "status": "success"
        }
