"""Collection classes for managing multiple tools."""

from typing import Any, Dict, List

from app.exceptions import ToolError
from app.logger import logger
from app.tool.base import BaseTool, ToolFailure, ToolResult


class ToolCollection:
    """A collection of defined tools."""

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, *tools: BaseTool):
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}

    def __iter__(self):
        return iter(self.tools)

    def to_params(self) -> List[Dict[str, Any]]:
        return [tool.to_param() for tool in self.tools]

    async def execute(
        self, *, name: str, tool_input: Dict[str, Any] = None
    ) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")

        # Ensure tool_input is a dict for unpacking
        if tool_input is None:
            tool_input = {}

        # Comprehensive parameter validation and type safety
        validated_input = {}
        for key, value in tool_input.items():
            # Ensure all parameter keys and values are safe for string operations
            if isinstance(value, dict):
                # Convert dict to string if it might be used with .lower()
                logger.warning(
                    f"🔧 Converting dict parameter '{key}' to string for safety: {value}"
                )
                validated_input[key] = str(value)
            elif value is None:
                validated_input[key] = ""
            else:
                validated_input[key] = value

        # Validate required parameters before execution
        if hasattr(tool, "config") and tool.config and tool.config.parameters:
            required_params = tool.config.parameters.get("required", [])
            missing_params = [
                param for param in required_params if param not in validated_input
            ]

            if missing_params:
                error_msg = f"Tool {name} missing required parameters: {missing_params}"
                logger.error(f"🚨 {error_msg}")
                return ToolFailure(error=error_msg)

        try:
            result = await tool.execute(**validated_input)
            return result
        except ToolError as e:
            return ToolFailure(error=e.message)
        except TypeError as e:
            if "missing" in str(e) and "required positional argument" in str(e):
                error_msg = f"Tool {name} execution failed - missing required arguments: {str(e)}"
                logger.error(f"🚨 {error_msg}")
                return ToolFailure(error=error_msg)
            else:
                raise

    async def execute_all(self) -> List[ToolResult]:
        """Execute all tools in the collection sequentially."""
        results = []
        for tool in self.tools:
            try:
                result = await tool.execute()
                results.append(result)
            except ToolError as e:
                results.append(ToolFailure(error=e.message))
        return results

    def get_tool(self, name: str) -> BaseTool:
        return self.tool_map.get(name)

    def add_tool(self, tool: BaseTool):
        """Add a single tool to the collection.

        If a tool with the same name already exists, it will be skipped and a warning will be logged.
        """
        if tool.name in self.tool_map:
            logger.warning(f"Tool {tool.name} already exists in collection, skipping")
            return self

        self.tools += (tool,)
        self.tool_map[tool.name] = tool
        return self

    def add_tools(self, *tools: BaseTool):
        """Add multiple tools to the collection.

        If any tool has a name conflict with an existing tool, it will be skipped and a warning will be logged.
        """
        for tool in tools:
            self.add_tool(tool)
        return self
