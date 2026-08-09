# OmniMind AI — Autonomous Multi-Agent SaaS & Enterprise RAG Platform

![OmniMind AI Core Engine](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green?logo=fastapi)
![Architecture](https://img.shields.io/badge/Architecture-Async%20DAG%20Multi--Agent-orange)

OmniMind AI is an enterprise-grade autonomous multi-agent platform designed for high-throughput task orchestration, modular tool execution, dynamic RAG knowledge retrieval, and real-time streaming APIs.

---

## 🌟 Key Features

1. **Autonomous Multi-Agent Engine**:
   - `OrchestratorAgent`: Analyzes goals and plans task decompositions.
   - `WorkerAgent`: Executes technical work using dynamic sandboxed tools.
   - `RAGAgent`: Performs hybrid vector knowledge retrieval & context synthesis.
   - `ReviewerAgent`: Audits and validates outputs for quality and safety.

2. **Async DAG Execution Engine**:
   - Supports Sequential workflows and parallel Directed Acyclic Graph (DAG) task trees with dependency resolution.
   - Shared multi-tier memory state across agent teams (`AgentMemory`).

3. **Enterprise RAG Engine**:
   - Hybrid dense vector search + keyword term overlap re-ranking.
   - Intelligent text chunking with customizable sliding window overlap (`TextChunker`).
   - Pluggable `VectorStore` interface with built-in high-performance `InMemoryVectorStore`.

4. **Dynamic Tool Registry**:
   - Pydantic schema validation for all tool inputs.
   - Pre-built tools: `WebSearchTool`, `DocumentRetrievalTool`, `PythonCodeExecutorTool`, `HTTPClientTool`.
   - Automatic OpenAI-compatible function calling schema export (`to_json_schema()`).

5. **REST API & SSE Streaming Server**:
   - Built on FastAPI with async endpoint handlers.
   - Server-Sent Events (`/api/v1/agent/stream`) for streaming agent thoughts.
   - Interactive OpenAPI documentation available at `/docs`.

---

## 📁 Repository Structure

```
c:\OmniMind AI\
├── main.py                     # Interactive CLI runner demo
├── pyproject.toml              # Project dependencies and configuration
├── requirements.txt            # Package requirement list
├── README.md                   # Platform documentation
├── omnimind/
│   ├── core/                   # Agent abstractions & workflow DAG engine
│   │   ├── base_agent.py
│   │   ├── agent_roles.py
│   │   ├── workflow_engine.py
│   │   └── memory.py
│   ├── tools/                  # Dynamic tool registry & built-in tools
│   │   ├── base_tool.py
│   │   ├── registry.py
│   │   └── builtin_tools.py
│   ├── rag/                    # Vector store, chunking, retriever & embeddings
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── providers/              # LLM provider abstractions & mock provider
│   │   └── llm_provider.py
│   └── api/                    # FastAPI REST API & SSE streaming endpoints
│       ├── app.py
│       └── models.py
└── tests/                      # Pytest unit & integration test suite
    ├── test_agents.py
    ├── test_workflow.py
    ├── test_tools.py
    ├── test_rag.py
    └── test_api.py
```

---

## ⚡ Quick Start

### 1. Installation
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

### 2. Run Interactive CLI
Run the multi-agent demonstration:
```bash
python main.py
```

### 3. Run Test Suite
Run `pytest` to execute all unit and integration tests:
```bash
pytest -v
```

### 4. Launch FastAPI Server
```bash
uvicorn omnimind.api.app:app --reload --port 8000
```
Access the interactive OpenAPI UI at `http://127.0.0.1:8000/docs`.

---

## 🔗 Key API Endpoints

- `GET /health`: System health check & active agent roster.
- `POST /api/v1/agent/run`: Run single agent action.
- `GET /api/v1/agent/stream`: Stream agent execution steps via Server-Sent Events.
- `POST /api/v1/rag/ingest`: Ingest document into knowledge vector store.
- `POST /api/v1/rag/query`: Query Enterprise RAG store.
- `POST /api/v1/workflow/run`: Execute multi-agent DAG or sequential workflows.

---

## 🛡️ License
Distributed under the MIT License.
