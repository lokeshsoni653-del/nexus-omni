import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from omnimind.tools.base_tool import BaseTool
from omnimind.rag.chroma_store import ChromaDBManager

logger = logging.getLogger("omnimind.tools.chroma_tool")


class ChromaPDFQueryInput(BaseModel):
    query: str = Field(description="Question or search query to search within private PDF documents")
    top_k: int = Field(default=3, description="Number of relevant PDF passages to retrieve")


class ChromaPDFQueryTool(BaseTool):
    """Custom Agent Tool for querying ChromaDB private document store."""

    name = "chroma_pdf_query"
    description = "Queries the private PDF document collection in ChromaDB to retrieve relevant knowledge passages."
    args_schema = ChromaPDFQueryInput

    def __init__(self, chroma_manager: Optional[ChromaDBManager] = None):
        super().__init__()
        self.chroma_manager = chroma_manager or ChromaDBManager()

    async def _run(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        logger.info(f"ChromaPDFQueryTool searching ChromaDB for query: '{query}'")
        passages = self.chroma_manager.query(query_text=query, n_results=top_k)

        if not passages:
            return {
                "query": query,
                "found": False,
                "message": "No relevant passages found in private PDF documents.",
                "passages": []
            }

        return {
            "query": query,
            "found": True,
            "total_retrieved": len(passages),
            "passages": passages
        }
