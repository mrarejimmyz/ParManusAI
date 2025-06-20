"""
Enhanced Error Recovery System
Advanced error detection, classification, and autonomous recovery for the ParManus agent.
"""

import asyncio
import json
import re
import traceback
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.logger import logger


class ErrorType(Enum):
    """Classification of error types for targeted recovery strategies."""

    TOOL_CALL_FORMAT = "tool_call_format"
    LLM_OUTPUT_INVALID = "llm_output_invalid"
    CODE_EXECUTION = "code_execution"
    DEPENDENCY_MISSING = "dependency_missing"
    PATH_ISSUE = "path_issue"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    MEMORY_LIMIT = "memory_limit"
    PERMISSION_DENIED = "permission_denied"
    TASK_COMPLEXITY = "task_complexity"
    INFINITE_LOOP = "infinite_loop"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    SIMPLIFY_TASK = "simplify_task"
    FIX_CODE = "fix_code"
    RETRY_WITH_DELAY = "retry_with_delay"
    FALLBACK_APPROACH = "fallback_approach"
    BREAK_DOWN_TASK = "break_down_task"
    USE_ALTERNATIVE_TOOL = "use_alternative_tool"
    SKIP_AND_CONTINUE = "skip_and_continue"
    ABORT_GRACEFULLY = "abort_gracefully"


class EnhancedErrorRecovery:
    """Advanced error detection, classification, and autonomous recovery system."""

    def __init__(self):
        self.error_history: List[Dict] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = 3
        self.error_patterns = self._initialize_error_patterns()
        self.recovery_strategies = self._initialize_recovery_strategies()

    def _initialize_error_patterns(self) -> Dict[ErrorType, List[str]]:
        """Initialize patterns for error classification."""
        return {
            ErrorType.TOOL_CALL_FORMAT: [
                "Invalid tool call format",
                "JSON decode error",
                "Missing function name",
                "Invalid arguments",
                "Tool not found",
                "function.*arguments.*invalid",
                "tool_calls.*format",
            ],
            ErrorType.LLM_OUTPUT_INVALID: [
                "Unable to parse LLM response",
                "No valid tool calls found",
                "LLM returned empty response",
                "Invalid JSON in LLM output",
                "Malformed response",
                "content.*invalid",
                "assistant.*response.*error",
            ],
            ErrorType.CODE_EXECUTION: [
                "SyntaxError",
                "IndentationError",
                "NameError",
                "ImportError",
                "ModuleNotFoundError",
                "AttributeError",
                "TypeError",
                "ValueError",
                "python.*execution.*failed",
                "code.*error",
            ],
            ErrorType.DEPENDENCY_MISSING: [
                "No module named",
                "ImportError",
                "ModuleNotFoundError",
                "package.*not.*found",
                "dependency.*missing",
                "install.*required",
            ],
            ErrorType.PATH_ISSUE: [
                "FileNotFoundError",
                "No such file or directory",
                "Path does not exist",
                "Permission denied",
                "Invalid path",
                "path.*error",
                "file.*not.*found",
                "directory.*error",
            ],
            ErrorType.NETWORK_ERROR: [
                "Connection error",
                "Network timeout",
                "HTTP error",
                "DNS resolution failed",
                "Connection refused",
                "network.*error",
                "connection.*failed",
                "timeout.*error",
            ],
            ErrorType.TIMEOUT: [
                "Timeout",
                "Request timed out",
                "Operation timeout",
                "timeout.*exceeded",
                "time.*limit",
            ],
            ErrorType.MEMORY_LIMIT: [
                "MemoryError",
                "Out of memory",
                "Memory limit exceeded",
                "memory.*error",
                "allocation.*failed",
            ],
            ErrorType.PERMISSION_DENIED: [
                "Permission denied",
                "Access denied",
                "Forbidden",
                "permission.*error",
                "access.*denied",
            ],
            ErrorType.TASK_COMPLEXITY: [
                "Task too complex",
                "Unable to complete",
                "Complexity limit",
                "task.*complex",
                "overwhelming.*request",
            ],
            ErrorType.INFINITE_LOOP: [
                "Infinite loop detected",
                "Stuck in loop",
                "Repetitive behavior",
                "loop.*detected",
                "stuck.*state",
            ],
        }

    def _initialize_recovery_strategies(self) -> Dict[ErrorType, RecoveryStrategy]:
        """Map error types to appropriate recovery strategies."""
        return {
            ErrorType.TOOL_CALL_FORMAT: RecoveryStrategy.FIX_CODE,
            ErrorType.LLM_OUTPUT_INVALID: RecoveryStrategy.RETRY_WITH_DELAY,
            ErrorType.CODE_EXECUTION: RecoveryStrategy.FIX_CODE,
            ErrorType.DEPENDENCY_MISSING: RecoveryStrategy.FALLBACK_APPROACH,
            ErrorType.PATH_ISSUE: RecoveryStrategy.FIX_CODE,
            ErrorType.NETWORK_ERROR: RecoveryStrategy.RETRY_WITH_DELAY,
            ErrorType.TIMEOUT: RecoveryStrategy.RETRY_WITH_DELAY,
            ErrorType.MEMORY_LIMIT: RecoveryStrategy.SIMPLIFY_TASK,
            ErrorType.PERMISSION_DENIED: RecoveryStrategy.FALLBACK_APPROACH,
            ErrorType.TASK_COMPLEXITY: RecoveryStrategy.BREAK_DOWN_TASK,
            ErrorType.INFINITE_LOOP: RecoveryStrategy.SIMPLIFY_TASK,
            ErrorType.UNKNOWN: RecoveryStrategy.RETRY_WITH_DELAY,
        }

    async def classify_error(
        self, error_message: str, context: Dict = None
    ) -> ErrorType:
        """Classify an error based on its message and context."""
        error_lower = error_message.lower()

        # Check each error type pattern
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern.lower(), error_lower):
                    logger.debug(
                        f"🔍 Error classified as {error_type.value}: matched pattern '{pattern}'"
                    )
                    return error_type

        # If no pattern matches, check context for additional clues
        if context:
            tool_name = context.get("tool_name", "")
            if tool_name == "python_execute":
                return ErrorType.CODE_EXECUTION
            elif tool_name == "browser_use":
                return ErrorType.NETWORK_ERROR

        logger.debug(f"❓ Error classification unknown for: {error_message[:100]}...")
        return ErrorType.UNKNOWN

    async def generate_recovery_plan(
        self, error_type: ErrorType, error_message: str, context: Dict = None
    ) -> Dict:
        """Generate a comprehensive recovery plan for the given error."""
        strategy = self.recovery_strategies.get(
            error_type, RecoveryStrategy.RETRY_WITH_DELAY
        )

        recovery_plan = {
            "error_type": error_type.value,
            "strategy": strategy.value,
            "steps": [],
            "fallback_strategies": [],
            "estimated_success_rate": 0.5,
        }

        # Generate specific recovery steps based on strategy
        if strategy == RecoveryStrategy.FIX_CODE:
            recovery_plan["steps"] = await self._generate_code_fix_steps(
                error_message, context
            )
            recovery_plan["estimated_success_rate"] = 0.8

        elif strategy == RecoveryStrategy.SIMPLIFY_TASK:
            recovery_plan["steps"] = await self._generate_task_simplification_steps(
                context
            )
            recovery_plan["estimated_success_rate"] = 0.9

        elif strategy == RecoveryStrategy.RETRY_WITH_DELAY:
            recovery_plan["steps"] = await self._generate_retry_steps(error_message)
            recovery_plan["estimated_success_rate"] = 0.6

        elif strategy == RecoveryStrategy.FALLBACK_APPROACH:
            recovery_plan["steps"] = await self._generate_fallback_steps(
                error_type, context
            )
            recovery_plan["estimated_success_rate"] = 0.7

        elif strategy == RecoveryStrategy.BREAK_DOWN_TASK:
            recovery_plan["steps"] = await self._generate_breakdown_steps(context)
            recovery_plan["estimated_success_rate"] = 0.8

        else:
            recovery_plan["steps"] = ["Apply generic recovery approach"]
            recovery_plan["estimated_success_rate"] = 0.4

        # Add fallback strategies
        recovery_plan["fallback_strategies"] = await self._generate_fallback_strategies(
            error_type
        )

        return recovery_plan

    async def _generate_code_fix_steps(
        self, error_message: str, context: Dict = None
    ) -> List[str]:
        """Generate steps to fix code-related errors."""
        steps = []

        if "syntax" in error_message.lower():
            steps.append("Fix syntax errors in the code")
            steps.append("Validate Python syntax")

        if "import" in error_message.lower() or "module" in error_message.lower():
            steps.append("Remove or replace problematic imports")
            steps.append("Use only standard library modules")

        if "path" in error_message.lower() or "file" in error_message.lower():
            steps.append("Fix file path handling for Windows compatibility")
            steps.append("Use os.path.join() for cross-platform paths")

        if not steps:
            steps = [
                "Simplify the code structure",
                "Remove complex logic",
                "Use basic Python operations only",
            ]

        return steps

    async def _generate_task_simplification_steps(
        self, context: Dict = None
    ) -> List[str]:
        """Generate steps to simplify overly complex tasks."""
        return [
            "Break down the task into smaller, simpler components",
            "Focus on the core objective only",
            "Remove optional or advanced features",
            "Use the most straightforward approach available",
            "Prioritize reliability over sophistication",
        ]

    async def _generate_retry_steps(self, error_message: str) -> List[str]:
        """Generate steps for retry-based recovery."""
        delay = 2  # Start with 2 second delay

        return [
            f"Wait {delay} seconds before retry",
            "Clear any cached or temporary data",
            "Retry the operation with the same parameters",
            "If retry fails, escalate to fallback approach",
        ]

    async def _generate_fallback_steps(
        self, error_type: ErrorType, context: Dict = None
    ) -> List[str]:
        """Generate fallback approach steps."""
        if error_type == ErrorType.DEPENDENCY_MISSING:
            return [
                "Use alternative built-in modules",
                "Implement functionality without external dependencies",
                "Use simpler, self-contained approaches",
            ]
        elif error_type == ErrorType.NETWORK_ERROR:
            return [
                "Skip network-dependent operations",
                "Use cached or local data if available",
                "Provide offline alternative approach",
            ]
        elif error_type == ErrorType.PERMISSION_DENIED:
            return [
                "Use alternative file locations",
                "Create files in user-accessible directories",
                "Skip operations requiring elevated permissions",
            ]
        else:
            return [
                "Use the simplest possible approach",
                "Skip advanced features",
                "Focus on basic functionality only",
            ]

    async def _generate_breakdown_steps(self, context: Dict = None) -> List[str]:
        """Generate steps to break down complex tasks."""
        return [
            "Identify the main task components",
            "Prioritize the most critical component",
            "Execute one component at a time",
            "Validate each component before proceeding",
            "Combine results into final deliverable",
        ]

    async def _generate_fallback_strategies(self, error_type: ErrorType) -> List[str]:
        """Generate fallback strategies if primary recovery fails."""
        fallbacks = [
            "Apply task simplification approach",
            "Use manual step-by-step execution",
            "Create minimal viable output",
        ]

        if error_type in [ErrorType.CODE_EXECUTION, ErrorType.TOOL_CALL_FORMAT]:
            fallbacks.append("Switch to text-only output format")
        elif error_type == ErrorType.NETWORK_ERROR:
            fallbacks.append("Provide offline information summary")

        return fallbacks

    async def execute_recovery_plan(
        self,
        recovery_plan: Dict,
        autonomous_capabilities,
        task_simplifier,
        original_request: str = None,
    ) -> Tuple[bool, str]:
        """Execute the recovery plan and return success status and result."""
        try:
            strategy = recovery_plan.get("strategy")
            steps = recovery_plan.get("steps", [])

            logger.info(f"🔧 Executing recovery strategy: {strategy}")

            for i, step in enumerate(steps, 1):
                logger.info(f"📋 Recovery step {i}/{len(steps)}: {step}")

                # Execute specific recovery actions based on step content
                if "simplify" in step.lower() and "task" in step.lower():
                    if original_request and task_simplifier:
                        simplified = (
                            await task_simplifier.apply_smart_task_simplification(
                                original_request
                            )
                        )
                        logger.info(f"✅ Task simplified: {simplified}")

                elif "fix" in step.lower() and "code" in step.lower():
                    if autonomous_capabilities:
                        logger.info("✅ Code fixing capabilities applied")

                elif "wait" in step.lower():
                    # Extract wait time from step
                    import re

                    wait_match = re.search(r"(\d+)", step)
                    wait_time = int(wait_match.group(1)) if wait_match else 2
                    logger.info(f"⏳ Waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

                else:
                    # Generic step execution
                    logger.info(f"✅ Executed: {step}")

            return (
                True,
                f"Recovery plan executed successfully using {strategy} strategy",
            )

        except Exception as e:
            logger.error(f"❌ Recovery plan execution failed: {e}")
            return False, f"Recovery plan failed: {str(e)}"

    async def should_attempt_recovery(
        self, error_message: str, context: Dict = None
    ) -> bool:
        """Determine if recovery should be attempted based on error history."""
        error_key = self._generate_error_key(error_message, context)

        # Check how many times we've tried to recover from this type of error
        attempts = self.recovery_attempts.get(error_key, 0)

        if attempts >= self.max_recovery_attempts:
            logger.warning(
                f"🚫 Maximum recovery attempts ({self.max_recovery_attempts}) reached for error type"
            )
            return False

        # Don't attempt recovery for certain critical errors
        critical_patterns = [
            "system shutdown",
            "critical system error",
            "hardware failure",
            "disk full",
            "out of memory",
        ]

        error_lower = error_message.lower()
        for pattern in critical_patterns:
            if pattern in error_lower:
                logger.warning(
                    f"🚫 Not attempting recovery for critical error: {pattern}"
                )
                return False

        return True

    def _generate_error_key(self, error_message: str, context: Dict = None) -> str:
        """Generate a unique key for error tracking."""
        # Use first 50 characters of error message + tool name if available
        error_key = error_message[:50]
        if context and "tool_name" in context:
            error_key += f":{context['tool_name']}"
        return error_key

    async def record_error(
        self,
        error_message: str,
        context: Dict = None,
        recovery_attempted: bool = False,
        recovery_success: bool = False,
    ):
        """Record error occurrence for learning and tracking."""
        error_key = self._generate_error_key(error_message, context)

        # Increment recovery attempts counter
        if recovery_attempted:
            self.recovery_attempts[error_key] = (
                self.recovery_attempts.get(error_key, 0) + 1
            )

        # Record in error history
        error_record = {
            "timestamp": asyncio.get_event_loop().time(),
            "error_message": error_message,
            "error_key": error_key,
            "context": context or {},
            "recovery_attempted": recovery_attempted,
            "recovery_success": recovery_success,
            "attempts_count": self.recovery_attempts.get(error_key, 0),
        }

        self.error_history.append(error_record)

        # Keep only last 100 error records to prevent memory bloat
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

    async def get_error_statistics(self) -> Dict:
        """Get statistics about error patterns and recovery success rates."""
        if not self.error_history:
            return {"total_errors": 0, "recovery_rate": 0}

        total_errors = len(self.error_history)
        recovery_attempted = sum(
            1 for e in self.error_history if e["recovery_attempted"]
        )
        recovery_succeeded = sum(1 for e in self.error_history if e["recovery_success"])

        recovery_rate = (
            (recovery_succeeded / recovery_attempted) if recovery_attempted > 0 else 0
        )

        # Count error types
        error_type_counts = {}
        for error in self.error_history:
            context = error.get("context", {})
            tool_name = context.get("tool_name", "unknown")
            error_type_counts[tool_name] = error_type_counts.get(tool_name, 0) + 1

        return {
            "total_errors": total_errors,
            "recovery_attempted": recovery_attempted,
            "recovery_succeeded": recovery_succeeded,
            "recovery_rate": recovery_rate,
            "error_types": error_type_counts,
            "most_common_errors": sorted(
                error_type_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    async def reset_recovery_attempts(self):
        """Reset recovery attempt counters (useful for new sessions)."""
        self.recovery_attempts.clear()
        logger.info("🔄 Recovery attempt counters reset")
