"""
Thinking Engine - Handles cognitive processes and decision making
Manages thinking, planning, tool selection, and response generation.
"""

from typing import Any, Dict, List, Optional

from app.agent.core.tool_manager import ToolManager
from app.exceptions import AgentTaskComplete, TokenLimitExceeded
from app.logger import logger
from app.schema import Message, ToolCall


class ThinkingEngine:
    """Handles the agent's cognitive processes and decision making."""

    def __init__(self, agent_instance, orchestrator):
        self.agent = agent_instance
        self.orchestrator = orchestrator
        self.tool_manager = ToolManager(agent_instance)
        self.thinking_history: List[Dict] = []

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
                messages_for_llm.append(
                    {"role": msg.role, "content": msg.content}
                )  # Get filtered tools for autonomous execution
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
        # Extract tool calls from response
        self.agent.tool_calls = tool_calls = (
            response.get("tool_calls")
            if response and isinstance(response, dict)
            else (
                response.tool_calls
                if response and hasattr(response, "tool_calls")
                else []
            )
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

        # Add assistant message to memory
        assistant_msg = (
            Message.from_tool_calls(content=content, tool_calls=self.agent.tool_calls)
            if self.agent.tool_calls
            else Message(role="assistant", content=content)
        )
        self.agent.messages.append(assistant_msg)

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

    async def cleanup(self):
        """Clean up thinking engine resources."""
        logger.debug("🧹 Cleaning up thinking engine")
        await self.tool_manager.cleanup()
        self.thinking_history.clear()
