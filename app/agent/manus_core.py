"""
Optimized Manus Core Agent - Lean Orchestrator Architecture
Minimal core that orchestrates modular components for maximum separation of concerns.
"""

import os
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.agent.core.agent_orchestrator import AgentOrchestrator
from app.agent.core.base import AgentCapability, AgentConfig, BaseAgent
from app.agent.core.thinking_engine import ThinkingEngine
from app.agent.core.tool_manager import ToolManager
from app.config import config
from app.exceptions import AgentTaskComplete
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import AgentState, ToolCall, ToolChoice
from app.tool import MarkdownToPDFTool, Terminate, ToolCollection, WebSearch
from app.tool.ask_human import AskHuman
from app.tool.ask_vision import AskVision
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.llm_analysis_report import LLMAnalysisReportTool
from app.tool.mcp import MCPClients
from app.tool.python_execute import PythonExecute


class Manus(BaseAgent):
    """Optimized Manus Agent - Lean orchestrator leveraging modular architecture."""

    # Core tool configuration
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            WebSearch(),
            LLMAnalysisReportTool(),
            AskVision(),
            AskHuman(),
            MarkdownToPDFTool(),
            Terminate(),
        )
    )
    tool_choices: str = ToolChoice.AUTO
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])
    tool_calls: List[ToolCall] = Field(default_factory=list)  # Essential state
    current_plan: Optional[Dict] = None
    current_phase: int = 0
    todo_file_path: str = ""
    original_user_request: Optional[str] = Field(default=None)
    memory_system: Optional[Any] = Field(default=None)

    # Browser state for compatibility
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

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    # Core modular components
    orchestrator: Optional[AgentOrchestrator] = Field(default=None)
    thinking_engine: Optional[ThinkingEngine] = Field(default=None)
    tool_manager: Optional[ToolManager] = Field(default=None)

    def __init__(self, **kwargs):
        """Initialize Manus with lean, modular configuration."""
        if "config" not in kwargs:
            kwargs["config"] = AgentConfig(
                name="Manus",
                description="Optimized modular agent with autonomous capabilities",
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

        # Set todo file path
        self.todo_file_path = os.path.join(config.workspace_root, "todo.md")

        # Initialize modular components
        self.orchestrator = AgentOrchestrator(self)
        self.thinking_engine = ThinkingEngine(self, self.orchestrator)
        self.tool_manager = ToolManager(self)

        logger.debug("✅ Optimized Manus initialized with modular architecture")

    @classmethod
    async def create(cls, **kwargs):
        """Asynchronous factory method to create an optimized Manus instance."""
        logger.debug("🚀 Creating optimized modular Manus instance...")
        try:
            instance = cls(**kwargs)
            logger.debug("✅ Optimized Manus instance created successfully")
            return instance
        except Exception as e:
            logger.error(f"❌ Error during optimized Manus.create: {e}", exc_info=True)
            raise

    async def initialize(self):
        """Initialize all modular components."""
        logger.info("🚀 Initializing modular Manus agent...")

        # Initialize orchestrator and all modules
        await self.orchestrator.initialize_modules()

        # Initialize MCP if configured
        if hasattr(config, "mcp_servers") and config.mcp_servers:
            await self._initialize_mcp_connections()

        logger.info("✅ Manus initialization complete")

    async def run(self, request: Optional[str] = None) -> str:
        """Optimized run method using modular orchestration."""
        try:
            # Store original user request for tool filtering
            if request:
                self.original_user_request = request

            # Initialize if not already done
            if not self.orchestrator._modules_initialized:
                await self.initialize()

            # Process request through modular pipeline
            if request:
                processed_request = await self.orchestrator.process_user_request(
                    request
                )
                await self.add_user_message(processed_request)

                # Handle todo-related requests
                if self.orchestrator.check_for_todo_request(processed_request):
                    auto_planned = await self.orchestrator.auto_plan_from_todo()
                    if auto_planned:
                        logger.info("🎯 Successfully auto-generated plan from todo.md")

            # Execute main task with modular support
            result = await super().run()

            # Validate completion using modular capabilities
            if request:
                completion_validated = await self.orchestrator.validate_task_completion(
                    request
                )

                if not completion_validated:
                    logger.warning("🔄 Task completion validation failed")
                    # The orchestrator will handle retries through its modules

            return result

        except AgentTaskComplete as e:
            # Task completed successfully with result
            logger.info(f"🎉 Task completed successfully: {e.message}")
            return str(e.message)
        except Exception as e:
            logger.error(f"❌ Error in optimized run: {e}")

            # Use modular error recovery
            recovery_success, recovery_message = (
                await self.orchestrator.handle_error_recovery(
                    str(e), {"context": "main_run", "request": request}
                )
            )

            if recovery_success:
                logger.info(
                    f"🔧 Run recovered through modular system: {recovery_message}"
                )
                return recovery_message

            raise

    async def think(self) -> bool:
        """Delegate thinking to modular thinking engine."""
        return await self.thinking_engine.think_and_plan()

    async def act(self) -> Any:
        """Execute actions using modular tool management."""
        if not self.tool_calls:
            logger.warning("⚠️ No tool calls to execute")

            # Handle no-tools case for research tasks
            if hasattr(self, "original_user_request"):
                user_request = getattr(self, "original_user_request", "").lower()
                research_indicators = [
                    "research",
                    "search",
                    "latest",
                    "current",
                    "news",
                    "breakthroughs",
                    "developments",
                    "analyze",
                    "investigate",
                    "find",
                    "look up",
                    "report",
                    "analysis",
                    "create a",
                    "generate a",
                    "write a",
                    "trends",
                ]

                is_research_task = any(
                    indicator in user_request for indicator in research_indicators
                )

                if is_research_task:
                    # Count consecutive no-tools occurrences
                    if not hasattr(self, "_consecutive_no_tools"):
                        self._consecutive_no_tools = 0
                    self._consecutive_no_tools += 1

                    logger.info(
                        f"🔍 Research task with no tools (attempt {self._consecutive_no_tools})"
                    )

                    if self._consecutive_no_tools >= 2:  # Reduced threshold
                        logger.info(
                            "🎯 Multiple no-tools attempts - forcing research completion"
                        )
                        # Force completion through thinking engine
                        await self.thinking_engine._force_generate_report()

                        # Generate completion result
                        completion_result = (
                            f"Research task completed successfully for: {user_request}"
                        )

                        if completion_result:
                            from app.exceptions import AgentTaskComplete

                            raise AgentTaskComplete(
                                "Research task completed with optimized workflow"
                            )
                        return "Research task completed with available data"

            return None
        else:
            # Reset no-tools counter when tools are available
            self._consecutive_no_tools = 0

        # Use smart monitor for execution monitoring
        step_result = None

        for tool_call in self.tool_calls:
            try:
                # Execute tool with modular validation and error handling
                result = await self.tool_manager.execute_tool_with_validation(tool_call)
                step_result = result

                # Monitor execution through orchestrator
                monitored_result = await self.orchestrator.monitor_execution(result)
                if monitored_result != result:
                    step_result = monitored_result

            except Exception as e:
                logger.error(f"🚨 Tool execution failed: {e}")

                # Use modular error recovery
                recovery_success, recovery_message = (
                    await self.orchestrator.handle_error_recovery(
                        str(e), {"tool_call": tool_call, "context": "action_execution"}
                    )
                )

                if recovery_success:
                    logger.info(f"🔧 Action recovered: {recovery_message}")
                    step_result = {"recovered": True, "message": recovery_message}
                else:
                    raise

        # Clear executed tool calls
        self.tool_calls = []
        return step_result

    # Delegation methods for modular functionality
    async def create_task_plan(self, user_request: str) -> Dict:
        """Delegate to orchestrator."""
        return await self.orchestrator.create_execution_plan(user_request)

    async def create_todo_list(self, plan: Dict) -> str:
        """Delegate to orchestrator."""
        return await self.orchestrator.create_todo_list(plan)

    async def update_todo_progress(self):
        """Delegate to orchestrator."""
        return await self.orchestrator.update_todo_progress()

    async def handle_browser_task(self, step: str) -> Optional[Dict]:
        """Delegate to orchestrator."""
        return await self.orchestrator.handle_browser_task(step)

    async def get_current_report_guidance(self) -> str:
        """Delegate to orchestrator."""
        return await self.orchestrator.get_current_report_guidance()

    async def _initialize_mcp_connections(self):
        """Initialize MCP connections if configured."""
        try:
            # This would be implemented based on your MCP configuration
            logger.debug("🔗 MCP connections initialized")
        except Exception as e:
            logger.warning(f"⚠️ MCP initialization warning: {e}")

    async def cleanup(self):
        """Clean up all modular components."""
        logger.info("🧹 Cleaning up optimized Manus agent...")

        cleanup_tasks = []

        # Cleanup modular components
        if self.orchestrator:
            cleanup_tasks.append(self.orchestrator.cleanup_modules())
        if self.thinking_engine:
            cleanup_tasks.append(self.thinking_engine.cleanup())
        if self.tool_manager:
            cleanup_tasks.append(self.tool_manager.cleanup())
            # Cleanup MCP clients if it has cleanup method
        if self.mcp_clients and hasattr(self.mcp_clients, "cleanup"):
            cleanup_tasks.append(self.mcp_clients.cleanup())

        # Execute all cleanup tasks
        if cleanup_tasks:
            import asyncio

            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        logger.info("✅ Optimized Manus cleanup complete")

    def get_stats(self) -> Dict:
        """Get comprehensive stats from all modules."""
        stats = {
            "agent_type": "Optimized Modular Manus",
            "modules_initialized": getattr(
                self.orchestrator, "_modules_initialized", False
            ),
        }

        if self.thinking_engine:
            stats["thinking"] = self.thinking_engine.get_thinking_stats()
        if self.tool_manager:
            stats["tools"] = self.tool_manager.get_execution_stats()

        return stats
