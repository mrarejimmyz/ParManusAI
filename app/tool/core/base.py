"""
Unified Tool Core - Single Base Class for All Tools
Eliminates duplication across 10+ tool base implementations.
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.config import config
from app.llm import LLM
from app.logger import logger
from app.tool.core.hallucination_detector import hallucination_detector


class ToolResult(BaseModel):
    """Standardized result from tool execution."""

    success: bool = Field(..., description="Whether execution was successful")
    content: Optional[Any] = Field(default=None, description="Tool output content")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )
    execution_time: Optional[float] = Field(
        default=None, description="Execution time in seconds"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "metadata": self.metadata or {},
            "execution_time": self.execution_time,
        }

    def __str__(self) -> str:
        """String representation for logging."""
        if self.success:
            return f"Success: {self.content}"
        else:
            return f"Error: {self.error}"


class ToolConfig(BaseModel):
    """Configuration for tool behavior."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameter schema"
    )

    # Execution settings
    timeout: Optional[float] = Field(default=None, description="Execution timeout")
    retries: int = Field(default=0, description="Number of retries on failure")
    cache_enabled: bool = Field(default=False, description="Enable result caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")

    # LLM integration
    llm_enabled: bool = Field(default=False, description="Enable LLM-driven behavior")
    llm_reasoning: bool = Field(
        default=False, description="Enable LLM reasoning before execution"
    )

    # Validation
    validate_params: bool = Field(default=True, description="Validate parameters")
    sanitize_input: bool = Field(default=True, description="Sanitize input parameters")


class BaseTool(BaseModel, ABC):
    """
    Unified base class for all tools.

    Replaces all existing tool base classes with a single, consistent interface.
    Provides standardized execution, validation, caching, and LLM integration.
    """

    # Core configuration
    config: ToolConfig = Field(..., description="Tool configuration")

    # LLM integration
    llm: Optional[LLM] = Field(
        default=None, description="LLM instance for intelligent behavior"
    )

    # Execution tracking
    execution_count: int = Field(default=0, description="Number of executions")
    last_execution_time: Optional[float] = Field(
        default=None, description="Last execution timestamp"
    )  # Cache storage
    cache: Dict[str, Any] = Field(default_factory=dict, description="Result cache")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        # Set default config if not provided
        if "config" not in kwargs and "name" in kwargs:
            kwargs["config"] = ToolConfig(
                name=kwargs.pop("name"),
                description=kwargs.pop("description", ""),
                parameters=kwargs.pop("parameters", {}),
                **{k: v for k, v in kwargs.items() if k in ToolConfig.__fields__},
            )

        super().__init__(**kwargs)

        # Initialize LLM if enabled
        if self.config.llm_enabled and not self.llm:
            self.llm = LLM()

        logger.debug(f"🔧 Initialized tool: {self.config.name}")

    # Abstract method that subclasses must implement
    @abstractmethod
    async def _execute(self, **kwargs) -> ToolResult:
        """
        Core execution logic - implemented by specific tools.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Execution result
        """
        pass

    # Main execution interface
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with full framework support.

        Args:
            **kwargs: Tool parameters        Returns:
            ToolResult: Execution result with metadata
        """
        start_time = time.time()
        self.execution_count += 1
        self.last_execution_time = start_time

        try:
            # Validate parameters
            if self.config.validate_params:
                await self._validate_parameters(kwargs)

            # Sanitize input
            if self.config.sanitize_input:
                kwargs = await self._sanitize_input(kwargs)

            # Hallucination detection
            hallucination_result = (
                hallucination_detector.detect_hallucinated_parameters(
                    self.config.name, kwargs
                )
            )

            if hallucination_result["is_hallucination"]:
                logger.warning(
                    f"🎭 Hallucination detected in {self.config.name}, using safe alternatives"
                )
                kwargs = hallucination_detector.generate_safe_alternative(
                    self.config.name, kwargs
                )
                # Add detection metadata
                kwargs["_detection_metadata"] = hallucination_result

            # Check cache
            if self.config.cache_enabled:
                cache_key = self._generate_cache_key(kwargs)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    logger.debug(f"🎯 Cache hit for {self.config.name}")
                    cached_result.execution_time = time.time() - start_time
                    return cached_result

            # LLM reasoning (if enabled)
            if self.config.llm_reasoning and self.llm:
                kwargs = await self._llm_reasoning(kwargs)

            # Pre-execution hook
            await self._pre_execute(**kwargs)

            # Execute with timeout and retries
            result = await self._execute_with_retries(**kwargs)

            # Post-execution hook
            await self._post_execute(result, **kwargs)

            # Cache result
            if self.config.cache_enabled and result.success:
                cache_key = self._generate_cache_key(kwargs)
                self._cache_result(cache_key, result)

            # Add execution metadata
            result.execution_time = time.time() - start_time
            result.metadata = result.metadata or {}
            result.metadata.update(
                {
                    "tool_name": self.config.name,
                    "execution_count": self.execution_count,
                    "timestamp": start_time,
                }
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"❌ Tool {self.config.name} failed after {execution_time:.2f}s: {e}"
            )

            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "tool_name": self.config.name,
                    "execution_count": self.execution_count,
                    "timestamp": start_time,
                },
            )

    # Execution framework methods
    async def _execute_with_retries(self, **kwargs) -> ToolResult:
        """Execute with retry logic."""
        last_error = None

        for attempt in range(self.config.retries + 1):
            try:
                if self.config.timeout:
                    # TODO: Implement timeout logic
                    result = await self._execute(**kwargs)
                else:
                    result = await self._execute(**kwargs)

                if result.success:
                    return result
                else:
                    last_error = result.error
                    if attempt < self.config.retries:
                        logger.warning(
                            f"⚠️ Tool {self.config.name} attempt {attempt + 1} failed: {result.error}"
                        )
                        await self._retry_delay(attempt)

            except Exception as e:
                last_error = str(e)
                if attempt < self.config.retries:
                    logger.warning(
                        f"⚠️ Tool {self.config.name} attempt {attempt + 1} error: {e}"
                    )
                    await self._retry_delay(attempt)
                else:
                    raise

        return ToolResult(
            success=False,
            error=f"Failed after {self.config.retries + 1} attempts: {last_error}",
        )

    async def _retry_delay(self, attempt: int):
        """Delay between retry attempts."""
        import asyncio

        delay = min(2**attempt, 10)  # Exponential backoff, max 10s
        await asyncio.sleep(delay)

    # Hook methods (can be overridden)
    async def _pre_execute(self, **kwargs):
        """Hook called before execution (can be overridden)."""
        pass

    async def _post_execute(self, result: ToolResult, **kwargs):
        """Hook called after execution (can be overridden)."""
        pass

    async def _validate_parameters(self, kwargs: Dict[str, Any]):
        """Validate input parameters against schema."""
        # Basic validation - subclasses can override for specific validation
        if self.config.parameters:
            required = self.config.parameters.get("required", [])
            for param in required:
                if param not in kwargs:
                    raise ValueError(f"Required parameter '{param}' missing")

    async def _sanitize_input(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input parameters."""
        # Basic sanitization - subclasses can override
        sanitized = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                # Basic string sanitization
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value
        return sanitized

    async def _llm_reasoning(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to reason about parameters and optimize execution."""
        if not self.llm:
            return kwargs

        reasoning_prompt = f"""
        I'm about to execute the tool '{self.config.name}' with these parameters:
        {json.dumps(kwargs, indent=2)}

        Tool description: {self.config.description}

        Please analyze these parameters and suggest any optimizations or corrections.
        Return the parameters as JSON.
        """

        try:
            response = await self.llm.ask(reasoning_prompt)
            # Try to parse JSON response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                optimized_params = json.loads(
                    json_match.group()
                )  # Validate that optimized_params is a dict and has reasonable structure
                if not isinstance(optimized_params, dict):
                    logger.warning(
                        f"⚠️ LLM returned non-dict parameters for {self.config.name}, falling back to original"
                    )
                    return kwargs

                # Ensure that string parameters remain strings (prevent dict values for string params)
                validated_params = {}
                for key, value in optimized_params.items():
                    # Critical: Ensure no complex objects that could cause .lower() errors
                    if isinstance(value, (dict, list)):
                        logger.warning(
                            f"⚠️ LLM returned complex type for '{key}': {type(value)}, converting to string"
                        )
                        validated_params[key] = str(value)
                    elif value is None:
                        validated_params[key] = ""
                    # If the original parameter was a string, ensure the optimized one is too
                    if key in kwargs and isinstance(kwargs[key], str):
                        if (
                            not isinstance(value, (str, int, float, bool))
                            or value is None
                        ):
                            logger.warning(
                                f"⚠️ LLM changed string param '{key}' to complex type {type(value)}, using original"
                            )
                            validated_params[key] = kwargs[key]
                        else:
                            validated_params[key] = str(value)  # Ensure it's a string
                    else:
                        validated_params[key] = value

                # Add any missing parameters from original kwargs
                for key, value in kwargs.items():
                    if key not in validated_params:
                        validated_params[key] = value

                logger.info(f"🧠 LLM optimized parameters for {self.config.name}")
                return validated_params
        except Exception as e:
            logger.warning(f"⚠️ LLM reasoning failed for {self.config.name}: {e}")

        return kwargs

    # Caching methods
    def _generate_cache_key(self, kwargs: Dict) -> str:
        """Generate cache key for the execution parameters."""
        # Create a deterministic string from kwargs
        sorted_items = sorted(kwargs.items())
        key_string = json.dumps(
            sorted_items, sort_keys=True, default=str
        )  # Hash for consistent key length
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[ToolResult]:
        """Get cached result if available and not expired."""
        if cache_key not in self.cache:
            return None

        cached_entry = self.cache[cache_key]
        if time.time() - cached_entry["timestamp"] > self.config.cache_ttl:
            del self.cache[cache_key]
            return None

        return cached_entry["result"]

    def _cache_result(self, cache_key: str, result: ToolResult):
        """Cache execution result."""
        self.cache[cache_key] = {"result": result, "timestamp": time.time()}

    # Utility methods
    def get_name(self) -> str:
        """Get tool name."""
        return self.config.name

    def get_description(self) -> str:
        """Get tool description."""
        return self.config.description

    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema."""
        return self.config.parameters

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "name": self.config.name,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time,
            "cache_entries": len(self.cache),
            "cache_enabled": self.config.cache_enabled,
            "llm_enabled": self.config.llm_enabled,
        }

    def to_param(self) -> Dict[str, Any]:
        """Convert tool to function call format for LLM usage."""
        return {
            "type": "function",
            "function": {
                "name": self.config.name,
                "description": self.config.description,
                "parameters": self.config.parameters,
            },
        }

    def clear_cache(self):
        """Clear cached results."""
        self.cache.clear()
        logger.debug(f"🧹 Cleared cache for {self.config.name}")


class ToolRegistry:
    """Registry for managing and discovering tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: BaseTool, category: str = "general"):
        """Register a tool in the registry."""
        tool_name = tool.get_name()
        self._tools[tool_name] = tool

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool_name)

        logger.debug(f"📝 Registered tool '{tool_name}' in category '{category}'")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get all tools in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self._categories.keys())

    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool."""
        tool = self._tools.get(name)
        if not tool:
            return None

        return {
            "name": tool.get_name(),
            "description": tool.get_description(),
            "parameters": tool.get_parameters(),
            "stats": tool.get_stats(),
        }


# Global tool registry instance
tool_registry = ToolRegistry()


# Utility functions
def register_tool(tool: BaseTool, category: str = "general"):
    """Register a tool in the global registry."""
    tool_registry.register(tool, category)


def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool from the global registry."""
    return tool_registry.get_tool(name)


def list_available_tools() -> List[str]:
    """List all available tools."""
    return tool_registry.list_tools()


__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolConfig",
    "ToolRegistry",
    "tool_registry",
    "register_tool",
    "get_tool",
    "list_available_tools",
]
