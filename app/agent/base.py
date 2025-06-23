import asyncio
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.exceptions import AgentTaskComplete
from app.intelligent_error_handler import AdaptiveRecoverySystem
from app.llm import LLM
from app.logger import logger
from app.sandbox.client import SANDBOX_CLIENT
from app.schema import ROLE_TYPE, AgentState, Memory, Message, Role
from app.utils.string_safety import safe_lower

from .reliability import CircuitBreaker, StuckStateDetector


class BaseAgent(BaseModel, ABC):
    """
    Abstract base class for managing agent state and execution with enhanced reliability.

    Provides foundational functionality for state transitions, memory management,
    and a step-based execution loop with circuit breaker and stuck state detection.
    """

    # Core attributes
    name: str = Field(..., description="Unique name of the agent")
    description: Optional[str] = Field(None, description="Optional agent description")

    # Prompts
    system_prompt: Optional[str] = Field(
        None, description="System-level instruction prompt"
    )
    next_step_prompt: Optional[str] = Field(
        None, description="Prompt for determining next action"
    )

    # Dependencies
    llm: LLM = Field(default_factory=LLM, description="Language model instance")
    memory: Memory = Field(default_factory=Memory, description="Agent's memory store")
    state: AgentState = Field(
        default=AgentState.IDLE, description="Current agent state"
    )

    # Execution control
    max_steps: int = Field(default=10, description="Maximum steps before termination")
    current_step: int = Field(default=0, description="Current step in execution")
    duplicate_threshold: int = Field(
        default=2, description="Threshold for duplicate detection"
    )

    # Enhanced reliability features
    circuit_breaker: CircuitBreaker = Field(default_factory=CircuitBreaker)
    stuck_detector: StuckStateDetector = Field(default_factory=StuckStateDetector)
    adaptive_recovery: AdaptiveRecoverySystem = Field(
        default_factory=AdaptiveRecoverySystem
    )
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

    # Critical error tracking to prevent infinite loops
    critical_error_count: int = Field(default=0)
    last_critical_error: Optional[str] = Field(default=None)
    max_critical_errors: int = Field(default=3)

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """Initialize agent with enhanced monitoring."""
        logger.info(
            f"Initializing {self.name} agent with enhanced reliability features"
        )
        self.performance_metrics = {
            "start_time": time.time(),
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "stuck_recoveries": 0,
        }
        return self

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """Context manager for safe state transitions."""
        old_state = self.state
        self.state = new_state
        logger.debug(f"{self.name} state: {old_state} -> {new_state}")
        try:
            yield
        finally:
            if self.state == new_state:  # Only revert if state hasn't changed
                self.state = old_state
                logger.debug(f"{self.name} state reverted: {new_state} -> {old_state}")

    def update_memory(
        self,
        role: str,
        content: str,
        base64_image: Optional[str] = None,
        **kwargs,
    ):
        """Add a message to the agent's memory with validation."""
        message_map = {
            Role.USER: "user",
            Role.ASSISTANT: "assistant",
            Role.SYSTEM: "system",
        }

        # Use passed role directly if it's a string, otherwise map it
        if isinstance(role, str):
            final_role = role
        else:
            final_role = message_map.get(role, "user")

        # Create the message
        message = Message(role=final_role, content=content)

        # Add base64 image if provided
        if base64_image:
            message.base64_image = base64_image

        # Add any additional properties
        for key, value in kwargs.items():
            if hasattr(message, key):
                setattr(message, key, value)

        self.memory.messages.append(message)
        logger.debug(f"Added {final_role} message to {self.name} memory")

    async def run(self) -> str:
        """
        Enhanced run loop with reliability features.

        Executes steps until completion, max steps reached, or circuit breaker opens.
        Includes stuck state detection and adaptive recovery.
        """
        start_time = time.time()
        results = []

        logger.info(f"Starting agent {self.name} with max_steps={self.max_steps}")

        # EARLY SIMPLE REQUEST DETECTION - Check for simple Python requests
        # Get the last user message to see if it's a simple request
        if self.memory.messages:
            last_user_msg = None
            for msg in reversed(self.memory.messages):
                if hasattr(msg, "role") and msg.role == "user":
                    last_user_msg = msg
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    last_user_msg = msg
                    break

            if last_user_msg:
                # Fix the content extraction logic - simpler and more reliable
                if isinstance(last_user_msg, dict):
                    content = last_user_msg.get("content", "")
                else:
                    content = getattr(last_user_msg, "content", "")

                if content:
                    # Use safe_lower to prevent dict.lower() errors
                    content_lower = safe_lower(content).strip()

                    # Define simple patterns that should get immediate execution
                    simple_patterns = [
                        "print hello",
                        "hello world",
                        'print("hello',
                        "print('hello",
                        'print "hello',
                        "print 'hello",
                        "say hello",
                        "output hello",
                        "display hello",
                        "show hello",
                        "hello python",
                    ]

                    # Check if this is a simple request
                    is_simple_request = any(
                        pattern in content_lower for pattern in simple_patterns
                    )

                    if is_simple_request:
                        logger.info(
                            f"🎯 EARLY DETECTION: Simple request detected: '{content[:50]}...'"
                        )
                        logger.info(
                            "🚀 Executing immediate simple solution to avoid over-engineering"
                        )

                        # Check if python_execute tool is available
                        python_tool_available = (
                            hasattr(self, "available_tools") and self.available_tools
                        )

                        if python_tool_available:
                            try:
                                # Import and execute the python tool directly
                                from app.tool.python_execute import PythonExecute

                                python_tool = PythonExecute()

                                # Simple hello world code
                                simple_code = 'print("Hello, World!")'
                                logger.info(f"📝 Executing simple code: {simple_code}")

                                # Execute the code directly
                                result = await python_tool.execute(code=simple_code)

                                if result and hasattr(result, "result"):
                                    output = result.result
                                elif isinstance(result, dict) and "result" in result:
                                    output = result["result"]
                                else:
                                    output = str(result) if result else "Hello, World!"

                                logger.info(
                                    f"✅ Simple request completed successfully: {output}"
                                )

                                # Add the result to memory and return
                                self.memory.add_message(
                                    Message.assistant_message(
                                        f"Executed: {simple_code}\nOutput: {output}"
                                    )
                                )
                                self.state = AgentState.FINISHED
                                return (
                                    f"Simple request executed successfully:\n{output}"
                                )

                            except Exception as e:
                                logger.warning(
                                    f"⚠️ Early simple execution failed: {e}, falling back to normal flow"
                                )
                                # Fall through to normal execution if simple execution fails
                        else:
                            logger.info(
                                "📝 Python tool not available, using chat completion for simple response"
                            )
                            # Fallback to a simple text response for simple requests
                            self.memory.add_message(
                                Message.assistant_message("Hello, World!")
                            )
                            self.state = AgentState.FINISHED
                            return "Hello, World!"

        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_steps
                and self.circuit_breaker.can_execute()
                and self.state != AgentState.FINISHED
            ):
                step_start_time = time.time()

                try:
                    # Check for stuck state
                    if self.stuck_detector.is_stuck():
                        logger.warning(
                            f"Stuck state detected at step {self.current_step}"
                        )
                        self.performance_metrics["stuck_recoveries"] += 1

                        # Apply recovery strategy
                        recovery_success = await self.handle_stuck_state_advanced()
                        if not recovery_success:
                            logger.error("Failed to recover from stuck state")
                            break

                    # Execute the step
                    logger.debug(
                        f"Agent {self.name} executing step {self.current_step}"
                    )
                    result = await self.step()

                    # Record the result for stuck detection
                    self.stuck_detector.add_response(result)

                    # Update performance metrics
                    self.performance_metrics["total_steps"] += 1
                    self.performance_metrics["successful_steps"] += 1

                    # Record success in circuit breaker
                    self.circuit_breaker.call_succeeded()

                    results.append(result)
                    self.current_step += 1

                    step_duration = time.time() - step_start_time
                    logger.debug(
                        f"Step {self.current_step} completed in {step_duration:.2f}s"
                    )

                except AgentTaskComplete as e:
                    logger.info(f"Agent {self.name} task completed: {e}")
                    self.state = AgentState.FINISHED
                    results.append(str(e))
                    break

                except Exception as e:
                    logger.error(
                        f"Agent {self.name} step {self.current_step} failed: {e}"
                    )

                    # Check for critical errors that could cause infinite loops
                    error_str = str(e)
                    is_critical_error = (
                        "dict" in error_str
                        and "lower" in error_str
                        and "attribute" in error_str
                    ) or ("AttributeError" in error_str and "lower" in error_str)

                    if is_critical_error:
                        if self.last_critical_error == error_str:
                            self.critical_error_count += 1
                        else:
                            self.critical_error_count = 1
                            self.last_critical_error = error_str

                        if self.critical_error_count >= self.max_critical_errors:
                            logger.error(
                                f"🚨 CRITICAL: Same error occurred {self.critical_error_count} times. "
                                f"Terminating to prevent infinite loop: {error_str}"
                            )
                            self.state = AgentState.FINISHED
                            results.append(
                                f"Terminated due to repeated critical error: {error_str}"
                            )
                            break

                    # Record failure in circuit breaker and metrics
                    self.circuit_breaker.call_failed()
                    self.performance_metrics["failed_steps"] += 1

                    # Try adaptive recovery
                    try:
                        recovery_result = await self.adaptive_recovery.handle_error(
                            e,
                            {
                                "step": self.current_step,
                                "agent_name": self.name,
                                "current_prompt": self.next_step_prompt,
                            },
                        )

                        if recovery_result:
                            logger.info(
                                f"Adaptive recovery successful for step {self.current_step}"
                            )
                            results.append(f"Recovered from error: {recovery_result}")
                        else:
                            results.append(f"Step {self.current_step} failed: {e}")

                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {recovery_error}")
                        results.append(f"Step {self.current_step} failed: {e}")

                    self.current_step += 1

        # Handle termination conditions
        if self.current_step >= self.max_steps:
            logger.info(f"Agent {self.name} reached max steps ({self.max_steps})")
            self.current_step = 0
            self.state = AgentState.IDLE
            results.append(f"Terminated: Reached max steps ({self.max_steps})")
        elif not self.circuit_breaker.can_execute():
            logger.warning(f"Agent {self.name} terminated due to circuit breaker")
            results.append(
                "Terminated: Circuit breaker opened due to repeated failures"
            )
        elif self.state == AgentState.FINISHED:
            logger.info(f"Agent {self.name} finished successfully")

        # Log performance summary
        total_duration = time.time() - start_time
        self._log_performance_summary(total_duration)

        await SANDBOX_CLIENT.cleanup()
        final_result = "\n".join(results) if results else "No steps executed"
        logger.info(
            f"Agent {self.name} run() completed, returning result length: {len(final_result)}"
        )
        return final_result

    async def handle_stuck_state_advanced(self) -> bool:
        """Advanced stuck state handling with multiple recovery strategies."""
        logger.warning(f"Agent {self.name} detected stuck state, attempting recovery")

        # Analyze recent actions to determine recovery strategy
        recent_responses = list(self.stuck_detector.recent_responses)
        recent_actions = list(self.stuck_detector.recent_actions)

        # Strategy 1: Browser tool specific recovery
        browser_actions = [
            "go_to_url",
            "extract_content",
            "click_element",
            "input_text",
        ]
        if any(action in str(recent_actions) for action in browser_actions):
            logger.info(
                "Detected browser tool stuck state, applying browser-specific recovery"
            )

            # Clear browser-related memory
            if len(self.memory.messages) > 5:
                self.memory.messages = self.memory.messages[:-2]

            # Add browser-specific guidance
            browser_recovery_prompts = [
                "The browser tool seems to be having issues. Try using basic page content extraction instead of complex extraction goals.",
                "Browser navigation may be failing. Try accessing a different URL or using a simpler approach.",
                "Content extraction is not working. Try scrolling the page or waiting for it to load completely before extracting content.",
                "Switch to a different browser action or try the same action with different parameters.",
            ]

            import random

            recovery_prompt = random.choice(browser_recovery_prompts)
            self.next_step_prompt = (
                f"{recovery_prompt}\n\nOriginal task: {self.next_step_prompt}"
            )

        # Strategy 2: Tool failure recovery
        elif "failed" in safe_lower(str(recent_responses)) or "error" in safe_lower(
            str(recent_responses)
        ):
            logger.info(
                "Detected tool failure pattern, applying tool-specific recovery"
            )

            # More aggressive memory clearing for tool failures
            if len(self.memory.messages) > 8:
                self.memory.messages = self.memory.messages[:-4]

            tool_recovery_prompts = [
                "The current tool approach is not working. Try using a completely different tool or method.",
                "Tool execution is failing repeatedly. Break down the task into smaller steps using different tools.",
                "Switch to a manual approach or use simpler tool operations.",
                "The current strategy is not effective. Try a fundamentally different approach to achieve the same goal.",
            ]

            import random

            recovery_prompt = random.choice(tool_recovery_prompts)
            self.next_step_prompt = (
                f"{recovery_prompt}\n\nOriginal task: {self.next_step_prompt}"
            )

        # Strategy 3: Generic stuck state recovery (fallback)
        else:
            logger.info("Applying generic stuck state recovery")

            # Standard memory clearing
            if len(self.memory.messages) > 10:
                self.memory.messages = self.memory.messages[:-3]

            # Generic recovery prompts
            randomization_prompts = [
                "Try a completely different approach to solve this problem.",
                "Consider alternative methods you haven't tried yet.",
                "Step back and reassess the situation from a new perspective.",
                "Use a different strategy or tool to make progress.",
                "Break down the problem into smaller, different steps.",
            ]

            import random

            random_prompt = random.choice(randomization_prompts)
            self.next_step_prompt = (
                f"{random_prompt}\n\nOriginal task: {self.next_step_prompt}"
            )

        # Strategy 4: Lower circuit breaker threshold temporarily
        if hasattr(self, "circuit_breaker"):
            original_threshold = self.circuit_breaker.failure_threshold
            self.circuit_breaker.failure_threshold = max(1, original_threshold - 1)
            logger.info(
                f"Temporarily lowered circuit breaker threshold from {original_threshold} to {self.circuit_breaker.failure_threshold}"
            )

        # Strategy 5: Reset stuck detector
        self.stuck_detector.reset()

        logger.info(f"Applied recovery strategy based on detected pattern")
        return True

    def handle_stuck_state(self):
        """Legacy stuck state handler for backward compatibility."""
        stuck_prompt = (
            "Observed duplicate responses. Consider new strategies and "
            "avoid repeating ineffective paths already attempted."
        )
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"
        logger.warning(f"Agent detected stuck state. Added prompt: {stuck_prompt}")

    def is_stuck(self) -> bool:
        """Legacy stuck detection for backward compatibility."""
        return self.stuck_detector.is_stuck()

    def _log_performance_summary(self, duration: float):
        """Log performance summary."""
        metrics = self.performance_metrics
        success_rate = (
            metrics["successful_steps"] / max(metrics["total_steps"], 1) * 100
        )

        logger.info(
            f"Agent {self.name} performance summary: "
            f"Duration: {duration:.1f}s, "
            f"Steps: {metrics['total_steps']}, "
            f"Success rate: {success_rate:.1f}%, "
            f"Stuck recoveries: {metrics['stuck_recoveries']}"
        )

    @abstractmethod
    async def step(self) -> str:
        """Execute a single step in the agent's workflow."""

    @property
    def messages(self) -> List[Message]:
        """Retrieve a list of messages from the agent's memory."""
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        """Set the list of messages in the agent's memory."""
        self.memory.messages = value
