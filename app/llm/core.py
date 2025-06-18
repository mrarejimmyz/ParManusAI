"""
Unified LLM Core - Single Interface for All LLM Operations
Eliminates duplication across 6+ LLM implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.config import config
from app.logger import logger


class TokenCounter(BaseModel):
    """Unified token counting across all providers."""

    prompt_tokens: int = Field(default=0, description="Total prompt tokens used")
    completion_tokens: int = Field(
        default=0, description="Total completion tokens used"
    )

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used."""
        return self.prompt_tokens + self.completion_tokens

    def update(self, prompt_tokens: int, completion_tokens: int):
        """Update token counts."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens

    def reset(self):
        """Reset token counts."""
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def get_dict(self) -> Dict[str, int]:
        """Get token counts as dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class MessageFormatter:
    """Unified message formatting for all providers."""

    @staticmethod
    def format_messages(messages: List[Union[Dict, Any]]) -> List[Dict[str, Any]]:
        """Format messages to OpenAI-compatible format."""
        formatted = []

        for msg in messages:
            if isinstance(msg, dict):
                formatted.append(msg)
            elif hasattr(msg, "to_dict"):
                formatted.append(msg.to_dict())
            elif hasattr(msg, "model_dump"):
                formatted.append(msg.model_dump())
            else:
                # Fallback - assume it's a string
                formatted.append({"role": "user", "content": str(msg)})

        return formatted

    @staticmethod
    def format_tool_calls(tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Format tool calls to standard format."""
        formatted = []

        for i, tool_call in enumerate(tool_calls):
            if hasattr(tool_call, "id") and hasattr(tool_call, "function"):
                # OpenAI object format
                formatted.append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                )
            elif isinstance(tool_call, dict):
                # Dict format - ensure proper structure
                formatted.append(
                    {
                        "id": tool_call.get("id", f"call_{i}"),
                        "type": "function",
                        "function": {
                            "name": tool_call.get("function", {}).get("name", ""),
                            "arguments": tool_call.get("function", {}).get(
                                "arguments", "{}"
                            ),
                        },
                    }
                )
            else:
                # Fallback - create basic structure
                formatted.append(
                    {
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {"name": str(tool_call), "arguments": "{}"},
                    }
                )

        return formatted


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, settings):
        self.settings = settings
        self.token_counter = TokenCounter()
        self.formatter = MessageFormatter()

    @abstractmethod
    async def ask(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Basic text generation."""
        pass

    @abstractmethod
    async def ask_tool(
        self, messages: List[Dict[str, Any]], tools: List[Dict], **kwargs
    ) -> Dict:
        """Tool calling interface."""
        pass

    @abstractmethod
    async def ask_vision(
        self, messages: List[Dict[str, Any]], images: List[str], **kwargs
    ) -> str:
        """Vision model interface."""
        pass

    def get_token_count(self) -> Dict[str, int]:
        """Get unified token count."""
        return self.token_counter.get_dict()

    def reset_token_count(self):
        """Reset token counter."""
        self.token_counter.reset()


class OllamaProvider(BaseLLMProvider):
    """Unified Ollama provider combining all functionality."""

    def __init__(self, settings):
        super().__init__(settings)

        # Initialize OpenAI client for Ollama
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key or "ollama",
        )

        logger.info(f"🚀 Initialized Unified Ollama Provider: {settings.model}")

    async def ask(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Unified ask implementation."""
        formatted_messages = self.formatter.format_messages(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model,
                messages=formatted_messages,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                **kwargs,
            )

            content = response.choices[0].message.content

            # Update token counter
            if hasattr(response, "usage") and response.usage:
                self.token_counter.update(
                    response.usage.prompt_tokens, response.usage.completion_tokens
                )

            return content

        except Exception as e:
            logger.error(f"Error in Ollama ask: {e}")
            raise

    async def ask_tool(
        self, messages: List[Dict[str, Any]], tools: List[Dict], **kwargs
    ) -> Dict:
        """Unified tool calling implementation."""
        formatted_messages = self.formatter.format_messages(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model,
                messages=formatted_messages,
                tools=tools,
                tool_choice=kwargs.get("tool_choice", "auto"),
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                **{k: v for k, v in kwargs.items() if k != "tool_choice"},
            )

            # Update token counter
            if hasattr(response, "usage") and response.usage:
                self.token_counter.update(
                    response.usage.prompt_tokens, response.usage.completion_tokens
                )

            message = response.choices[0].message
            tool_calls = self.formatter.format_tool_calls(message.tool_calls or [])

            return {
                "content": message.content or "",
                "tool_calls": tool_calls,
                "usage": (
                    response.usage.model_dump() if hasattr(response, "usage") else {}
                ),
            }

        except Exception as e:
            logger.error(f"Error in Ollama ask_tool: {e}")
            raise

    async def ask_vision(
        self, messages: List[Dict[str, Any]], images: List[str], **kwargs
    ) -> str:
        """Unified vision implementation."""
        formatted_messages = self.formatter.format_messages(messages)

        # Add images to the last user message
        if images and formatted_messages:
            last_msg = formatted_messages[-1]
            if last_msg.get("role") == "user":
                content = []
                if last_msg.get("content"):
                    content.append({"type": "text", "text": last_msg["content"]})

                for image in images:
                    content.append({"type": "image_url", "image_url": {"url": image}})

                last_msg["content"] = content

        # Use vision model if available, otherwise fallback to main model
        model = (
            self.settings.vision.model
            if self.settings.vision and self.settings.vision.enabled
            else self.settings.model
        )

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                **kwargs,
            )

            content = response.choices[0].message.content

            # Update token counter
            if hasattr(response, "usage") and response.usage:
                self.token_counter.update(
                    response.usage.prompt_tokens, response.usage.completion_tokens
                )

            return content

        except Exception as e:
            logger.error(f"Error in Ollama ask_vision: {e}")
            raise


class UnifiedLLM:
    """
    Unified LLM Interface - Single entry point for all LLM operations.

    Replaces all existing LLM implementations with a single, consistent interface.
    Automatically routes to the appropriate provider based on configuration.
    """

    def __init__(self, settings=None):
        self.settings = settings or config.llm
        self._provider = self._create_provider()

        # Expose common properties
        self.model = self.settings.model
        self.max_tokens = self.settings.max_tokens
        self.temperature = self.settings.temperature
        self.vision_enabled = (
            self.settings.vision and self.settings.vision.enabled
            if self.settings.vision
            else False
        )

    def _create_provider(self) -> BaseLLMProvider:
        """Create appropriate provider based on settings."""
        api_type = getattr(self.settings, "api_type", "ollama").lower()

        if api_type == "ollama":
            return OllamaProvider(self.settings)
        else:
            # Future: Add OpenAI, Anthropic, etc.
            raise NotImplementedError(f"Provider '{api_type}' not yet implemented")

    async def ask(self, messages: Union[str, List], **kwargs) -> str:
        """
        Basic text generation interface.

        Args:
            messages: String or list of messages
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        return await self._provider.ask(messages, **kwargs)

    async def ask_tool(
        self, messages: Union[str, List], tools: List[Dict], **kwargs
    ) -> Dict:
        """
        Tool calling interface.

        Args:
            messages: String or list of messages
            tools: List of tool definitions
            **kwargs: Additional parameters (tool_choice, etc.)

        Returns:
            Dict with content, tool_calls, and usage information
        """
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        return await self._provider.ask_tool(messages, tools, **kwargs)

    async def ask_vision(
        self, messages: Union[str, List], images: List[str] = None, **kwargs
    ) -> str:
        """
        Vision model interface.

        Args:
            messages: String or list of messages
            images: List of image URLs/paths
            **kwargs: Additional parameters

        Returns:
            Generated text response with vision understanding
        """
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        images = images or []
        return await self._provider.ask_vision(messages, images, **kwargs)

    def get_token_count(self) -> Dict[str, int]:
        """Get current token usage statistics."""
        return self._provider.get_token_count()

    def reset_token_count(self):
        """Reset token usage counter."""
        self._provider.reset_token_count()

    # Legacy compatibility methods
    def get_token_usage(self) -> Dict[str, int]:
        """Legacy method name compatibility."""
        return self.get_token_count()

    @property
    def text_model(self):
        """Legacy property compatibility."""
        return self.model

    @property
    def vision_model(self):
        """Legacy property compatibility."""
        return (
            self.settings.vision.model
            if self.settings.vision and self.settings.vision.enabled
            else self.model
        )


# Factory function for backward compatibility
def create_llm(settings=None):
    """Factory function to create UnifiedLLM instance."""
    return UnifiedLLM(settings)


# Legacy aliases for backward compatibility
LLM = UnifiedLLM
create_llm_with_tools = create_llm
