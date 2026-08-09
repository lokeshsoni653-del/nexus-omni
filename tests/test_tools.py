import pytest
from omnimind.tools import (
    ToolRegistry, WebSearchTool, PythonCodeExecutorTool, HTTPClientTool, DocumentRetrievalTool
)


@pytest.mark.asyncio
async def test_tool_registry():
    registry = ToolRegistry()
    tool = WebSearchTool()
    registry.register(tool)

    assert "web_search" in registry.list_tools()
    retrieved = registry.get_tool("web_search")
    assert retrieved is tool

    res = await registry.execute_tool("web_search", query="OmniMind AI")
    assert res.success is True
    assert res.output["query"] == "OmniMind AI"


@pytest.mark.asyncio
async def test_python_executor_tool():
    executor = PythonCodeExecutorTool()
    res = await executor.execute(code="a = 10\nb = 20\nprint(a + b)")
    assert res.success is True
    assert res.output["stdout"] == "30"


@pytest.mark.asyncio
async def test_python_executor_security():
    executor = PythonCodeExecutorTool()
    res = await executor.execute(code="import os\nos.system('echo hacked')")
    assert res.success is True
    assert "Operation 'import os' is restricted" in res.output["error"]
