import os
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


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini 1.5 Live AI Provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Gemini LLM Provider initialized with model: '{model_name}'.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini SDK: {e}")
                self.model = None
        else:
            self.model = None

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.model:
            # Fallback to Mock if API key missing
            return await MockLLMProvider().generate(messages, tools, temperature, max_tokens)

        # Build prompt from messages
        prompt_parts = []
        for msg in messages:
            prefix = "System Directive:" if msg.role == Role.SYSTEM else ("User:" if msg.role == Role.USER else "Assistant:")
            prompt_parts.append(f"{prefix}\n{msg.content}")

        full_prompt = "\n\n".join(prompt_parts)

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config={"temperature": temperature, "max_output_tokens": max_tokens}
            )
            text = response.text if hasattr(response, "text") and response.text else "No content returned from Gemini."
            return LLMResponse(content=text, tokens_used=len(text.split()))
        except Exception as err:
            logger.error(f"Gemini API error: {err}")
            return await MockLLMProvider().generate(messages, tools, temperature, max_tokens)

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        res = await self.generate(messages, tools, temperature, max_tokens)
        for word in res.content.split(" "):
            yield word + " "


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI GPT-4o / GPT-3.5 Live AI Provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name

        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info(f"OpenAI LLM Provider initialized with model: '{model_name}'.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI SDK: {e}")
                self.client = None
        else:
            self.client = None

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.client:
            return await MockLLMProvider().generate(messages, tools, temperature, max_tokens)

        formatted_messages = [{"role": m.role.value, "content": m.content} for m in messages]

        try:
            res = await self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = res.choices[0].message.content or ""
            return LLMResponse(content=content, tokens_used=res.usage.total_tokens if res.usage else len(content.split()))
        except Exception as err:
            logger.error(f"OpenAI API error: {err}")
            return await MockLLMProvider().generate(messages, tools, temperature, max_tokens)

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        res = await self.generate(messages, tools, temperature, max_tokens)
        for word in res.content.split(" "):
            yield word + " "


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

        # Default intelligent response based on role context
        system_prompt = next((m.content for m in messages if m.role == Role.SYSTEM), "")
        
        reply = f"Processed query: '{last_user_msg}' under context: '{system_prompt[:60]}...'"
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


def get_llm_provider(api_key: Optional[str] = None, provider_type: str = "auto") -> BaseLLMProvider:
    """Factory function to instantiate live Gemini, OpenAI, or Mock LLM Provider."""
    gemini_key = api_key or os.getenv("GEMINI_API_KEY")
    openai_key = api_key or os.getenv("OPENAI_API_KEY")

    if gemini_key:
        return GeminiLLMProvider(api_key=gemini_key)
    elif openai_key:
        return OpenAILLMProvider(api_key=openai_key)
    else:
        return MockLLMProvider()
