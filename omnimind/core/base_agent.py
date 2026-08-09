import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from omnimind.providers.llm_provider import BaseLLMProvider, MockLLMProvider, LLMMessage, Role
from omnimind.tools.registry import ToolRegistry
from omnimind.tools.base_tool import BaseTool, ToolResult
from omnimind.core.memory import AgentMemory

logger = logging.getLogger("omnimind.core.base_agent")


class AgentStepResult(BaseModel):
    agent_name: str
    thought: str
    action_taken: str
    output: Any
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """Abstract Base Class for OmniMind Autonomous AI Agents."""

    def __init__(
        self,
        name: str,
        role_description: str,
        system_prompt: str,
        llm_provider: Optional[BaseLLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory: Optional[AgentMemory] = None,
    ):
        self.name = name
        self.role_description = role_description
        self.system_prompt = system_prompt
        self.llm_provider = llm_provider or MockLLMProvider()
        self.tool_registry = tool_registry or ToolRegistry()
        self.memory = memory or AgentMemory()

    def register_tool(self, tool: BaseTool) -> None:
        """Register a specific tool for this agent."""
        self.tool_registry.register(tool)

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a registered tool by name."""
        return await self.tool_registry.execute_tool(tool_name, **kwargs)

    @abstractmethod
    async def process_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> AgentStepResult:
        """Core decision-making and action logic for specific agent role."""
        pass

    async def perceive(self, input_text: str) -> None:
        """Receive environment observation / input prompt."""
        self.memory.add_message(Role.USER, input_text)

    async def think(self) -> str:
        """Query LLM provider with current message history and available tool schemas."""
        messages = [LLMMessage(role=Role.SYSTEM, content=self.system_prompt)] + self.memory.short_term_messages
        tool_schemas = self.tool_registry.export_json_schemas()

        response = await self.llm_provider.generate(
            messages=messages,
            tools=tool_schemas if tool_schemas else None
        )
        return response.content
