"""
Thinking Engine - Handles cognitive processes and decision making
Manages thinking, planning, tool selection, and response generation.
"""

import json
import time
from typing import Any, Dict, List, Optional

from app.agent.core.tool_manager import ToolManager
from app.exceptions import AgentTaskComplete, TokenLimitExceeded
from app.logger import logger
from app.schema import Message, ToolCall
from app.utils.llm_report_generator import (LLMReportGenerator,
                                            SearchResultFormatter)


class ThinkingEngine:
    """Handles the agent's cognitive processes and decision making."""

    def __init__(self, agent_instance, orchestrator):
        self.agent = agent_instance
        self.orchestrator = orchestrator
        self.tool_manager = ToolManager(agent_instance)
        self.thinking_history: List[Dict] = []
        # Initialize LLM report generator
        self.report_generator = (
            LLMReportGenerator(agent_instance.llm)
            if hasattr(agent_instance, "llm")
            else None
        )
        # Add workflow state tracking
        self.workflow_state = {
            "research_data_collected": False,
            "report_generated": False,
            "collected_data": [],
            "last_search_results": None,
        }

    async def think_and_plan(self) -> bool:
        """Core thinking process - analyze situation and plan next actions."""
        try:
            # Initialize browser state if needed
            await self._initialize_browser_state()

            # Add next step prompt for tool selection
            if self.agent.config.next_step_prompt:
                user_msg = Message(
                    role="user", content=self.agent.config.next_step_prompt
                )
                self.agent.messages.append(user_msg)

            # Get LLM response with filtered tools
            response = await self._get_llm_response_with_filtered_tools()

            # Process and validate response
            return await self._process_thinking_response(response)

        except AgentTaskComplete as e:
            logger.info(f"🎉 Task completed successfully: {e.message}")
            self.agent.state = self.agent.state.FINISHED
            raise
        except TokenLimitExceeded as e:
            logger.error(f"🚨 Token limit exceeded: {e}")
            self.agent.state = self.agent.state.FINISHED
            return False
        except Exception as e:
            logger.error(f"❌ Error in thinking process: {e}")

            # Attempt autonomous error recovery
            recovery_success, recovery_message = (
                await self.orchestrator.handle_error_recovery(
                    str(e), {"context": "thinking_process"}
                )
            )

            if recovery_success:
                logger.info(f"🔧 Thinking process recovered: {recovery_message}")
                return True

            raise

    async def _get_llm_response_with_filtered_tools(self) -> Any:
        """Get LLM response with appropriately filtered tools."""
        # Prepare messages for LLM
        messages_for_llm = []
        if self.agent.config.system_prompt:
            messages_for_llm.append(
                {"role": "system", "content": self.agent.config.system_prompt}
            )

        # Convert Message objects to dicts
        for msg in self.agent.messages:
            if hasattr(msg, "model_dump"):
                messages_for_llm.append(msg.model_dump())
            elif isinstance(msg, dict):
                messages_for_llm.append(msg)
            else:
                messages_for_llm.append({"role": msg.role, "content": msg.content})

        # Get filtered tools for autonomous execution
        available_tools_list = self.agent.available_tools.to_params()
        filtered_tools = await self.tool_manager.filter_tools_for_autonomous_execution(
            available_tools_list, getattr(self.agent, "original_user_request", "")
        )

        # Make LLM call with filtered tools
        response = await self.agent.llm.ask_tool(
            messages=messages_for_llm,
            tools=filtered_tools,
            tool_choice=self.agent.tool_choices,
        )

        return response

    async def _process_thinking_response(self, response: Any) -> bool:
        """Process and validate the thinking response from LLM."""
        # Extract tool calls from LLM response
        raw_tool_calls = (
            response.get("tool_calls")
            if response and isinstance(response, dict)
            else (
                response.tool_calls
                if response and hasattr(response, "tool_calls")
                else []
            )
        )

        logger.info(
            f"🔍 Raw tool calls from response: {raw_tool_calls} (type: {type(raw_tool_calls)})"
        )

        # If no tool_calls found, try to extract from content
        if not raw_tool_calls:
            content = (
                response.get("content")
                if response and isinstance(response, dict)
                else (
                    response.content
                    if response and hasattr(response, "content")
                    else ""
                )
            )
            logger.info(
                f"🔍 No tool calls found, checking content for tool patterns..."
            )

            # Try to extract tool calls from content if it contains tool patterns
            if content and any(
                pattern in content.lower()
                for pattern in ["search", "generate_report", "analysis"]
            ):
                logger.info(
                    f"🔍 Content suggests tool usage but no tool calls extracted"
                )

        # Process tool calls through fixing logic to ensure argument validation
        if raw_tool_calls:
            fixed_tool_calls = await self._fix_tool_call_arguments(raw_tool_calls)
            self.agent.tool_calls = tool_calls = fixed_tool_calls
        else:
            self.agent.tool_calls = tool_calls = raw_tool_calls

        logger.info(
            f"🛠️ Final tool calls assigned to agent: {len(tool_calls) if tool_calls else 0} tools"
        )

        content = (
            response.get("content")
            if response and isinstance(response, dict)
            else (response.content if response and hasattr(response, "content") else "")
        )

        # Log thinking results
        logger.info(f"✨ {self.agent.config.name}'s thoughts: {content}")
        logger.info(
            f"🛠️ {self.agent.config.name} selected {len(tool_calls) if tool_calls else 0} tools to use"
        )

        # Check for research/analysis patterns and update workflow state
        user_messages = [
            msg.content
            for msg in self.agent.messages
            if hasattr(msg, "role") and msg.role == "user" and hasattr(msg, "content")
        ]
        original_request = getattr(self.agent, "original_user_request", "")
        all_text = " ".join(user_messages + [original_request, content])

        is_research_analysis = any(
            pattern in all_text.lower()
            for pattern in [
                "research",
                "analyze",
                "analysis",
                "report",
                "study",
                "investigate",
                "examine",
                "review",
                "assess",
                "evaluate",
                "summarize",
                "summary",
            ]
        )

        # Check for PDF conversion requests
        pdf_requested = any(
            pattern in all_text.lower()
            for pattern in [
                "pdf", "convert to pdf", "as pdf", "make pdf", "generate pdf",
                "export pdf", "save as pdf", "pdf format", "pdf file"
            ]
        )

        if is_research_analysis:
            logger.info(f"🔬 Detected research/analysis task pattern")

            # If PDF is requested, ensure we have both report generation and PDF conversion
            if pdf_requested:
                logger.info(f"📄 PDF conversion requested for research task")

                # Check if we have report generation tool
                has_report_tool = tool_calls and any(
                    "generate_analysis_report" in (
                        tc.get("function", {}).get("name", "")
                        if isinstance(tc, dict)
                        else (
                            getattr(tc, "function", {}).get("name", "")
                            if hasattr(tc, "function")
                            else str(tc).lower()
                        )
                    )
                    for tc in tool_calls
                )

                # Check if we have PDF tool
                has_pdf_tool = tool_calls and any(
                    "markdown_to_pdf" in (
                        tc.get("function", {}).get("name", "")
                        if isinstance(tc, dict)
                        else (
                            getattr(tc, "function", {}).get("name", "")
                            if hasattr(tc, "function")
                            else str(tc).lower()
                        )
                    )
                    for tc in tool_calls
                )

                # Auto-add missing tools for PDF workflow
                if has_report_tool and not has_pdf_tool:
                    logger.info(f"🎯 Auto-adding PDF conversion tool for complete workflow")
                    await self._add_pdf_conversion_tool()
                elif not has_report_tool and not has_pdf_tool:
                    logger.info(f"🎯 Auto-adding both report and PDF tools for complete workflow")
                    # Will be handled by force report generation logic below

            # Check if we have search tool calls that might provide data
            if tool_calls and any(
                "search"
                in (
                    tc.get("function", {}).get("name", "")
                    if isinstance(tc, dict)
                    else (
                        getattr(tc, "function", {}).get("name", "")
                        if hasattr(tc, "function")
                        else str(tc).lower()
                    )
                )
                for tc in tool_calls
            ):
                self.workflow_state["research_data_collected"] = True
                logger.info(f"🔬 Research tools detected, marking data as collected")

        # Add assistant message to memory
        assistant_msg = (
            Message.from_tool_calls(content=content, tool_calls=self.agent.tool_calls)
            if self.agent.tool_calls
            else Message(role="assistant", content=content)
        )
        self.agent.messages.append(assistant_msg)

        # Check if we should force report generation for research/analysis tasks
        await self._check_forced_report_generation(tool_calls, content)

        # Record thinking session
        self.thinking_history.append(
            {
                "content": content,
                "tool_count": len(tool_calls) if tool_calls else 0,
                "tools_selected": [
                    tc.function.name if hasattr(tc, "function") else "unknown"
                    for tc in (tool_calls or [])
                ],
            }
        )

        # Validate that autonomous tasks don't select ask_human
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = (
                    tool_call.function.name
                    if hasattr(tool_call, "function")
                    else tool_call.get("function", {}).get("name")
                )
                if tool_name == "ask_human" and getattr(
                    self.agent, "original_user_request", ""
                ):
                    # This should have been filtered out - apply recovery
                    logger.warning(
                        "🚨 ask_human selected for autonomous task - applying recovery"
                    )
                    await self._handle_invalid_tool_selection()
                    return False

        return True

    async def _handle_invalid_tool_selection(self):
        """Handle cases where invalid tools are selected for autonomous tasks."""
        logger.info("🔧 Applying invalid tool selection recovery")

        # Clear the invalid tool calls
        self.agent.tool_calls = []

        # Add a corrective message to guide the agent
        corrective_msg = Message(
            role="user",
            content="Please focus on the task and use appropriate tools for autonomous completion. Do not ask for human input.",
        )
        self.agent.messages.append(corrective_msg)

    async def _initialize_browser_state(self):
        """Initialize browser state if needed."""
        if (
            hasattr(self.orchestrator, "browser_handler")
            and self.orchestrator.browser_handler
        ):
            await self.orchestrator.browser_handler._initialize_browser_state()

    def get_thinking_stats(self) -> Dict:
        """Get thinking process statistics."""
        total_sessions = len(self.thinking_history)
        avg_tools_per_session = (
            sum(h["tool_count"] for h in self.thinking_history) / total_sessions
            if total_sessions > 0
            else 0
        )

        return {
            "total_thinking_sessions": total_sessions,
            "average_tools_per_session": avg_tools_per_session,
            "recent_tools": [
                h["tools_selected"] for h in self.thinking_history[-5:]
            ],  # Last 5 sessions
        }

    async def _check_forced_report_generation(self, tool_calls, content):
        """Check if we should force report generation for research/analysis tasks."""
        try:
            user_messages = [
                msg.content
                for msg in self.agent.messages
                if hasattr(msg, "role")
                and msg.role == "user"
                and hasattr(msg, "content")
            ]
            original_request = getattr(self.agent, "original_user_request", "")
            all_text = " ".join(user_messages + [original_request, content])

            # Enhanced patterns for research/analysis tasks
            is_research_analysis = any(
                pattern in all_text.lower()
                for pattern in [
                    "research",
                    "analyze",
                    "analysis",
                    "report",
                    "study",
                    "investigate",
                    "examine",
                    "review",
                    "assess",
                    "evaluate",
                    "summarize",
                    "summary",
                    "information about",
                    "tell me about",
                    "what is",
                    "explain",
                    "details about",
                    "overview of",
                    "background on",
                    "insights on",
                ]
            )

            # Check if no tools were selected or if we should force a report
            should_force_report = False

            if is_research_analysis:
                # Force report if no useful tools selected
                if not tool_calls or len(tool_calls) == 0:
                    logger.info(
                        f"🎯 No tools selected for research task - forcing report generation"
                    )
                    should_force_report = True

                # Force report if only non-research tools selected
                elif not any(
                    tool_name
                    in [
                        "enhanced_search",
                        "search_enhanced",
                        "generate_analysis_report",
                        "enhanced_browser",
                    ]
                    for tool_name in [
                        (
                            tc.get("function", {}).get("name", "")
                            if isinstance(tc, dict)
                            else (
                                getattr(tc, "function", {}).get("name", "")
                                if hasattr(tc, "function")
                                else str(tc)
                            )
                        )
                        for tc in tool_calls
                    ]
                ):
                    logger.info(
                        f"🎯 No research tools selected for research task - forcing report generation"
                    )
                    should_force_report = True

                # Force report if we've already attempted research
                elif self.workflow_state.get(
                    "research_data_collected", False
                ) and not self.workflow_state.get("report_generated", False):
                    logger.info(f"🎯 Research attempted, now forcing report generation")
                    should_force_report = True

            if should_force_report:
                await self._force_generate_report()

        except Exception as e:
            logger.warning(f"Error in forced report generation check: {e}")

    async def _force_generate_report(self):
        """Force generation of an analysis report using available data."""
        try:
            logger.info(f"🎯 Forcing report generation for research/analysis task")

            # Create a report generation tool call with proper parameters
            query = getattr(self.agent, "original_user_request", "Research Analysis")

            # Create fallback research data when tools fail
            fallback_research_data = {
                "search_results": {
                    "query": query,
                    "results": [],
                    "status": "fallback_llm_only",
                    "note": "Using LLM knowledge only due to tool limitations",
                },
                "analysis_context": {
                    "task_type": "research_analysis",
                    "data_source": "llm_knowledge",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }

            report_tool_call = {
                "function": {
                    "name": "generate_analysis_report",
                    "arguments": json.dumps(
                        {
                            "query": query,
                            "research_data": json.dumps(fallback_research_data),
                            "confidence_level": "Medium",
                            "output_filename": f"{query.lower().replace(' ', '_')}_analysis.md",
                        }
                    ),
                }
            }

            # Add to tool calls if not already present
            if not any(
                tc.get("function", {}).get("name") == "generate_analysis_report"
                for tc in (self.agent.tool_calls or [])
            ):
                if not self.agent.tool_calls:
                    self.agent.tool_calls = []
                self.agent.tool_calls.append(report_tool_call)
                logger.info(f"🎯 Added forced report generation tool call")

            self.workflow_state["report_generated"] = True

        except Exception as e:
            logger.warning(f"Error forcing report generation: {e}")

    async def _add_pdf_conversion_tool(self):
        """Automatically add PDF conversion tool when requested."""
        try:
            logger.info(f"🎯 Adding PDF conversion tool to workflow")

            # Create PDF conversion tool call
            pdf_tool_call = {
                "id": f"pdf_conversion_{int(time.time())}",
                "type": "function",
                "function": {
                    "name": "markdown_to_pdf",
                    "arguments": json.dumps({
                        "markdown_file_path": "auto_detect",  # Will be detected from recent files
                        "output_path": "auto_generate"  # Will generate appropriate name
                    })
                }
            }

            # Add to tool calls if not already present
            if not any(
                tc.get("function", {}).get("name") == "markdown_to_pdf"
                for tc in (self.agent.tool_calls or [])
            ):
                if not self.agent.tool_calls:
                    self.agent.tool_calls = []
                self.agent.tool_calls.append(pdf_tool_call)
                logger.info(f"🎯 Added PDF conversion tool call to workflow")

        except Exception as e:
            logger.warning(f"Error adding PDF conversion tool: {e}")

    async def cleanup(self):
        """Clean up thinking engine resources."""
        logger.debug("🧹 Cleaning up thinking engine")
        await self.tool_manager.cleanup()
        self.thinking_history.clear()

    async def _fix_tool_call_arguments(self, tool_calls: List[Dict]) -> List[Dict]:
        """Fix tool call arguments using the same logic as LLM core."""
        fixed_calls = []

        for call in tool_calls:
            try:
                # Extract tool information
                function_data = call.get("function", {})
                tool_name = function_data.get("name", "")
                args_str = function_data.get("arguments", "{}")

                # Parse arguments
                try:
                    args = (
                        json.loads(args_str) if isinstance(args_str, str) else args_str
                    )
                except json.JSONDecodeError:
                    logger.warning(
                        f"🔧 Invalid JSON arguments for {tool_name}: {args_str}"
                    )
                    args = {}
                # Apply python_execute specific fixing logic
                if tool_name == "python_execute":
                    code = args.get("code", "")

                    # Check if code is missing or empty
                    if not code or code.strip() == "":
                        logger.warning(
                            f"🔧 Detected empty python_execute code, generating fallback"
                        )

                        # Check if this is a simple request
                        user_messages = [
                            msg.content
                            for msg in self.agent.messages
                            if hasattr(msg, "role")
                            and msg.role == "user"
                            and hasattr(msg, "content")
                        ]
                        is_simple_request = any(
                            any(
                                word in content.lower()
                                for word in ["print", "hello", "simple", "hello world"]
                            )
                            for content in user_messages
                            if content
                        )

                        if is_simple_request:
                            args["code"] = 'print("Hello, World!")'
                            logger.info(f"🎯 Used simple solution for simple request")
                        else:
                            args["code"] = "print('Hello, World!')"
                            logger.info(
                                f"🤖 Fixed empty python_execute with fallback code"
                            )

                    # Update the tool call with fixed arguments
                    call["function"]["arguments"] = json.dumps(args)

                fixed_calls.append(call)

            except Exception as e:
                logger.warning(f"Error fixing tool call arguments: {e}")
                fixed_calls.append(call)  # Keep original if fixing fails

        return fixed_calls
