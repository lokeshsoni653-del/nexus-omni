"""
OmniMind AI — Interactive Document Q&A & Vector Search Chat API Route
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from config import settings
from omnimind.rag.chroma_store import ChromaDBManager
from omnimind.providers.llm_provider import get_llm_provider, LLMMessage, Role

logger = logging.getLogger("omnimind.api.routes.chat")
router = APIRouter(prefix="/chat", tags=["Interactive Document Q&A"])


class DocumentQaRequest(BaseModel):
    query: str = Field(..., description="Question or query about ingested PDF documents")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional list of target document IDs to filter search")
    api_key: Optional[str] = Field(default=None, description="Optional user API key (Gemini/OpenAI)")


class DocumentQaResponse(BaseModel):
    query: str
    answer: str
    sources: List[dict]
    model_used: str


@router.post("/document-qa", response_model=DocumentQaResponse)
async def interactive_document_qa(payload: DocumentQaRequest):
    """
    Query ingested PDF document knowledge base using vector search + live LLM response synthesis.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    # 1. Search ChromaDB vector store
    chroma_mgr = ChromaDBManager(
        collection_name=settings.CHROMA_COLLECTION_NAME,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )
    passages = chroma_mgr.search(query, top_k=3)

    context_snippets = []
    sources = []

    for idx, p in enumerate(passages, 1):
        doc_id = p.get("id", f"Doc_{idx}")
        content = p.get("content", "")
        context_snippets.append(f"[{doc_id}]: {content}")
        sources.append({
            "id": doc_id,
            "snippet": content[:200] + ("..." if len(content) > 200 else ""),
            "metadata": p.get("metadata", {})
        })

    context_str = "\n\n".join(context_snippets) if context_snippets else "No relevant enterprise PDF documents found in ChromaDB store."

    # 2. Synthesize response using Live LLM Provider
    llm = get_llm_provider(api_key=payload.api_key)

    system_prompt = (
        "You are OmniMind AI Document Intelligence Assistant. "
        "Use the provided retrieved PDF document excerpts to answer the user's question accurately, "
        "concisely, and professionally with clear page citations."
    )

    user_prompt = f"Retrieved Document Context:\n{context_str}\n\nUser Question:\n{query}"

    messages = [
        LLMMessage(role=Role.SYSTEM, content=system_prompt),
        LLMMessage(role=Role.USER, content=user_prompt),
    ]

    llm_res = await llm.generate(messages, temperature=0.3, max_tokens=1024)

    return DocumentQaResponse(
        query=query,
        answer=llm_res.content,
        sources=sources,
        model_used=type(llm).__name__,
    )
