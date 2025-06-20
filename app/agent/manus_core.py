"""
Unified Manus Core Agent - Migrated to Use Unified Architecture
Clean, modular implementation using the unified BaseAgent with all capabilities.
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from app.agent.browser import BrowserContextHelper
from app.agent.core.base import AgentCapability, AgentConfig, BaseAgent
from app.agent.deliverable_verifier import DeliverableVerifier
from app.agent.manus_browser_handler import ManusBrowserHandler
from app.agent.manus_planning import ManusPlanning
from app.agent.manus_utils import ManusUtils
from app.agent.planning_coordinator import PlanningCoordinator
from app.agent.query_analyzer import QueryAnalyzer
from app.agent.smart_monitor import SmartAgentMonitor
from app.agent.step_executor import StepExecutor
from app.agent.todo_manager import TodoManager
from app.config import config
from app.exceptions import AgentTaskComplete, TokenLimitExceeded
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.reasoning import EnhancedReasoningEngine
from app.schema import (
    TOOL_CHOICE_TYPE,
    AgentState,
    Function,
    Message,
    ToolCall,
    ToolChoice,
)
from app.tool import Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute


class Manus(BaseAgent):
    """A versatile general-purpose agent with enhanced planning and reasoning capabilities."""  # Tool calling support

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            AskHuman(),
            Terminate(),
        )
    )

    tool_choices: str = ToolChoice.AUTO
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])
    tool_calls: List[ToolCall] = Field(default_factory=list)
    current_base64_image: Optional[str] = None  # Enhanced reasoning and planning
    reasoning_framework: EnhancedReasoningEngine = Field(
        default_factory=EnhancedReasoningEngine
    )
    current_plan: Optional[Dict] = None
    current_phase: int = 0
    todo_file_path: str = ""

    # Additional fields for components initialized in __init__
    memory_system: Optional[Any] = Field(default=None)
    optimization_mode: bool = Field(default=True)
    deep_reasoning_enabled: bool = Field(default=True)
    planning_module: Optional[Any] = Field(default=None)
    llm_planner: Optional[Any] = Field(default=None)
    browser_handler: Optional[Any] = Field(default=None)
    utils_module: Optional[Any] = Field(default=None)
    query_analyzer: Optional[Any] = Field(default=None)
    planning_coordinator: Optional[Any] = Field(default=None)
    step_executor: Optional[Any] = Field(default=None)
    todo_manager: Optional[Any] = Field(default=None)
    deliverable_verifier: Optional[Any] = Field(default=None)
    smart_monitor: Optional[Any] = Field(default=None)

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command

    # Add browser state tracking
    browser_state: Dict = Field(
        default_factory=lambda: {
            "current_url": None,
            "content_extracted": False,
            "analysis_complete": False,
            "screenshots_taken": False,
            "last_action": None,
            "page_ready": False,
            "structure_analyzed": False,
            "summary_complete": False,
        }
    )

    def __init__(self, **kwargs):
        # Set up unified configuration for Manus
        if "config" not in kwargs:
            kwargs["config"] = AgentConfig(
                name="Manus",
                description="A versatile agent that can solve various tasks using multiple tools with strategic planning",
                capabilities=[
                    AgentCapability.REASONING,
                    AgentCapability.PLANNING,
                    AgentCapability.BROWSING,
                    AgentCapability.CODING,
                    AgentCapability.SEARCH,
                    AgentCapability.TOOL_CALLING,
                    AgentCapability.MEMORY,
                    AgentCapability.WEB_SCRAPING,
                    AgentCapability.REPORT_GENERATION,
                    AgentCapability.TASK_AUTOMATION,
                    AgentCapability.INTERACTION,
                    AgentCapability.LEARNING,
                ],
                max_steps=config.max_steps,
                max_observe=config.max_observe,
                system_prompt=SYSTEM_PROMPT.format(directory=config.workspace_root),
                next_step_prompt=NEXT_STEP_PROMPT,
                memory_enabled=True,
                learning_enabled=True,
            )

        super().__init__(**kwargs)
        logger.debug("Manus __init__ started.")
        self.todo_file_path = os.path.join(
            config.workspace_root, "todo.md"
        )  # ENHANCED AI SYSTEM: Initialize reasoning and learning systems
        from app.enhanced_memory import EnhancedMemorySystem

        # Use the correct field name (reasoning_framework, not reasoning_engine)
        self.memory_system = EnhancedMemorySystem()
        self.optimization_mode = True
        self.deep_reasoning_enabled = True

        # Initialize modular components
        self.planning_module = ManusPlanning(self)
        self.llm_planner = None
        self.browser_handler = ManusBrowserHandler(self)
        self.utils_module = ManusUtils(self)

        # Initialize new modular components
        self.query_analyzer = QueryAnalyzer()
        self.planning_coordinator = PlanningCoordinator(self)
        self.step_executor = StepExecutor(self)
        self.todo_manager = TodoManager(self)
        self.deliverable_verifier = DeliverableVerifier()
        
        # Initialize smart monitoring for loop detection and recovery
        self.smart_monitor = SmartAgentMonitor(
            llm=self.llm, 
            workspace_path=config.workspace_root
        )

        logger.info(
            "🧠 ENHANCED AI SYSTEM INITIALIZED: Deep reasoning and learning enabled"
        )
        logger.debug("Manus __init__ completed.")

    def _ensure_llm_planner(self):
        """Ensure LLM planner is initialized with the current LLM."""
        self.planning_coordinator.ensure_llm_planner()

    @classmethod
    async def create(cls, **kwargs):
        """Asynchronous factory method to create a Manus instance."""
        logger.debug("Manus.create started.")
        try:
            instance = cls(**kwargs)
            logger.debug("Manus instance created.")
            # Any asynchronous initialization logic can go here if needed
            return instance
        except Exception as e:
            logger.error(f"Error during Manus.create: {e}", exc_info=True)
            raise

    async def create_task_plan(self, user_request: str) -> Dict:
        """Create comprehensive task plan using LLM-driven planner"""
        # Set LLM for query analyzer
        self.query_analyzer.llm = self.llm
        return await self.planning_coordinator.create_task_plan(
            user_request, self.query_analyzer
        )

    async def create_todo_list(self, plan: Dict) -> str:
        return await self.todo_manager.create_todo_list(plan)

    async def update_todo_progress(self):
        return await self.todo_manager.update_todo_progress()

    async def handle_browser_task(self, step: str) -> Optional[Dict]:
        return await self.browser_handler.handle_browser_task(step)

    async def _initialize_browser_state(self):
        return await self.browser_handler._initialize_browser_state()

    async def get_current_report_guidance(self) -> str:
        """Get guidance on what needs to be completed in the current report"""
        return await self.planning_coordinator.get_current_report_guidance()

    async def _extract_url_from_request(self, step: str) -> Optional[str]:
        return self.browser_handler._extract_url_from_request(step)

    async def think(self) -> bool:
        """Think about the next action based on the current plan phase and step with tool calling support"""
        try:
            await self._initialize_browser_state()

            # Add next step prompt for tool selection
            if self.config.next_step_prompt:
                user_msg = Message(role="user", content=self.config.next_step_prompt)
                self.messages.append(user_msg)

            # Get response with tool options
            try:
                # Prepare messages with system prompt if available
                messages_for_llm = []
                if self.config.system_prompt:
                    messages_for_llm.append(
                        {"role": "system", "content": self.config.system_prompt}
                    )

                # Convert Message objects to dicts and add to messages
                for msg in self.messages:
                    if hasattr(msg, "model_dump"):
                        messages_for_llm.append(msg.model_dump())
                    elif isinstance(msg, dict):
                        messages_for_llm.append(msg)
                    else:
                        messages_for_llm.append(
                            {"role": msg.role, "content": msg.content}
                        )

                response = await self.llm.ask_tool(
                    messages=messages_for_llm,
                    tools=self.available_tools.to_params(),
                    tool_choice=self.tool_choices,
                )
            except AgentTaskComplete as e:
                logger.info(f"🎉 Task completed successfully: {e.message}")
                self.state = AgentState.FINISHED
                raise
            except TokenLimitExceeded as e:
                logger.error(f"🚨 Token limit exceeded: {e}")
                self.state = AgentState.FINISHED
                return False
            except Exception as e:
                logger.error(f"Error in tool calling: {e}")
                raise

            # Extract tool calls from response
            self.tool_calls = tool_calls = (
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
                else (
                    response.content
                    if response and hasattr(response, "content")
                    else ""
                )
            )

            # Log response info
            logger.info(f"✨ {self.config.name}'s thoughts: {content}")
            logger.info(
                f"🛠️ {self.config.name} selected {len(tool_calls) if tool_calls else 0} tools to use"
            )  # Add assistant message to memory
            assistant_msg = (
                Message.from_tool_calls(content=content, tool_calls=self.tool_calls)
                if self.tool_calls
                else Message(role="assistant", content=content)
            )
            self.messages.append(assistant_msg)

            # Return True if we have tool calls or content
            return bool(self.tool_calls or content)

        except AgentTaskComplete:
            raise
        except Exception as e:
            logger.error(f"Error in think(): {str(e)}")
            return False

    async def act(self) -> str:
        """Execute tool calls or perform plan-based actions with smart monitoring"""
        try:
            # Determine the action description for monitoring
            if self.tool_calls:
                action_desc = f"execute_tools({len(self.tool_calls)} tools)"
            else:
                action_desc = "plan_based_action"
            
            # Monitor the action execution
            monitoring_result = await self.smart_monitor.monitor_action(action_desc)
            
            # Check if monitor detected issues and wants us to skip/modify action
            if monitoring_result.get("status") == "duplicate_prevention":
                logger.info(f"🔍 Smart Monitor: {monitoring_result.get('message')}")
                return monitoring_result.get("message", "Action prevented by smart monitor")
            elif monitoring_result.get("status") == "stuck_recovery":
                logger.info(f"🔍 Smart Monitor: Applied stuck state recovery")
                return monitoring_result.get("recovery", {}).get("message", "Recovery applied")
            
            # Execute the actual action
            if self.tool_calls:
                result = await self._execute_tool_calls()
            else:
                result = await self._execute_plan_based_action()
            
            return result

        except AgentTaskComplete:
            self.state = AgentState.FINISHED
            return "Task completed successfully"
        except Exception as e:
            logger.error(f"Error in act(): {str(e)}")
            return f"Error in action: {str(e)}"

    async def _execute_tool_calls(self) -> str:
        """Execute the selected tool calls"""
        if not self.tool_calls:
            return "No tools to execute"

        results = []
        for command in self.tool_calls:
            # Reset base64_image for each tool call
            self.current_base64_image = None

            result = await self._execute_single_tool(command)

            if self.config.max_observe:
                result = result[: self.config.max_observe]

            results.append(result)

            # Handle tool name extraction for logging
            if isinstance(command, dict) and "function" in command:
                tool_name = command["function"].get("name", "unknown")
                tool_id = command.get("id", "unknown")
            elif hasattr(command, "function") and hasattr(command.function, "name"):
                tool_name = command.function.name
                tool_id = getattr(command, "id", "unknown")
            else:
                tool_name = str(command)
                tool_id = "unknown"

            logger.info(
                f"🎯 Tool '{tool_name}' completed its mission! Result: {result}"
            )

            # Add tool response to memory
            tool_msg = Message(
                role="tool", content=result, tool_call_id=tool_id, name=tool_name
            )
            self.messages.append(tool_msg)

        return "\n\n".join(results)

    async def _execute_single_tool(self, command: ToolCall) -> str:
        """Execute a single tool call with robust error handling"""
        try:
            # Handle both dict and object formats
            if isinstance(command, dict):
                # Dict format from LLM response
                if "function" not in command or not command["function"]:
                    return "Error: Invalid command format"
                function_data = command["function"]
                name = function_data.get("name")
                arguments_str = function_data.get("arguments", "{}")
            elif (
                hasattr(command, "function")
                and command.function
                and command.function.name
            ):
                # Object format
                name = command.function.name
                arguments_str = command.function.arguments
            else:
                return "Error: Invalid command format"

            if not name or name not in self.available_tools.tool_map:
                return f"Error: Unknown tool '{name}'"

            try:
                arguments = json.loads(arguments_str) if arguments_str else {}

                # Execute the tool
                logger.info(f"🔧 Activating tool: '{name}'...")
                result = await self.available_tools.execute(
                    name=name, tool_input=arguments
                )

                # Handle special tools
                await self._handle_special_tool(name=name, result=result)

                # Check if result is a ToolResult with base64_image
                if hasattr(result, "base64_image") and result.base64_image:
                    self.current_base64_image = result.base64_image

                # For browser_use tool, return the ToolResult object directly
                # This preserves base64_image for vision integration
                if name == "browser_use" and hasattr(result, "base64_image"):
                    logger.info(f"🖼️ Returning ToolResult object for vision integration")
                    return result

                # Format result for display for other tools
                observation = (
                    f"Observed output of cmd `{name}` executed:\n{str(result)}"
                    if result
                    else f"Cmd `{name}` completed with no output"
                )

                return observation

            except json.JSONDecodeError:
                error_msg = f"Error parsing arguments for {name}: Invalid JSON format"
                logger.error(
                    f"📝 Invalid JSON arguments for '{name}': {command.function.arguments}"
                )
                return f"Error: {error_msg}"
            except AgentTaskComplete as e:
                # Propagate task completion signal
                logger.info(
                    f"🎉 Task completion signaled during tool execution: {e.message}"
                )
                raise
            except Exception as e:
                error_msg = f"⚠️ Tool '{name}' encountered a problem: {str(e)}"
                logger.exception(error_msg)
                return f"Error: {error_msg}"

        except Exception as e:
            logger.error(f"Error executing tool: {str(e)}")
            return f"Error: Invalid command format - {str(e)}"

    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """Handle special tool execution and state changes"""
        if not self._is_special_tool(name):
            return

        if self._should_finish_execution(name=name, result=result, **kwargs):
            # Set agent state to finished
            logger.info(f"🏁 Special tool '{name}' has completed the task!")
            self.state = AgentState.FINISHED

    def _is_special_tool(self, name: str) -> bool:
        """Check if tool name is in special tools list"""
        return name.lower() in [n.lower() for n in self.special_tool_names]

    @staticmethod
    def _should_finish_execution(**kwargs) -> bool:
        """Determine if tool execution should finish the agent"""
        return True

    async def _execute_plan_based_action(self) -> str:
        """Execute traditional plan-based actions when no tool calls are made"""
        # Validate and recover from invalid position
        if not await self.utils_module._validate_current_position():
            logger.warning("Invalid position detected, attempting recovery")

            # Ensure we have a valid plan
            if not self.current_plan or "phases" not in self.current_plan:
                logger.error("No valid plan exists")
                return "Error: No valid plan exists"

            # Fix phase index if out of bounds
            if self.current_phase >= len(self.current_plan["phases"]):
                self.current_phase = len(self.current_plan["phases"]) - 1
                logger.info(f"Reset phase to {self.current_phase}")

            # Fix step index if out of bounds
            current_phase = self.current_plan["phases"][self.current_phase]
            if "steps" in current_phase:
                if self.current_step >= len(current_phase["steps"]):
                    self.current_step = len(current_phase["steps"]) - 1
                    logger.info(f"Reset step to {self.current_step}")

                # If still invalid, reset to beginning of phase
                if self.current_step < 0:
                    self.current_step = 0
                    logger.info("Reset step to 0")
            else:
                self.current_step = 0
                logger.info("No steps in current phase, reset step to 0")

            # Validate again after recovery
            if not await self.utils_module._validate_current_position():
                logger.error("Recovery failed, position still invalid")
                return "Error: Failed to recover from invalid position"

            logger.info(
                f"Successfully recovered to phase {self.current_phase}, step {self.current_step}"
            )

        current_phase = await self.utils_module._get_current_phase()
        current_step = await self.utils_module._get_current_step()

        # This should never happen now due to validation, but keep as safety
        if not current_phase or not current_step or current_step == "phase_complete":
            if current_step == "phase_complete":
                logger.info("Phase completed, progressing to next phase")
                await self.utils_module.progress_to_next_phase()
                return "Phase completed, progressing to next phase"
            else:
                logger.error("No valid phase or step found in plan")
                return "Error: No valid phase or step found in plan"

        # Handle browser initialization if URL is detected
        url = await self._extract_url_from_request(current_step)
        if url:
            browser_init_needed = (
                await self.step_executor.handle_browser_initialization(url)
            )
            if browser_init_needed:
                return "Browser initialized for URL"

        # Execute the current step using the step executor
        step_result = await self.step_executor.execute_step(current_step)

        if step_result:
            # Step executed successfully, progress to next step
            logger.info(f"✅ Step '{current_step}' completed successfully")
            await self.utils_module.progress_to_next_step(verified=True)
            return "Step executed successfully and progressed to next step"
        else:
            logger.error(f"❌ Step '{current_step}' execution failed")
            return "Step execution failed"

    async def step(self) -> str:
        """Execute a single step, creating a plan if needed - overrides BaseAgent.step()"""
        if self.state == AgentState.FINISHED:
            return "Agent has finished execution"

        if self.current_step >= self.config.max_steps:
            self.state = AgentState.FINISHED
            return f"Maximum steps ({self.config.max_steps}) reached"

        try:
            self.current_step += 1

            # On first step, check for simple queries BEFORE creating complex plans
            if self.current_step == 1 and not self.current_plan:
                # Get the last user request from memory
                user_messages = [msg for msg in self.messages if msg.role == "user"]
                if not user_messages:
                    # Try from memory if available
                    if self.memory and hasattr(self.memory, "messages"):
                        user_messages = [
                            msg for msg in self.memory.messages if msg.role == "user"
                        ]

                if not user_messages:
                    return "Error: No user request found"

                request = user_messages[-1].content

                # Set LLM for query analyzer
                self.query_analyzer.llm = self.llm

                # Check if this is a simple query that can be handled directly
                is_simple = await self.query_analyzer.is_simple_query(request)
                if is_simple:
                    logger.info("🚀 Simple query detected - providing direct response")
                    response = await self.query_analyzer.handle_simple_query(request)
                    # Mark task as complete and return the response
                    self.state = AgentState.FINISHED
                    return f"Direct response: {response}"

                # If not simple, proceed with normal planning
                self.current_plan = await self.create_task_plan(request)
                await self.create_todo_list(self.current_plan)
                return "Created initial task plan"

            # Use unified BaseAgent step execution with think() and act()
            self.state = AgentState.THINKING

            # Think about next action
            should_continue = await self.think()

            if not should_continue:
                self.state = AgentState.FINISHED
                return "Agent decided to stop"

            # Execute action
            self.state = AgentState.ACTING
            result = await self.act()

            # Store result
            self.last_result = result
            self.execution_history.append(
                {"step": self.current_step, "timestamp": time.time(), "result": result}
            )

            # Check if finished
            if self.state != AgentState.FINISHED:
                self.state = AgentState.IDLE

            return result

        except AgentTaskComplete:
            # Task is complete - create final report if we have search results
            logger.info("🎯 Task completed - creating final deliverable report")
            try:
                if (
                    hasattr(self, "action_executor")
                    and self.action_executor.last_search_results
                ):
                    # Create final report with all collected data
                    await self.action_executor.execute_creation_action(
                        "Create final report with findings"
                    )
                    logger.info("✅ Final report created successfully")
                else:
                    logger.warning("⚠️ No search results available for final report")
            except Exception as e:
                logger.error(f"❌ Error creating final report: {e}")

            self.state = AgentState.FINISHED
            return "Task completed successfully"
        except Exception as e:
            logger.error(f"Error in step(): {str(e)}")
            self.state = AgentState.FINISHED
            return f"Error in step: {str(e)}"

    async def read_todo_goal(self) -> Optional[str]:
        """Read the goal from todo.md file."""
        return await self.todo_manager.read_todo_goal()

    async def auto_plan_from_todo(self) -> bool:
        """Automatically create a plan from todo.md goal and fill in empty steps."""
        return await self.todo_manager.auto_plan_from_todo()

    async def update_todo_with_steps(self, plan: Dict):
        """Update todo.md file with generated steps from the plan."""
        await self.todo_manager.update_todo_with_steps(plan)

    async def run(self, request: Optional[str] = None) -> str:
        """Enhanced run method that checks for todo.md auto-planning."""
        # If request is provided, add it to memory first
        if request:
            await self.add_user_message(request)

            # Check if this is a todo.md-related request
            if self.todo_manager.check_for_todo_request(request):
                # Try to auto-plan from todo.md
                auto_planned = await self.auto_plan_from_todo()
                if auto_planned:
                    logger.info("🎯 Successfully auto-generated plan from todo.md")
                    # Now proceed with normal execution

        # Call parent run method
        return await super().run()

    async def cleanup(self):
        """Clean up resources used by the agent's tools."""
        logger.info(f"🧹 Cleaning up resources for agent '{self.config.name}'...")
        for tool_name, tool_instance in self.available_tools.tool_map.items():
            if hasattr(tool_instance, "cleanup") and asyncio.iscoroutinefunction(
                tool_instance.cleanup
            ):
                try:
                    logger.debug(f"🧼 Cleaning up tool: {tool_name}")
                    await tool_instance.cleanup()
                except Exception as e:
                    logger.error(
                        f"🚨 Error cleaning up tool '{tool_name}': {e}", exc_info=True
                    )
        logger.info(f"✨ Cleanup complete for agent '{self.config.name}'.")

    def _should_exclude_ask_human(self, user_request: str, tools: List[str]) -> bool:
        """Determine if ask_human tool should be excluded for simple tasks"""
        if "ask_human" not in tools:
            return False
        
        request_lower = user_request.lower()
        
        # Simple file/report creation tasks - exclude ask_human
        simple_patterns = [
            "create a file",
            "write a file", 
            "save to file",
            "create a report",
            "write a report",
            "generate a report",
            "make a file",
            "output to file",
            "save as",
        ]
        
        for pattern in simple_patterns:
            if pattern in request_lower:
                logger.info(f"🚫 Excluding ask_human for simple task: {pattern}")
                return True
        
        # Complex tasks requiring human input - allow ask_human
        complex_patterns = [
            "what is your",
            "what are your", 
            "tell me about your",
            "what do you think",
            "your opinion",
            "your preference",
            "user preference",
            "favorite",
            "which do you prefer",
        ]
        
        for pattern in complex_patterns:
            if pattern in request_lower:
                logger.info(f"✅ Allowing ask_human for complex task: {pattern}")
                return False
        
        # Default: exclude for simple file operations, allow for others
        return "file" in request_lower or "report" in request_lower
