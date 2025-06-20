"""
Tool Manager - Handles all tool-related operations
Manages tool execution, filtering, validation, and error handling.
"""

import json
from typing import Any, Dict, List, Optional

from app.agent.autonomous_capabilities import AutonomousCapabilities
from app.logger import logger
from app.schema import ToolCall
from app.tool import ToolCollection


class ToolManager:
    """Manages tool operations, filtering, and execution."""

    def __init__(self, agent_instance):
        self.agent = agent_instance
        self.autonomous_capabilities = AutonomousCapabilities()
        self.execution_history: List[Dict] = []

    async def filter_tools_for_autonomous_execution(
        self, available_tools: ToolCollection, user_request: str = None
    ) -> List[Dict]:
        """Filter tools based on autonomous execution requirements."""
        if not user_request:
            user_request = getattr(self.agent, "original_user_request", "")

        all_tools = available_tools.to_params()

        if not user_request:
            return all_tools

        # Get tool names for filtering
        tool_names = [tool["function"]["name"] for tool in all_tools]

        # Check if ask_human should be excluded for autonomous tasks
        if self.autonomous_capabilities.should_exclude_ask_human(
            user_request, tool_names
        ):
            # Filter out ask_human tool for autonomous operations
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

            # Execute the tool
            name = (
                command.function.name
                if hasattr(command, "function")
                else command.get("function", {}).get("name")
            )

            if not name or name not in self.agent.available_tools.tool_map:
                logger.error(f"🚨 Tool '{name}' not found in available tools")
                return {"error": f"Tool '{name}' not found"}

            # Predict expected output files before execution
            expected_files = (
                await self.autonomous_capabilities.predict_expected_output_files(
                    command
                )
            )

            # Execute the tool
            result = await self.agent.available_tools.execute(
                name,
                (
                    command.function.arguments
                    if hasattr(command, "function")
                    else command.get("function", {}).get("arguments", {})
                ),
            )

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
                str(command.function.arguments)
                if hasattr(command, "function")
                else "{}"
            )

        logger.debug(f"🔧 Executing tool: {name}")

        # Special logging for code execution
        if name == "python_execute":
            try:
                if isinstance(arguments_str, str):
                    args = json.loads(arguments_str)
                else:
                    args = arguments_str
                code = args.get("code", "")
                logger.debug(f"📝 Python code: {code[:100]}...")
            except Exception:
                pass

    async def _validate_tool_call(self, command: ToolCall) -> bool:
        """Validate tool call format and arguments."""
        try:
            if isinstance(command, dict):
                return "function" in command and "name" in command.get("function", {})
            else:
                return hasattr(command, "function") and hasattr(
                    command.function, "name"
                )
        except Exception:
            return False

    async def _post_execution_validation(
        self, command: ToolCall, result: Any, expected_files: List[str]
    ):
        """Validate execution results and check for expected outputs."""
        try:
            # Check if expected files were created
            if expected_files:
                missing_files = (
                    await self.autonomous_capabilities.verify_output_files_created(
                        expected_files
                    )
                )
                if missing_files:
                    logger.warning(f"⚠️ Expected files not created: {missing_files}")

            # Validate result format
            if result is None:
                logger.warning("⚠️ Tool execution returned None")
            elif isinstance(result, dict) and "error" in result:
                logger.warning(
                    f"⚠️ Tool execution returned error: {result.get('error')}"
                )

        except Exception as e:
            logger.debug(f"Post-execution validation error: {e}")

    def get_execution_stats(self) -> Dict:
        """Get tool execution statistics."""
        total_executions = len(self.execution_history)
        successful_executions = len(
            [h for h in self.execution_history if h["status"] == "success"]
        )
        failed_executions = total_executions - successful_executions

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": (
                successful_executions / total_executions if total_executions > 0 else 0
            ),
        }

    async def cleanup(self):
        """Clean up tool manager resources."""
        logger.debug("🧹 Cleaning up tool manager")
        self.execution_history.clear()
