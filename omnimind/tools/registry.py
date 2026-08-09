import logging
from typing import Dict, List, Optional, Any
from omnimind.tools.base_tool import BaseTool, ToolResult

logger = logging.getLogger("omnimind.tools.registry")


class ToolRegistry:
    """Central registry for discovering, executing, and managing tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool registration: {tool.name}")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def unregister(self, tool_name: str) -> bool:
        """Remove a tool from the registry."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get tool instance by name."""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute tool by name with arguments."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{tool_name}' is not registered."
            )
        return await tool.execute(**kwargs)

    def export_json_schemas(self) -> List[Dict[str, Any]]:
        """Export JSON schemas for all registered tools."""
        return [tool.to_json_schema() for tool in self._tools.values()]
