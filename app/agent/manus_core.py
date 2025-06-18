import asyncio
import json
import os
import time
from typing import Dict, List, Optional

from pydantic import Field, model_validator

from app.agent.browser import BrowserContextHelper
from app.agent.manus_browser_handler import ManusBrowserHandler
from app.agent.manus_planning import ManusPlanning
from app.agent.manus_utils import ManusUtils
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.exceptions import AgentTaskComplete
from app.llm_planning import LLMDrivenPlanner
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.reasoning import EnhancedReasoningEngine
from app.schema import AgentState, Function, Message, ToolCall
from app.tool import Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute


class Manus(ToolCallAgent):
    """A versatile general-purpose agent with enhanced planning and reasoning capabilities."""

    name: str = "Manus"
    description: str = (
        "A versatile agent that can solve various tasks using multiple tools with strategic planning"
    )

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = config.max_observe
    max_steps: int = config.max_steps

    # Enhanced reasoning and planning
    reasoning_framework: EnhancedReasoningEngine = Field(
        default_factory=EnhancedReasoningEngine
    )
    current_plan: Optional[Dict] = None
    current_phase: int = 0
    current_step: int = 0
    todo_file_path: str = ""

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    # Add general-purpose tools to the tool collection
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            AskHuman(),
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command

    # Add browser state tracking (renamed from _browser_state to browser_state)
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
        super().__init__(**kwargs)
        logger.debug("Manus __init__ started.")
        self.todo_file_path = os.path.join(config.workspace_root, "todo.md")

        # ENHANCED AI SYSTEM: Initialize reasoning and learning systems
        from app.enhanced_memory import EnhancedMemorySystem
        from app.reasoning import EnhancedReasoningEngine

        self.reasoning_engine = EnhancedReasoningEngine()
        self.memory_system = EnhancedMemorySystem()
        self.optimization_mode = True
        self.deep_reasoning_enabled = True

        self.planning_module = ManusPlanning(self)
        # Initialize LLM planner without LLM for now - will be set later
        self.llm_planner = None
        self.browser_handler = ManusBrowserHandler(self)
        self.utils_module = ManusUtils(self)

        logger.info(
            "🧠 ENHANCED AI SYSTEM INITIALIZED: Deep reasoning and learning enabled"
        )
        logger.debug("Manus __init__ completed.")

    def _ensure_llm_planner(self):
        """Ensure LLM planner is initialized with the current LLM."""
        if self.llm_planner is None and self.llm is not None:
            self.llm_planner = LLMDrivenPlanner(llm=self.llm)

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

    async def _is_simple_query(self, user_request: str) -> bool:
        """Detect if this is a simple query that doesn't need complex planning."""
        simple_patterns = [
            # Mathematical questions
            r"\b\d+\s*[\+\-\*\/]\s*\d+",
            r"what\s+is\s+\d+",
            r"calculate",
            r"math",
            # Simple factual questions
            r"^what\s+is\s+(?:your\s+)?name",
            r"^who\s+are\s+you",
            r"^what\s+can\s+you\s+do",
            r"^hello",
            r"^hi\b",
            # Quick recommendations that can be answered from knowledge
            r"^name\s+\d+\s+\w+\s+to\s+(?:invest|buy|use)",
            r"^recommend\s+(?:a|one|\d+)",
            r"^suggest\s+(?:a|one|\d+)",
            r"^what\s+(?:is\s+)?(?:the\s+)?best\s+\w+",
            # Simple explanations
            r"^explain\s+\w+\s+in\s+\w+\s+words",
            r"^define\s+\w+",
            r"^what\s+does\s+\w+\s+mean",
        ]

        import re

        request_lower = user_request.lower().strip()

        for pattern in simple_patterns:
            if re.search(pattern, request_lower):
                return True

        # Use LLM to determine if this is a simple query
        try:
            prompt = f"""Is this user request a simple query that can be answered quickly (within 1-2 minutes) with a brief response?

Consider it simple if it's:
- A basic factual question
- A quick lookup or definition
- A short "what/who/when/where/how/why" question
- Something that doesn't require detailed research or complex analysis

User request: "{user_request}"

Respond with only "yes" or "no"."""

            response = await self.llm.ask(prompt)
            is_simple = response.strip().lower() == "yes"

            if is_simple:
                logger.info("🔍 LLM determined this is a simple query")
                return True
            else:
                logger.info(
                    "🔍 LLM determined this is a complex query requiring detailed analysis"
                )
                return False

        except Exception as e:
            logger.warning(f"LLM simple query detection failed: {e}")
            # Fallback to simple heuristics
            return self._fallback_is_simple_query(user_request)

    def _fallback_is_simple_query(self, user_request: str) -> bool:
        """Fallback simple query detection using basic heuristics."""
        request_lower = user_request.lower()

        # Check for short queries (likely simple)
        if len(request_lower.split()) <= 6:
            simple_keywords = [
                "what",
                "who",
                "when",
                "where",
                "how",
                "why",
                "is",
                "are",
                "can",
                "do",
                "does",
            ]
            if any(request_lower.startswith(kw) for kw in simple_keywords):
                return True

        return False

    async def _handle_simple_query(self, user_request: str) -> str:
        """Handle simple queries directly with LLM without complex planning."""
        logger.info(f"🚀 Handling simple query directly: {user_request}")

        # Ensure LLM is available
        if not self.llm:
            return "I need an LLM to answer your question."

        # Create a focused prompt for simple queries
        simple_prompt = f"""You are Manus, a helpful AI assistant. The user has asked a simple, direct question that needs a clear, concise answer.

User question: {user_request}

Please provide a direct, helpful answer. If this is asking for a recommendation (like crypto to invest), provide ONE specific recommendation with a brief reason why. Keep your response concise and actionable.

If you cannot provide a specific recommendation due to lack of current market data, clearly state this limitation and provide general guidance instead."""

        try:
            response = await self.llm.ask([{"role": "user", "content": simple_prompt}])
            return response
        except Exception as e:
            logger.error(f"Error in simple query handling: {e}")
            return f"I encountered an error while processing your question: {str(e)}"

    async def create_task_plan(self, user_request: str) -> Dict:
        """Create comprehensive task plan using LLM-driven planner"""
        logger.info(f"🎯 Creating LLM-driven comprehensive plan for: {user_request}")

        # Ensure LLM planner is initialized
        self._ensure_llm_planner()

        if self.llm_planner is None:
            logger.warning("LLM planner not available, using legacy planning only")
            return await self.planning_module.create_task_plan(user_request)

        # Check if it's a simple query that can be handled directly
        is_simple = await self._is_simple_query(user_request)
        if is_simple:
            logger.info("Detected simple query, handling directly without planning")
            response = await self._handle_simple_query(user_request)
            return {
                "phases": [
                    {
                        "steps": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "respond",
                                    "arguments": {"response": response},
                                },
                            }
                        ]
                    }
                ]
            }

        # Use the new LLM-driven planner for all requests
        plan = await self.llm_planner.create_comprehensive_plan(user_request)

        # Also create legacy plan for compatibility
        legacy_plan = await self.planning_module.create_task_plan(user_request)

        # Merge the plans (LLM plan takes priority)
        if plan:
            plan["legacy_phases"] = legacy_plan.get("phases", [])
            return plan
        else:
            return legacy_plan

    async def create_todo_list(self, plan: Dict) -> str:
        return await self.planning_module.create_todo_list(plan)

    async def update_todo_progress(self):
        return await self.planning_module.update_todo_progress()

    async def handle_browser_task(self, step: str) -> Optional[Dict]:
        return await self.browser_handler.handle_browser_task(step)

    async def _initialize_browser_state(self):
        return await self.browser_handler._initialize_browser_state()

    async def get_current_report_guidance(self) -> str:
        """Get guidance on what needs to be completed in the current report"""
        try:
            if not hasattr(self, "action_executor"):
                return "No active action executor"

            status = self.action_executor.get_current_report_status()

            if "error" in status:
                return f"Report status error: {status['error']}"

            completion_pct = status.get("completion_percentage", 0)
            completed_sections = status.get("completed_sections", 0)
            total_sections = status.get("total_sections", 0)
            missing_sections = status.get("missing_sections", [])
            placeholder_sections = status.get("placeholder_sections", [])

            guidance = f"Current report is {completion_pct:.1f}% complete ({completed_sections}/{total_sections} sections).\n"

            if placeholder_sections:
                guidance += f"Priority: Replace placeholders in {', '.join(placeholder_sections[:3])}\n"

            if missing_sections:
                guidance += f"Still needed: {', '.join(missing_sections[:3])}\n"

            if completion_pct < 50:
                guidance += "Focus on Executive Summary and Key Findings first."

            return guidance

        except Exception as e:
            logger.error(f"Error getting report guidance: {e}")
            return "Could not get report guidance"

    async def _verify_deliverable_creation(self, current_step: str) -> bool:
        """
        Verify that the deliverable for the current step was actually created
        """
        try:
            # Check if a new file was created in the workspace
            workspace_path = os.path.join(os.getcwd(), "workspace")
            if not os.path.exists(workspace_path):
                logger.warning("Workspace directory does not exist")
                return False

            # Get list of files in workspace
            current_files = []
            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    current_files.append(os.path.join(root, file))

            # Check if any files were created recently (within last 60 seconds)
            import time

            current_time = time.time()
            recent_files = []

            for filepath in current_files:
                try:
                    # Check file modification time
                    mtime = os.path.getmtime(filepath)
                    if current_time - mtime < 60:  # Created within last 60 seconds
                        recent_files.append(filepath)
                except OSError:
                    continue

            if recent_files:
                logger.info(
                    f"✅ Found {len(recent_files)} recently created deliverable(s): {[os.path.basename(f) for f in recent_files]}"
                )

                # Additional verification: check if files contain substantial content
                for filepath in recent_files:
                    try:
                        if filepath.endswith(".md"):
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read()
                                if len(content) > 500:  # Substantial content
                                    logger.info(
                                        f"✅ Verified substantial content in {os.path.basename(filepath)} ({len(content)} characters)"
                                    )
                                    return True
                                else:
                                    logger.warning(
                                        f"⚠️ File {os.path.basename(filepath)} has insufficient content ({len(content)} characters)"
                                    )
                    except Exception as e:
                        logger.warning(f"Could not verify content of {filepath}: {e}")
                        continue

                # If we have recent files but couldn't verify content, still consider it a success
                if recent_files:
                    return True

            logger.warning("⚠️ No recent deliverables found in workspace")
            return False

        except Exception as e:
            logger.error(f"Error verifying deliverable creation: {e}")
            return False

    async def _extract_url_from_request(self, step: str) -> Optional[str]:
        return self.browser_handler._extract_url_from_request(step)

    async def think(self) -> bool:
        """Think about the next action based on the current plan phase and step"""
        try:
            await self._initialize_browser_state()

            # Validate and recover from invalid position
            if not await self.utils_module._validate_current_position():
                logger.warning("Invalid position detected, attempting recovery")

                # Ensure we have a valid plan
                if not self.current_plan or "phases" not in self.current_plan:
                    logger.error("No valid plan exists")
                    return False

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
                    return False

                logger.info(
                    f"Successfully recovered to phase {self.current_phase}, step {self.current_step}"
                )

            current_phase = await self.utils_module._get_current_phase()
            current_step = await self.utils_module._get_current_step()

            # This should never happen now due to validation, but keep as safety
            if (
                not current_phase
                or not current_step
                or current_step == "phase_complete"
            ):
                if current_step == "phase_complete":
                    logger.info("Phase completed, progressing to next phase")
                    await self.utils_module.progress_to_next_phase()
                    return True
                else:
                    logger.error("No valid phase or step found in plan")
                    return False

            url = await self._extract_url_from_request(current_step)
            if url:
                if not self.browser_state.get("initialized"):
                    browser_args = {"action": "initialize", "url": url}
                    func = Function(
                        name="browser_use", arguments=json.dumps(browser_args)
                    )
                    self.tool_calls = [
                        ToolCall(
                            id="browser_init_" + str(int(time.time())),
                            type="function",
                            function=func,
                        )
                    ]
                    return True

            # Handle different types of steps with actual tool execution
            step_lower = current_step.lower()

            # Initialize action executor if not already done
            if not hasattr(self, "action_executor"):
                from app.agent.actions import (
                    SimplifiedManusActionExecutor as ManusActionExecutor,
                )

                self.action_executor = ManusActionExecutor(self)

            # Research and planning steps - navigate to relevant websites
            if any(
                keyword in step_lower
                for keyword in ["research", "plan", "identify", "sources"]
            ):
                logger.info(f"Executing research action for: {current_step}")
                action_success = await self.action_executor.execute_research_action(
                    current_step
                )
                if action_success:
                    success = await self.utils_module.progress_to_next_step(
                        verified=True
                    )
                    return True
                else:
                    logger.warning(f"Research action failed for step: {current_step}")
                    # For research, we can proceed but mark as unverified
                    await self.utils_module.progress_to_next_step(verified=False)
                    return True  # Continue execution

            # Data extraction steps - scrape and collect information
            elif any(
                keyword in step_lower
                for keyword in ["extract", "headlines", "gather", "collect", "visit"]
            ):
                logger.info(f"Executing data extraction for: {current_step}")
                action_success = await self.action_executor.execute_extraction_action(
                    current_step
                )
                if action_success:
                    success = await self.utils_module.progress_to_next_step(
                        verified=True
                    )
                    return True
                else:
                    logger.warning(f"Extraction action failed for step: {current_step}")
                    # For extraction, we can proceed but mark as unverified
                    await self.utils_module.progress_to_next_step(verified=False)
                    return True  # Continue execution

            # Verification steps - check multiple sources
            elif any(
                keyword in step_lower
                for keyword in ["verify", "check", "multiple sources", "confirm"]
            ):
                logger.info(f"Executing verification action for: {current_step}")
                action_success = await self.action_executor.execute_verification_action(
                    current_step
                )
                if action_success:
                    success = await self.utils_module.progress_to_next_step(
                        verified=True
                    )
                    return True
                else:
                    logger.warning(
                        f"Verification action failed for step: {current_step}"
                    )
                    # For verification, we can proceed but mark as unverified
                    await self.utils_module.progress_to_next_step(verified=False)
                    return True  # Continue execution

            # File creation steps - generate reports and documents
            elif any(
                keyword in step_lower
                for keyword in [
                    "generate",
                    "create",
                    "format",
                    "output",
                    ".md",
                    "write",
                    "report",
                ]
            ):
                logger.info(f"Executing file creation for: {current_step}")
                action_success = await self.action_executor.execute_creation_action(
                    current_step
                )
                if action_success:
                    # For creation actions, also verify the deliverable was actually created
                    deliverable_verified = await self._verify_deliverable_creation(
                        current_step
                    )
                    if deliverable_verified:
                        # Update report completion status after creation
                        self.action_executor.update_report_completion()
                        success = await self.utils_module.progress_to_next_step(
                            verified=True
                        )
                        return True
                    else:
                        logger.warning(
                            f"Creation action completed but deliverable not verified for step: {current_step}"
                        )
                        # Creation step must be verified to proceed
                        return False  # Do not progress, retry this step
                else:
                    logger.warning(f"Creation action failed for step: {current_step}")
                    # Creation failure is critical - do not progress
                    return False  # Do not progress, retry this step

            # Navigation steps (legacy support)
            elif "navigate" in step_lower or "Navigate to website" in current_step:
                logger.info(f"Executing navigation for: {current_step}")
                action_success = await self.action_executor.execute_navigation_action(
                    current_step
                )
                if action_success:
                    success = await self.utils_module.progress_to_next_step(
                        verified=True
                    )
                    return True
                else:
                    logger.warning(f"Navigation action failed for step: {current_step}")
                    # For navigation, we can proceed but mark as unverified
                    await self.utils_module.progress_to_next_step(verified=False)
                    return True  # Continue execution

            # Default case - try to determine action from context
            else:
                logger.info(f"Executing default action for: {current_step}")
                action_success = await self.action_executor.execute_default_action(
                    current_step
                )
                if action_success:
                    success = await self.utils_module.progress_to_next_step(
                        verified=True
                    )
                    return True
                else:
                    logger.warning(f"Default action failed for step: {current_step}")
                    # For default actions, we can proceed but mark as unverified
                    await self.utils_module.progress_to_next_step(verified=False)
                    return True  # Continue execution

        except AgentTaskComplete:
            raise
        except Exception as e:
            logger.error(f"Error in think(): {str(e)}")
            return False

    async def step(self) -> str:
        """Execute a single step, creating a plan if needed"""
        try:
            # On first step, check for simple queries BEFORE creating complex plans
            if self.current_step == 1 and not self.current_plan:
                # Get the last user request from memory
                user_messages = [
                    msg for msg in self.memory.messages if msg.role == "user"
                ]
                if not user_messages:
                    raise ValueError("No user request found in memory")

                request = user_messages[-1].content

                # Check if this is a simple query that can be handled directly
                is_simple = await self._is_simple_query(request)
                if is_simple:
                    logger.info("🚀 Simple query detected - providing direct response")
                    response = await self._handle_simple_query(request)
                    # Mark task as complete and return the response
                    self.state = AgentState.FINISHED
                    return f"Direct response: {response}"

                # If not simple, proceed with normal planning
                self.current_plan = await self.create_task_plan(request)
                await self.create_todo_list(self.current_plan)
                return "Created initial task plan"

            # Validate position before proceeding
            if not await self.utils_module._validate_current_position():
                logger.warning(
                    "Invalid position detected in step(), attempting recovery"
                )
                # Attempt recovery using the recovery method
                recovery_success = (
                    await self.utils_module.recover_from_invalid_position()
                )
                if not recovery_success:
                    logger.error("Failed to recover from invalid position")
                    return "Error: Unable to recover from invalid position"
                logger.info("Successfully recovered from invalid position")

            # Synchronize with base framework step tracking
            await self.utils_module.sync_with_base_framework()

            # For subsequent steps, use think() to determine and take actions
            success = await self.think()
            if success:
                return "Thinking complete - no action needed..."
            else:
                logger.error("Think failed")
                return "Error during think phase"

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
            return f"Error in step: {str(e)}"

    async def read_todo_goal(self) -> Optional[str]:
        """Read the goal from todo.md file."""
        try:
            if os.path.exists(self.todo_file_path):
                with open(self.todo_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract goal from todo.md
                import re

                goal_match = re.search(r"\*\*Goal:\*\*\s*(.+)", content)
                if goal_match:
                    goal = goal_match.group(1).strip()
                    logger.info(f"📋 Found goal in todo.md: {goal}")
                    return goal
        except Exception as e:
            logger.error(f"Error reading todo.md: {e}")

        return None

    async def auto_plan_from_todo(self) -> bool:
        """Automatically create a plan from todo.md goal and fill in empty steps."""
        goal = await self.read_todo_goal()
        if not goal:
            return False

        try:
            # Check if todo.md has empty steps sections
            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            import re

            empty_steps = re.findall(r"\*\*Steps:\*\*\s*$", content, re.MULTILINE)

            if len(empty_steps) > 0:
                logger.info(
                    "🤖 Auto-generating action plan for empty steps sections..."
                )

                # Create a comprehensive plan
                if self.llm_planner is None:
                    self._ensure_llm_planner()

                if self.llm_planner:
                    plan = await self.llm_planner.create_comprehensive_plan(goal)
                    self.current_plan = plan

                    # Update todo.md with generated steps
                    await self.update_todo_with_steps(plan)
                    return True

        except Exception as e:
            logger.error(f"Error auto-planning from todo: {e}")

        return False

    async def update_todo_with_steps(self, plan: Dict):
        """Update todo.md file with generated steps from the plan."""
        try:
            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Generate steps for each phase
            for i, phase in enumerate(plan.get("phases", [])):
                phase_num = i + 1
                steps_text = "\n".join([f"- {step}" for step in phase.get("steps", [])])

                # Replace empty steps section for this phase
                import re

                pattern = f"(## Phase {phase_num}:.*?\\*\\*Steps:\\*\\*\\s*)"
                replacement = f"\\g<1>\n{steps_text}"
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)

            # Write updated content back
            with open(self.todo_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("✅ Updated todo.md with generated action steps")

        except Exception as e:
            logger.error(f"Error updating todo.md: {e}")

    async def run(self, request: Optional[str] = None) -> str:
        """Enhanced run method that checks for todo.md auto-planning."""
        # If request is provided, add it to memory first
        if request:
            self.update_memory("user", request)

            # Check if this is a todo.md-related request
            if "todo.md" in request.lower() or "work on the todo" in request.lower():
                # Try to auto-plan from todo.md
                auto_planned = await self.auto_plan_from_todo()
                if auto_planned:
                    logger.info("🎯 Successfully auto-generated plan from todo.md")
                    # Now proceed with normal execution

        # Call parent run method without arguments (BaseAgent.run() doesn't accept parameters)
        return await super().run()
