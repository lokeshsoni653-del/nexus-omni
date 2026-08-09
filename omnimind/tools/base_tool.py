from abc import ABC, abstractmethod
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field
import time


class ToolResult(BaseModel):
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class BaseTool(ABC):
    """Abstract Base Tool interface for all OmniMind AI agent tools."""

    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None

    def __init__(self):
        if not self.name or not self.description:
            raise ValueError("Tools must define name and description")

    @abstractmethod
    async def _run(self, **kwargs: Any) -> Any:
        """Internal execution logic to be implemented by child classes."""
        pass

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute tool with input validation and execution timing."""
        start_time = time.time()
        try:
            if self.args_schema:
                validated_args = self.args_schema(**kwargs)
                kwargs_dict = validated_args.model_dump()
            else:
                kwargs_dict = kwargs

            result = await self._run(**kwargs_dict)
            elapsed = (time.time() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=result,
                execution_time_ms=round(elapsed, 2)
            )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000.0
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=round(elapsed, 2)
            )

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert tool definition to JSON Schema format compatible with LLM function calling."""
        parameters = {}
        if self.args_schema:
            parameters = self.args_schema.model_json_schema()
            # Clean up metadata properties not required by LLMs
            parameters.pop("title", None)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters if parameters else {"type": "object", "properties": {}},
            }
        }
