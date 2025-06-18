"""
Unified LLM Core - Single Point of Truth for All LLM Interactions
Eliminates the 3+ different LLM implementations with a clean, extensible interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from app.config import LLMSettings, config
from app.logger import logger
from app.schema import Message, ToolChoice


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def ask(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Basic text generation."""
        pass

    @abstractmethod
    async def ask_tool(
        self, messages: List[Dict[str, Any]], tools: List[Dict], **kwargs
    ) -> Dict:
        """Tool-calling generation."""
        pass

    @abstractmethod
    async def ask_vision(
        self, messages: List[Dict[str, Any]], images: List[str], **kwargs
    ) -> str:
        """Vision-enabled generation."""
        pass

    @abstractmethod
    def get_token_count(self) -> Dict[str, int]:
        """Get usage statistics."""
        pass


class TokenCounter:
    """Unified token counting across all providers."""

    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def update(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens

    def reset(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0


class MessageFormatter:
    """Unified message formatting for all providers."""

    @staticmethod
    def format_messages(messages: Union[str, List, Dict]) -> List[Dict[str, Any]]:
        """Convert any message format to standard OpenAI format."""
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]

        if isinstance(messages, dict):
            messages = [messages]

        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted.append(msg.to_dict())
            elif isinstance(msg, dict):
                # Ensure required fields
                formatted_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", str(msg)),
                }
                formatted.append(formatted_msg)
            else:
                formatted.append({"role": "user", "content": str(msg)})

        return formatted


class OllamaProvider(BaseLLMProvider):
    """Unified Ollama provider combining all functionality."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.token_counter = TokenCounter()
        self.formatter = MessageFormatter()

        # Initialize OpenAI client for Ollama
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key,
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

            return {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls or [],
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

    def get_token_count(self) -> Dict[str, int]:
        """Get unified token count."""
        return {
            "prompt_tokens": self.token_counter.prompt_tokens,
            "completion_tokens": self.token_counter.completion_tokens,
            "total_tokens": self.token_counter.total_tokens,
        }

    def reset_token_count(self):
        """Reset token counter."""
        self.token_counter.reset()


class UnifiedLLM:
    """
    Single, unified LLM interface that replaces all existing implementations.
    Provides consistent API across all providers and capabilities.
    """

    def __init__(self, settings: Optional[LLMSettings] = None):
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

    async def ask(self, messages: Union[str, List, Dict], **kwargs) -> str:
        """Universal text generation."""
        return await self._provider.ask(messages, **kwargs)

    async def ask_tool(
        self, messages: Union[str, List, Dict], tools: List[Dict], **kwargs
    ) -> Dict:
        """Universal tool calling."""
        return await self._provider.ask_tool(messages, tools, **kwargs)

    async def ask_vision(
        self, messages: Union[str, List, Dict], images: List[str] = None, **kwargs
    ) -> str:
        """Universal vision generation."""
        return await self._provider.ask_vision(messages, images or [], **kwargs)

    def get_token_count(self) -> Dict[str, int]:
        """Get usage statistics."""
        return self._provider.get_token_count()

    def reset_token_count(self):
        """Reset usage statistics."""
        self._provider.reset_token_count()

    # Legacy compatibility methods
    def _format_prompt_for_llama(self, messages: List[Dict[str, Any]]) -> str:
        """Legacy compatibility method."""
        return "\n".join(
            [
                f"<|{msg.get('role', 'user')}|>\n{msg.get('content', '')}"
                for msg in messages
            ]
        )

    @property
    def text_model(self):
        """Legacy compatibility property."""
        return self.model

    @property
    def vision_model(self):
        """Legacy compatibility property."""
        return self.settings.vision.model if self.settings.vision else self.model


# Factory function for backward compatibility
def create_llm_with_tools(config_or_settings=None):
    """Factory function that creates unified LLM instance."""
    if hasattr(config_or_settings, "llm"):
        settings = config_or_settings.llm
    else:
        settings = config_or_settings

    return UnifiedLLM(settings)


# Export unified interface
LLM = UnifiedLLM
__all__ = ["UnifiedLLM", "LLM", "create_llm_with_tools"]
