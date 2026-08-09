import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from omnimind.providers.llm_provider import LLMMessage, Role

logger = logging.getLogger("omnimind.core.memory")


class AgentMemory(BaseModel):
    """Multi-tiered memory component for agents and workflows."""

    short_term_messages: List[LLMMessage] = Field(default_factory=list)
    working_state: Dict[str, Any] = Field(default_factory=dict)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)

    def add_message(self, role: Role, content: str, name: Optional[str] = None) -> None:
        """Append message to short term context."""
        self.short_term_messages.append(LLMMessage(role=role, content=content, name=name))

    def update_state(self, key: str, value: Any) -> None:
        """Set shared working state key-value."""
        self.working_state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get shared working state key."""
        return self.working_state.get(key, default)

    def log_step(self, agent_name: str, step_type: str, details: Dict[str, Any]) -> None:
        """Log an execution step trace."""
        trace = {
            "agent": agent_name,
            "step_type": step_type,
            "details": details
        }
        self.execution_trace.append(trace)

    def clear_short_term(self) -> None:
        """Clear conversation buffer."""
        self.short_term_messages.clear()
