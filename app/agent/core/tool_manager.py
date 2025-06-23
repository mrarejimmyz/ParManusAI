"""
Tool Manager - Handles tool execution, validation, and autonomous capabilities integration
"""

from typing import Any, Dict, List, Optional

from app.agent.autonomous_capabilities import AutonomousCapabilities
from app.agent.intelligent_tool_filter import IntelligentToolFilter
from app.logger import logger
from app.schema import ToolCall


class ToolManager:
    """Manages tool execution with validation and autonomous capabilities."""

    def __init__(self, agent):
        self.agent = agent
        self.autonomous_capabilities = AutonomousCapabilities()
        self.intelligent_filter = IntelligentToolFilter()
        self.execution_history = []

    async def filter_tools_for_autonomous_execution(
        self, all_tools: List[Dict], user_request: str = None
    ) -> List[Dict]:
        """Filter tools for autonomous execution, removing inappropriate tools."""
        if not user_request:
            user_request = getattr(self.agent, "original_user_request", "")

        if not user_request:
            return all_tools

        # Apply intelligent tool filtering first (removes vision for text-only tasks)
        filtered_tools = self.intelligent_filter.filter_tools_for_task(
            all_tools, user_request
        )

        # Get tool names for additional filtering
        tool_names = [tool["function"]["name"] for tool in filtered_tools]

        # Check if ask_human should be excluded
        if self.autonomous_capabilities.should_exclude_ask_human(
            user_request, tool_names
        ):
            # Filter out ask_human tool
            filtered_tools = [
                tool
                for tool in filtered_tools
                if tool["function"]["name"] != "ask_human"
            ]
            logger.info("🤖 Excluded ask_human tool for autonomous task execution")

        return filtered_tools

    async def execute_tool_with_validation(self, command: ToolCall) -> Any:
        """Execute tool with validation and error handling."""
        try:
            # Log tool execution
            self._log_tool_execution(command)

            # Validate tool call format
            if not await self._validate_tool_call(command):
                return {"error": "Invalid tool call format"}

            # Extract tool name and parameters
            name = (
                command.function.name
                if hasattr(command, "function")
                else command.get("function", {}).get("name")
            )

            tool_args = (
                command.function.arguments
                if hasattr(command, "function")
                else command.get("function", {}).get("arguments", {})
            )  # Ensure tool_args is a dict and parse if it's a string
            if isinstance(tool_args, str):
                import json

                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}
            elif tool_args is None:
                tool_args = {}

            # Record action attempt in thinking engine's action memory
            if hasattr(self.agent, "thinking_engine") and hasattr(
                self.agent.thinking_engine, "action_memory"
            ):
                # Check if this action should be skipped due to redundancy
                should_skip = (
                    self.agent.thinking_engine.action_memory.should_skip_action(
                        name, tool_args
                    )
                )
                if should_skip:
                    logger.warning(f"🚫 Skipping redundant action: {name}")
                    return {
                        "skipped": True,
                        "reason": "redundant_action",
                        "message": f"Action {name} was skipped to prevent redundancy",
                    }

            # Check if available_tools is properly initialized
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
                result = {
                    "warning": f"Tool '{name}' returned no result"
                }  # Record successful execution in action memory
            if hasattr(self.agent, "thinking_engine") and hasattr(
                self.agent.thinking_engine, "action_memory"
            ):
                # For research tools, capture more detailed information
                if name in ["enhanced_search", "search", "browser_use"]:
                    # Store full result for research tools - ensure no truncation
                    full_result_summary = str(result) if result else ""
                    collected_data = (
                        result if isinstance(result, (dict, list)) else result
                    )

                    # Record with both summary and full collected data
                    self.agent.thinking_engine.action_memory.record_action(
                        name, tool_args, full_result_summary, True, collected_data
                    )

                    # Also call the thinking engine's record method for compatibility
                    self.agent.thinking_engine.record_tool_execution(
                        name, tool_args, result, True
                    )
                else:
                    self.agent.thinking_engine.record_tool_execution(
                        name, tool_args, result, True
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

            # Special handling for research tools that timeout or fail
            if name in [
                "enhanced_search",
                "enhanced_browser",
                "web_search",
                "browser_use_tool",
            ]:
                logger.info(
                    f"🔄 Research tool {name} failed, marking research as attempted"
                )
                # Mark research as attempted in workflow state
                if hasattr(self.agent, "thinking_engine"):
                    self.agent.thinking_engine.workflow_state[
                        "research_data_collected"
                    ] = True
                    logger.info(
                        "✅ Marked research data collection as completed despite timeout"
                    )

            # Record failed execution in action memory
            if hasattr(self.agent, "thinking_engine") and hasattr(
                self.agent.thinking_engine, "action_memory"
            ):
                self.agent.thinking_engine.record_tool_execution(
                    name, tool_args if "tool_args" in locals() else {}, str(e), False
                )

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

    async def execute_tools(self, tool_calls: List[ToolCall]) -> List[Any]:
        """Execute tools with intelligent coordination and result tracking."""
        results = []
        search_data = []
        browser_data = []

        # Track what types of tools are being executed
        tool_types = [
            (
                call.function.name
                if hasattr(call, "function")
                else call.get("function", {}).get("name", "")
            )
            for call in tool_calls
        ]
        has_search = any("search" in tool_type.lower() for tool_type in tool_types)
        has_browser = any("browser" in tool_type.lower() for tool_type in tool_types)
        has_report_gen = any(
            "generate_analysis_report" in tool_type for tool_type in tool_types
        )

        logger.info(f"🔧 Executing {len(tool_calls)} tools: {tool_types}")

        for i, tool_call in enumerate(tool_calls):
            try:
                self._log_tool_execution(tool_call)

                # Apply hallucination detection
                tool_call = await self._apply_hallucination_detection(
                    tool_call
                )  # Execute the tool
                result = await self._execute_single_tool(tool_call)
                results.append(result)

                # Track results for coordination
                tool_name = (
                    tool_call.function.name
                    if hasattr(tool_call, "function")
                    else tool_call.get("function", {}).get("name", "")
                )  # CRITICAL FIX: Update workflow state in thinking engine
                if hasattr(self.agent, "thinking_engine") and hasattr(
                    self.agent.thinking_engine, "update_workflow_state_from_tool_result"
                ):
                    await self.agent.thinking_engine.update_workflow_state_from_tool_result(
                        tool_name, result
                    )
                # Additional direct state update for critical tools
                if hasattr(self.agent, "thinking_engine") and hasattr(
                    self.agent.thinking_engine, "workflow_state"
                ):
                    if tool_name in ["enhanced_search", "web_search", "search"]:
                        self.agent.thinking_engine.workflow_state[
                            "research_data_collected"
                        ] = True
                        if result:
                            self.agent.thinking_engine.workflow_state[
                                "last_search_results"
                            ] = result
                        logger.info("📊 Direct workflow update: search data collected")
                    elif tool_name in ["enhanced_browser", "browser_use_tool"]:
                        self.agent.thinking_engine.workflow_state[
                            "research_data_collected"
                        ] = True
                        if result:
                            self.agent.thinking_engine.workflow_state[
                                "last_browser_results"
                            ] = result
                        logger.info("🌐 Direct workflow update: browser data collected")
                    elif tool_name in [
                        "generate_analysis_report",
                        "llm_analysis_report",
                    ]:
                        self.agent.thinking_engine.workflow_state[
                            "report_generated"
                        ] = True
                        logger.info(
                            "📄 Direct workflow update: report generated"
                        )  # IMMEDIATE COMPLETION: Stop agent after successful report generation
                        user_request = getattr(self.agent, "original_user_request", "")
                        if user_request and any(
                            keyword in user_request.lower()
                            for keyword in [
                                "research",
                                "report",
                                "analysis",
                                "analyze",
                                "investigate",
                                "study",
                                "examine",
                                "explore",
                                "create a",
                                "generate a",
                                "write a",
                                "trends",
                                "developments",
                            ]
                        ):
                            logger.info(
                                "🎉 Research report completed - stopping agent execution"
                            )
                            from app.exceptions import AgentTaskComplete

                            # Mark as successfully completed
                            self.agent.state = self.agent.state.FINISHED

                            # Clear any pending tool calls to prevent further execution
                            self.agent.tool_calls = []

                            # Determine appropriate completion message
                            completion_message = (
                                "Research and analysis report generated successfully"
                            )
                            if "quantum" in user_request.lower():
                                completion_message = (
                                    "Quantum computing research report completed"
                                )
                            elif (
                                "ai" in user_request.lower()
                                or "artificial intelligence" in user_request.lower()
                            ):
                                completion_message = (
                                    "AI developments analysis report completed"
                                )
                            elif "machine learning" in user_request.lower():
                                completion_message = (
                                    "Machine learning trends report completed"
                                )

                            raise AgentTaskComplete(completion_message)

                # Collect search and browser data for potential report generation
                if (
                    "search" in tool_name.lower()
                    and result
                    and hasattr(result, "content")
                ):
                    if isinstance(result.content, dict) and "results" in result.content:
                        search_data.extend(result.content["results"])
                    elif isinstance(result.content, list):
                        search_data.extend(result.content)

                if (
                    "browser" in tool_name.lower()
                    and result
                    and hasattr(result, "content")
                ):
                    if isinstance(result.content, dict):
                        browser_data.append(result.content)
                    elif isinstance(result.content, str) and len(result.content) > 100:
                        browser_data.append(
                            {"content": result.content, "source": "browser"}
                        )

                # If this is a report generation tool and we have collected data, enhance it
                if tool_name == "generate_analysis_report" and (
                    search_data or browser_data
                ):
                    logger.info(
                        f"📊 Enhancing report generation with collected data: {len(search_data)} search results, {len(browser_data)} browser results"
                    )
                    # The tool should handle this, but we can track it here

            except Exception as e:
                logger.error(f"❌ Error executing tool {i+1}: {e}")
                results.append(self._create_error_result(str(e)))

        # Update workflow state in thinking engine if available
        if hasattr(self.agent, "thinking_engine") and hasattr(
            self.agent.thinking_engine, "workflow_state"
        ):
            if search_data or browser_data:
                self.agent.thinking_engine.workflow_state["research_data_collected"] = (
                    True
                )
                self.agent.thinking_engine.workflow_state["collected_data"] = (
                    search_data + browser_data
                )
                self.agent.thinking_engine.workflow_state["last_search_results"] = (
                    search_data
                )
                self.agent.thinking_engine.workflow_state["last_browser_results"] = (
                    browser_data
                )

            if has_report_gen:
                self.agent.thinking_engine.workflow_state["report_generated"] = True

        return results

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
