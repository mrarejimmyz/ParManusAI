"""
Unified Tool Architecture - Eliminates Duplication in Tool Implementations
Provides consistent LLM integration and execution patterns for all tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.config import config
from app.logger import logger


class ToolCapability:
    """Defines tool capabilities and categories."""

    # Core capabilities
    TEXT_PROCESSING = "text_processing"
    FILE_OPERATIONS = "file_operations"
    NETWORK_ACCESS = "network_access"
    SYSTEM_INTERACTION = "system_interaction"
    DATA_ANALYSIS = "data_analysis"

    # Specialized capabilities
    WEB_SCRAPING = "web_scraping"
    CODE_EXECUTION = "code_execution"
    BROWSER_AUTOMATION = "browser_automation"
    VISUAL_PROCESSING = "visual_processing"


class ToolResult(BaseModel):
    """Unified result structure for all tools."""

    success: bool
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        if self.success:
            return self.content or str(self.data) or "Operation completed successfully"
        else:
            return self.error or "Operation failed"


class ToolConfig(BaseModel):
    """Configuration for tool behavior."""

    name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    requires_llm: bool = Field(default=False)
    max_retries: int = Field(default=3)
    timeout: Optional[int] = None
    enable_caching: bool = Field(default=True)


class BaseTool(BaseModel, ABC):
    """
    Unified base tool that provides consistent structure and LLM integration.
    All tools inherit from this to eliminate duplication.
    """

    config: ToolConfig
    llm: Optional[Any] = None  # LLM instance if needed

    # Execution tracking
    execution_count: int = Field(default=0)
    last_result: Optional[ToolResult] = None
    cache: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize LLM if required
        if self.config.requires_llm and self.llm is None:
            from app.llm import LLM

            self.llm = LLM()
            logger.debug(f"🧠 Initialized LLM for tool: {self.config.name}")

    @property
    def name(self) -> str:
        """Tool name for identification."""
        return self.config.name

    @property
    def description(self) -> str:
        """Tool description for LLM context."""
        return self.config.description

    async def execute(self, **kwargs) -> ToolResult:
        """
        Main execution method with unified error handling and caching.
        """
        self.execution_count += 1

        # Check cache if enabled
        if self.config.enable_caching:
            cache_key = self._generate_cache_key(kwargs)
            if cache_key in self.cache:
                logger.debug(f"📋 Cache hit for {self.config.name}")
                return self.cache[cache_key]

        # Execute with retries
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"🔧 Executing {self.config.name} (attempt {attempt + 1})")

                # Pre-execution hook
                await self._pre_execute(**kwargs)

                # Main execution
                result = await self._execute(**kwargs)

                # Post-execution hook
                await self._post_execute(result, **kwargs)

                # Cache successful results
                if self.config.enable_caching and result.success:
                    cache_key = self._generate_cache_key(kwargs)
                    self.cache[cache_key] = result

                self.last_result = result
                return result

            except Exception as e:
                error_msg = (
                    f"Tool {self.config.name} failed on attempt {attempt + 1}: {str(e)}"
                )
                logger.warning(error_msg)

                if attempt == self.config.max_retries - 1:
                    # Final attempt failed
                    result = ToolResult(
                        success=False,
                        error=error_msg,
                        metadata={"attempts": attempt + 1},
                    )
                    self.last_result = result
                    return result

        # This should never be reached, but just in case
        result = ToolResult(success=False, error="Unknown execution error")
        self.last_result = result
        return result

    @abstractmethod
    async def _execute(self, **kwargs) -> ToolResult:
        """Core execution logic - implemented by specific tools."""
        pass

    async def _pre_execute(self, **kwargs):
        """Hook called before execution (can be overridden)."""
        pass

    async def _post_execute(self, result: ToolResult, **kwargs):
        """Hook called after execution (can be overridden)."""
        pass

    def _generate_cache_key(self, kwargs: Dict) -> str:
        """Generate cache key for the execution parameters."""
        import hashlib
        import json

        # Create a deterministic string from kwargs
        sorted_items = sorted(kwargs.items())
        key_string = json.dumps(sorted_items, sort_keys=True, default=str)

        # Hash for consistent key length
        return hashlib.md5(key_string.encode()).hexdigest()

    async def llm_analyze(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Helper method for LLM analysis within tools."""
        if not self.llm:
            raise ValueError(f"LLM not available for tool {self.config.name}")

        full_prompt = f"""Tool: {self.config.name}
Context: {context or {}}

{prompt}"""

        return await self.llm.ask(full_prompt)

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.config.name,
                "description": self.config.description,
                "parameters": self._get_parameters_schema(),
            },
        }

    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for function calling."""
        pass


class LLMEnhancedTool(BaseTool):
    """Base class for tools that heavily use LLM reasoning."""

    def __init__(self, **kwargs):
        # Force LLM requirement
        if "config" in kwargs:
            kwargs["config"].requires_llm = True
        super().__init__(**kwargs)

    async def llm_plan_execution(self, task: str, context: Dict) -> Dict[str, Any]:
        """Use LLM to plan tool execution strategy."""
        planning_prompt = f"""You are planning execution for the {self.config.name} tool.

Task: {task}
Context: {context}
Tool Capabilities: {self.config.capabilities}

Plan the optimal execution strategy. Consider:
1. What approach would be most effective?
2. What parameters should be used?
3. What potential issues might arise?
4. How should results be processed?

Return a JSON plan with strategy, parameters, and considerations."""

        plan_text = await self.llm.ask(planning_prompt)

        try:
            import json

            return json.loads(plan_text)
        except:
            # Fallback to text-based plan
            return {"strategy": "default", "notes": plan_text}

    async def llm_analyze_result(self, result: Any, expected: str) -> Dict[str, Any]:
        """Use LLM to analyze tool execution results."""
        analysis_prompt = f"""Analyze the result of {self.config.name} tool execution.

Expected: {expected}
Actual Result: {result}

Provide analysis:
1. Was the execution successful?
2. Does the result meet expectations?
3. Are there any issues or improvements needed?
4. What should be the next step?

Return JSON with success assessment and recommendations."""

        analysis_text = await self.llm.ask(analysis_prompt)

        try:
            import json

            return json.loads(analysis_text)
        except:
            return {"analysis": analysis_text}


class SimpleExecuteTool(BaseTool):
    """Simple tool template for basic execution patterns."""

    def __init__(self, name: str, description: str, execute_func, **kwargs):
        config = ToolConfig(name=name, description=description)
        super().__init__(config=config, **kwargs)
        self.execute_func = execute_func

    async def _execute(self, **kwargs) -> ToolResult:
        """Execute the provided function."""
        try:
            result = await self.execute_func(**kwargs)
            return ToolResult(success=True, content=str(result))
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Basic schema - can be overridden."""
        return {"type": "object", "properties": {}, "required": []}


class ToolRegistry:
    """Central registry for all available tools."""

    _tools: Dict[str, type] = {}

    @classmethod
    def register(cls, tool_class: type):
        """Register a tool class."""
        tool_name = getattr(tool_class, "name", tool_class.__name__)
        cls._tools[tool_name] = tool_class
        logger.debug(f"📝 Registered tool: {tool_name}")

    @classmethod
    def get_tool(cls, name: str) -> Optional[type]:
        """Get tool class by name."""
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> List[str]:
        """List all registered tool names."""
        return list(cls._tools.keys())

    @classmethod
    def create_tool(cls, name: str, **kwargs) -> Optional[BaseTool]:
        """Create tool instance by name."""
        tool_class = cls.get_tool(name)
        if tool_class:
            return tool_class(**kwargs)
        return None


# Decorator for easy tool registration
def register_tool(tool_class):
    """Decorator to automatically register tools."""
    ToolRegistry.register(tool_class)
    return tool_class


# Factory for creating common tool types
class ToolFactory:
    """Factory for creating standardized tool instances."""

    @staticmethod
    def create_simple_tool(name: str, description: str, execute_func) -> SimpleTool:
        """Create a simple tool from a function."""
        return SimpleExecuteTool(name, description, execute_func)

    @staticmethod
    def create_llm_tool(
        name: str, description: str, capabilities: List[str]
    ) -> LLMEnhancedTool:
        """Create an LLM-enhanced tool template."""

        class CustomLLMTool(LLMEnhancedTool):
            def __init__(self):
                config = ToolConfig(
                    name=name,
                    description=description,
                    capabilities=capabilities,
                    requires_llm=True,
                )
                super().__init__(config=config)

            async def _execute(self, **kwargs) -> ToolResult:
                # Default implementation - should be overridden
                return ToolResult(success=True, content="LLM tool executed")

            def _get_parameters_schema(self) -> Dict[str, Any]:
                return {"type": "object", "properties": {}, "required": []}

        return CustomLLMTool()


# Export unified interface
__all__ = [
    "BaseTool",
    "LLMEnhancedTool",
    "SimpleExecuteTool",
    "ToolResult",
    "ToolConfig",
    "ToolCapability",
    "ToolRegistry",
    "ToolFactory",
    "register_tool",
]
