"""
OmniMind AI — ChromaDB Vector Store Manager
"""
import os
import uuid
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("omnimind.rag.chroma_store")

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.warning("chromadb package not found. Using memory fallback for ChromaDBManager.")


class ChromaDBManager:
    """Manager class for ChromaDB vector collection storage and similarity search."""

    def __init__(
        self,
        collection_name: str = "omnimind_pdf_knowledge",
        persist_directory: str = "./chroma_db",
        is_ephemeral: bool = False,
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.is_ephemeral = is_ephemeral
        self._fallback_docs: List[Dict[str, Any]] = []

        if HAS_CHROMADB:
            if is_ephemeral:
                self.client = chromadb.EphemeralClient()
            else:
                os.makedirs(self.persist_directory, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.persist_directory)

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB collection '{collection_name}' initialized.")
        else:
            self.client = None
            self.collection = None

    def add_documents(
        self,
        documents: Optional[List[str]] = None,
        texts: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add text documents/chunks into the ChromaDB collection."""
        docs = documents or texts or []
        if not ids:
            ids = [f"doc_{uuid.uuid4().hex[:12]}" for _ in range(len(docs))]
        if not metadatas:
            metadatas = [{} for _ in range(len(docs))]

        if HAS_CHROMADB and self.collection:
            self.collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Added {len(docs)} document chunks to ChromaDB collection '{self.collection_name}'.")
        else:
            for doc, meta, doc_id in zip(docs, metadatas, ids):
                self._fallback_docs.append({
                    "id": doc_id,
                    "document": doc,
                    "metadata": meta,
                })

        return ids

    def query(
        self,
        query_text: str,
        n_results: int = 4,
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search on the ChromaDB collection."""
        formatted = []
        if HAS_CHROMADB and self.collection:
            count = self.collection.count()
            if count == 0:
                return []

            # Retrieve candidate documents to ensure keyword matches are not truncated prematurely
            k_fetch = min(max(n_results * 3, 10), count)
            try:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=k_fetch,
                )
                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    doc_ids = results["ids"][0] if results.get("ids") else [f"doc_{i}" for i in range(len(docs))]
                    distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

                    for doc_id, doc_text, meta, dist in zip(doc_ids, docs, metas, distances):
                        formatted.append({
                            "id": doc_id,
                            "content": doc_text,
                            "metadata": meta,
                            "distance": dist,
                        })
            except Exception as e:
                logger.warning(f"ChromaDB vector query exception: {e}")

            if not formatted:
                all_items = self.collection.get()
                if all_items and all_items.get("documents"):
                    for doc_id, doc_text, meta in zip(
                        all_items["ids"],
                        all_items["documents"],
                        all_items["metadatas"] or [{}] * len(all_items["documents"])
                    ):
                        formatted.append({
                            "id": doc_id,
                            "content": doc_text,
                            "metadata": meta,
                            "distance": 0.0,
                        })

        else:
            for doc_item in self._fallback_docs:
                formatted.append({
                    "id": doc_item["id"],
                    "content": doc_item["document"],
                    "metadata": doc_item["metadata"],
                    "distance": 0.1,
                })

        # Rank exact query substring matches first
        q_lower = query_text.lower().strip()
        if q_lower and len(formatted) > 1:
            formatted.sort(key=lambda item: 0 if q_lower in item["content"].lower() else 1)

        return formatted[:n_results]

    def count(self) -> int:
        """Return the total number of document chunks in the collection."""
        if HAS_CHROMADB and self.collection:
            return self.collection.count()
        return len(self._fallback_docs)

    def reset_collection(self):
        """Reset / delete all items in the collection."""
        if HAS_CHROMADB and self.client:
            try:
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                logger.warning(f"Failed to reset collection: {e}")
        else:
            self._fallback_docs = []
