import asyncio
import io
import sys
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from omnimind.tools.base_tool import BaseTool


# Web Search Tool
class WebSearchInput(BaseModel):
    query: str = Field(description="Search query string")
    max_results: int = Field(default=3, description="Maximum number of results to return")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Searches the web for given query string and returns top snippets."
    args_schema = WebSearchInput

    async def _run(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        # Simulated high-grade web search engine response
        return {
            "query": query,
            "results": [
                {
                    "title": f"Enterprise Search Result {i+1} for {query}",
                    "snippet": f"Detailed insights regarding {query}. OmniMind AI multi-agent orchestration architecture enables high accuracy.",
                    "url": f"https://example.com/search?q={query}&id={i+1}"
                }
                for i in range(min(max_results, 5))
            ]
        }


# Document Retrieval Tool
class DocumentRetrievalInput(BaseModel):
    query: str = Field(description="Natural language query for RAG document collection")
    top_k: int = Field(default=3, description="Number of top document chunks to retrieve")


class DocumentRetrievalTool(BaseTool):
    name = "document_retrieval"
    description = "Retrieves relevant knowledge passages from the Enterprise RAG vector store."
    args_schema = DocumentRetrievalInput

    def __init__(self, rag_retriever: Optional[Any] = None):
        super().__init__()
        self.rag_retriever = rag_retriever

    async def _run(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        if self.rag_retriever:
            docs = await self.rag_retriever.retrieve(query, top_k=top_k)
            return {"query": query, "documents": docs}
        
        # Fallback simulation
        return {
            "query": query,
            "documents": [
                {
                    "doc_id": "doc_101",
                    "content": f"OmniMind AI Knowledge Base: Information regarding '{query}'. Multi-agent workflows ensure enterprise grade safety and verification.",
                    "score": 0.92
                }
            ]
        }


# Python Code Executor Tool
class PythonExecutorInput(BaseModel):
    code: str = Field(description="Python code string to execute in safe context")


class PythonCodeExecutorTool(BaseTool):
    name = "python_executor"
    description = "Executes pure Python code and captures standard output and returned variables."
    args_schema = PythonExecutorInput

    async def _run(self, code: str) -> Dict[str, Any]:
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        exec_globals = {"__builtins__": __builtins__}
        exec_locals: Dict[str, Any] = {}

        try:
            # Simple security check against unsafe os system calls
            forbidden = ["import os", "import subprocess", "os.system", "shutil.rmtree"]
            for term in forbidden:
                if term in code:
                    raise PermissionError(f"Operation '{term}' is restricted for safety.")

            exec(code, exec_globals, exec_locals)
            sys.stdout = old_stdout
            stdout_str = buffer.getvalue()

            # Clean output locals (remove builtins)
            result_vars = {k: str(v) for k, v in exec_locals.items() if not k.startswith("__")}

            return {
                "stdout": stdout_str.strip(),
                "variables": result_vars
            }
        except Exception as e:
            sys.stdout = old_stdout
            return {
                "stdout": buffer.getvalue().strip(),
                "error": str(e)
            }


# HTTP Client Tool
class HTTPClientInput(BaseModel):
    url: str = Field(description="Target endpoint URL")
    method: str = Field(default="GET", description="HTTP Method (GET, POST)")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Optional JSON payload for POST")


class HTTPClientTool(BaseTool):
    name = "http_client"
    description = "Sends an HTTP request to an external REST endpoint."
    args_schema = HTTPClientInput

    async def _run(self, url: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return {
                "status_code": response.status_code,
                "data": response.json() if "application/json" in response.headers.get("content-type", "") else response.text[:500]
            }
