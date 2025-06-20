"""
Agent Orchestrator - Coordinates all modular components
Handles initialization, coordination, and lifecycle management of agent modules.
"""

import asyncio
from typing import Any, Dict, List, Optional

from app.agent.autonomous_capabilities import AutonomousCapabilities
from app.agent.browser import BrowserContextHelper
from app.agent.deliverable_verifier import DeliverableVerifier
from app.agent.enhanced_error_recovery import EnhancedErrorRecovery
from app.agent.manus_browser_handler import ManusBrowserHandler
from app.agent.manus_planning import ManusPlanning
from app.agent.manus_utils import ManusUtils
from app.agent.planning_coordinator import PlanningCoordinator
from app.agent.query_analyzer import QueryAnalyzer
from app.agent.smart_monitor import SmartAgentMonitor
from app.agent.step_executor import StepExecutor
from app.agent.task_simplifier import TaskSimplifier
from app.agent.todo_manager import TodoManager
from app.config import config
from app.logger import logger
from app.reasoning import EnhancedReasoningEngine
from app.tool.mcp import MCPClients


class AgentOrchestrator:
    """Orchestrates all agent modules and handles their coordination."""

    def __init__(self, agent_instance):
        self.agent = agent_instance
        self._modules_initialized = False

        # Core modules
        self.autonomous_capabilities = AutonomousCapabilities()
        self.task_simplifier = TaskSimplifier()
        self.reasoning_engine = EnhancedReasoningEngine()

        # Coordination modules
        self.query_analyzer = None
        self.planning_coordinator = None
        self.step_executor = None
        self.todo_manager = None
        self.deliverable_verifier = None
        self.smart_monitor = None

        # Specialized modules
        self.browser_handler = None
        self.utils_module = None
        self.error_recovery = None
        self.mcp_clients = MCPClients()

        # State tracking
        self.browser_context_helper = None
        self.connected_servers = {}

    async def initialize_modules(self):
        """Initialize all modular components."""
        if self._modules_initialized:
            return

        logger.info("🔧 Initializing agent modules...")

        try:
            # Initialize core coordination modules (pass agent where needed)
            self.query_analyzer = QueryAnalyzer()
            self.planning_coordinator = PlanningCoordinator(self.agent)
            self.step_executor = StepExecutor(self.agent)
            self.todo_manager = TodoManager(self.agent)
            self.deliverable_verifier = DeliverableVerifier()
            self.smart_monitor = SmartAgentMonitor(
                llm=self.agent.llm,
                workspace_path=getattr(config, "workspace_root", "workspace"),
            )

            # Initialize specialized modules (pass agent where needed)
            self.browser_handler = ManusBrowserHandler(self.agent)
            self.utils_module = ManusUtils(self.agent)
            self.error_recovery = EnhancedErrorRecovery()
            self.browser_context_helper = BrowserContextHelper(self.agent)

            # Initialize enhanced systems
            from app.enhanced_memory import EnhancedMemorySystem

            self.agent.memory_system = EnhancedMemorySystem()

            self._modules_initialized = True
            logger.info("✅ All agent modules initialized successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing modules: {e}")
            raise

    async def process_user_request(self, request: str) -> str:
        """Process user request through modular pipeline."""
        # Store original request for autonomous filtering
        self.agent.original_user_request = request

        # Apply intelligent task simplification
        simplified_request = await self.task_simplifier.apply_smart_task_simplification(
            request
        )
        if simplified_request != request:
            logger.info(f"🎯 Auto-simplified request: {simplified_request}")
            request = simplified_request

        return request

    async def create_execution_plan(self, user_request: str) -> Dict:
        """Create task execution plan using modular planning."""
        return await self.planning_coordinator.create_task_plan(
            user_request, self.query_analyzer
        )

    async def filter_tools_for_request(self, tools, user_request: str = None) -> list:
        """Filter available tools based on request context."""
        if not user_request:
            user_request = getattr(self.agent, "original_user_request", "")

        if not user_request:
            return tools.to_params()

        # Get tool names for filtering
        tool_names = [tool["function"]["name"] for tool in tools.to_params()]

        # Check if ask_human should be excluded
        if self.autonomous_capabilities.should_exclude_ask_human(
            user_request, tool_names
        ):
            # Filter out ask_human tool
            filtered_tools = [
                tool
                for tool in tools.to_params()
                if tool["function"]["name"] != "ask_human"
            ]
            logger.info("🤖 Excluded ask_human tool for autonomous task")
            return filtered_tools

        return tools.to_params()

    async def validate_task_completion(self, original_request: str) -> bool:
        """Validate task completion using modular capabilities."""
        return await self.autonomous_capabilities.validate_task_completion()

    async def handle_error_recovery(
        self, error_message: str, context: Dict = None
    ) -> tuple:
        """Handle error recovery through modular system."""
        return await self.autonomous_capabilities.detect_and_handle_error(
            error_message, context
        )

    async def monitor_execution(self, step_result: Any) -> Any:
        """Monitor execution and apply recovery if needed."""
        return await self.smart_monitor.monitor_action(step_result)

    async def cleanup_modules(self):
        """Clean up all modules."""
        logger.info("🧹 Cleaning up agent modules...")

        cleanup_tasks = []

        # Cleanup modules that have cleanup methods
        modules_to_cleanup = [
            self.browser_handler,
            self.smart_monitor,
            self.browser_context_helper,
        ]

        for module in modules_to_cleanup:
            if module and hasattr(module, "cleanup"):
                cleanup_tasks.append(module.cleanup())

        # Handle MCP clients separately (has disconnect method)
        if self.mcp_clients:
            cleanup_tasks.append(self.mcp_clients.disconnect())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        logger.info("✅ Module cleanup complete")

    # Delegation methods for common operations
    async def create_todo_list(self, plan: Dict) -> str:
        """Delegate to todo manager."""
        return await self.todo_manager.create_todo_list(plan)

    async def update_todo_progress(self):
        """Delegate to todo manager."""
        return await self.todo_manager.update_todo_progress()

    async def handle_browser_task(self, step: str) -> Optional[Dict]:
        """Delegate to browser handler."""
        return await self.browser_handler.handle_browser_task(step)

    async def get_current_report_guidance(self) -> str:
        """Delegate to planning coordinator."""
        return await self.planning_coordinator.get_current_report_guidance()

    def check_for_todo_request(self, request: str) -> bool:
        """Delegate to todo manager."""
        return self.todo_manager.check_for_todo_request(request)

    async def auto_plan_from_todo(self) -> bool:
        """Delegate to todo manager."""
        return await self.todo_manager.auto_plan_from_todo()
