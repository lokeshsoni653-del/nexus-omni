import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel, Field

logger = logging.getLogger("omnimind.providers")


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class LLMMessage(BaseModel):
    role: Role
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class LLMResponse(BaseModel):
    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tokens_used: int = 0
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate response from LLM."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """Stream chunks from LLM."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock LLM provider for testing and offline execution."""

    def __init__(self, custom_responses: Optional[Dict[str, str]] = None):
        self.custom_responses = custom_responses or {}

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.role == Role.USER:
                last_user_msg = msg.content
                break

        # Check custom rules
        for key, response_text in self.custom_responses.items():
            if key.lower() in last_user_msg.lower():
                return LLMResponse(content=response_text, tokens_used=len(response_text.split()))

        # Check if tool invocation is needed based on available tools
        tool_calls = []
        if tools and "search" in last_user_msg.lower():
            for t in tools:
                if t.get("name") in ["web_search", "document_retrieval"]:
                    tool_calls.append(
                        ToolCall(
                            id="call_mock_123",
                            name=t["name"],
                            arguments={"query": last_user_msg}
                        )
                    )
                    return LLMResponse(
                        content=f"I need to use {t['name']} to look up information.",
                        tool_calls=tool_calls,
                        finish_reason="tool_calls"
                    )

        # Default intelligent response based on role context
        system_prompt = next((m.content for m in messages if m.role == Role.SYSTEM), "")
        
        reply = f"[Mock LLM Response] Processed query: '{last_user_msg}' under context: '{system_prompt[:60]}...'"
        return LLMResponse(content=reply, tokens_used=len(reply.split()))

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        response = await self.generate(messages, tools, temperature, max_tokens)
        words = response.content.split(" ")
        for word in words:
            yield word + " "
