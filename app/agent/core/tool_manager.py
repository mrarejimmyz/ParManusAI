"""
Tool Manager - Handles tool execution, validation, and autonomous capabilities integration
"""

from typing import Any, Dict, List, Optional

from app.agent.autonomous_capabilities import AutonomousCapabilities
from app.logger import logger
from app.schema import ToolCall


class ToolManager:
    """Manages tool execution with validation and autonomous capabilities."""

    def __init__(self, agent):
        self.agent = agent
        self.autonomous_capabilities = AutonomousCapabilities()
        self.execution_history = []

    async def filter_tools_for_autonomous_execution(
        self, all_tools: List[Dict], user_request: str = None
    ) -> List[Dict]:
        """Filter tools for autonomous execution, removing ask_human when appropriate."""
        if not user_request:
            user_request = getattr(self.agent, "original_user_request", "")

        if not user_request:
            return all_tools

        # Get tool names for filtering
        tool_names = [tool["function"]["name"] for tool in all_tools]

        # Check if ask_human should be excluded
        if self.autonomous_capabilities.should_exclude_ask_human(
            user_request, tool_names
        ):
            # Filter out ask_human tool
            filtered_tools = [
                tool for tool in all_tools if tool["function"]["name"] != "ask_human"
            ]
            logger.info("🤖 Excluded ask_human tool for autonomous task execution")
            return filtered_tools

        return all_tools

    async def execute_tool_with_validation(self, command: ToolCall) -> Any:
        """Execute tool with validation and error handling."""
        try:
            # Log tool execution
            self._log_tool_execution(command)

            # Validate tool call format
            if not await self._validate_tool_call(command):
                return {"error": "Invalid tool call format"}

            # Extract tool name
            name = (
                command.function.name
                if hasattr(command, "function")
                else command.get("function", {}).get("name")
            )  # Check if available_tools is properly initialized
            if not self.agent.available_tools:
                logger.error("🚨 Available tools not initialized")
                return {"error": "Available tools not initialized"}

            if not name or name not in self.agent.available_tools.tool_map:
                logger.error(f"🚨 Tool '{name}' not found in available tools")
                return {"error": f"Tool '{name}' not found"}  # Debug logging
            logger.debug(
                f"🔍 Available tools: {list(self.agent.available_tools.tool_map.keys())}"
            )

            # Predict expected output files before execution
            expected_files = (
                await self.autonomous_capabilities.predict_expected_output_files(
                    command
                )
            )

            # Execute the tool
            tool_args = (
                command.function.arguments
                if hasattr(command, "function")
                else command.get("function", {}).get("arguments", {})
            )

            # Ensure tool_args is a dict and parse if it's a string
            if isinstance(tool_args, str):
                import json

                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}
            elif tool_args is None:
                tool_args = {}

            logger.debug(f"🔍 Executing tool: {name} with args: {tool_args}")

            # Verify the execute method exists and is callable
            if not hasattr(self.agent.available_tools, "execute"):
                logger.error("🚨 Available tools missing execute method")
                return {"error": "Available tools missing execute method"}

            result = await self.agent.available_tools.execute(
                name=name, tool_input=tool_args
            )

            # Check if result is None
            if result is None:
                logger.warning(f"⚠️ Tool '{name}' returned None result")
                result = {"warning": f"Tool '{name}' returned no result"}

            # Post-execution validation
            await self._post_execution_validation(command, result, expected_files)

            # Record successful execution
            self.execution_history.append(
                {
                    "tool": name,
                    "status": "success",
                    "result_type": type(result).__name__,
                }
            )

            return result

        except Exception as e:
            logger.error(f"🚨 Error executing tool: {e}")

            # Record failed execution
            self.execution_history.append(
                {
                    "tool": name if "name" in locals() else "unknown",
                    "status": "error",
                    "error": str(e),
                }
            )

            # Attempt autonomous error recovery
            recovery_result = (
                await self.autonomous_capabilities.detect_and_handle_error(
                    str(e),
                    {
                        "tool": name if "name" in locals() else "unknown",
                        "command": command,
                    },
                )
            )

            if recovery_result[0]:  # Recovery was successful
                logger.info("🔧 Autonomous error recovery applied")
                return {"recovered": True, "message": recovery_result[1]}

            raise

    def _log_tool_execution(self, command: ToolCall):
        """Log tool execution details."""
        if isinstance(command, dict):
            function_data = command.get("function", {})
            name = function_data.get("name", "unknown")
            arguments_str = function_data.get("arguments", "{}")
        else:
            name = command.function.name if hasattr(command, "function") else "unknown"
            arguments_str = (
                command.function.arguments if hasattr(command, "function") else "{}"
            )

        # Convert arguments to string if it's a dict
        if isinstance(arguments_str, dict):
            import json

            arguments_str = json.dumps(arguments_str, indent=2)

        logger.info(f"🔧 Executing tool: {name}")
        logger.debug(f"📋 Tool arguments: {arguments_str}")

    async def _validate_tool_call(self, command: ToolCall) -> bool:
        """Validate tool call format and structure."""
        try:
            if isinstance(command, dict):
                # Validate dict format
                if "function" not in command:
                    logger.error("🚨 Tool call missing 'function' key")
                    return False

                function_data = command["function"]
                if "name" not in function_data:
                    logger.error("🚨 Tool call function missing 'name'")
                    return False

                return True
            else:
                # Validate object format
                if not hasattr(command, "function"):
                    logger.error("🚨 Tool call missing 'function' attribute")
                    return False

                if not hasattr(command.function, "name"):
                    logger.error("🚨 Tool call function missing 'name' attribute")
                    return False

                return True

        except Exception as e:
            logger.error(f"🚨 Tool call validation failed: {e}")
            return False

    async def _post_execution_validation(
        self, command: ToolCall, result: Any, expected_files: List[str]
    ):
        """Validate tool execution results and expected outputs."""
        try:
            # Validate expected file outputs
            if expected_files:
                await self.autonomous_capabilities.validate_expected_files(
                    expected_files
                )

            # Additional result validation can be added here
            logger.debug(f"✅ Tool execution validation completed")

        except Exception as e:
            logger.warning(f"⚠️ Post-execution validation warning: {e}")

    async def cleanup(self):
        """Clean up tool manager resources."""
        self.execution_history.clear()
        logger.debug("🧹 Tool manager cleanup completed")

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        total = len(self.execution_history)
        successful = len(
            [h for h in self.execution_history if h["status"] == "success"]
        )
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": success_rate,
        }
