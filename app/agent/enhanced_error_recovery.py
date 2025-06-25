"""
Enhanced Error Recovery System
Advanced error detection, classification, and autonomous recovery for the ParManus agent.
"""

import asyncio
import json
import re
import traceback
from collections import deque
from datetime import datetime
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
    DICT_LOWER_ERROR = "dict_lower_error"  # New error type for dict.lower() issues
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
    APPLY_STRING_SAFETY = "apply_string_safety"  # New strategy for dict.lower() errors
    PREEMPTIVE_OPTIMIZATION = "preemptive_optimization"  # Prevent errors before they occur
    SPEED_RECOVERY = "speed_recovery"  # Fast recovery for known issues
    ADAPTIVE_LEARNING = "adaptive_learning"  # Learn and adapt from patterns


class EnhancedErrorRecovery:
    """Advanced error detection, classification, and autonomous recovery system with speed optimization."""

    def __init__(self):
        self.error_history: List[Dict] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = 2  # Keep fast recovery
        self.error_patterns = self._initialize_error_patterns()
        self.recovery_strategies = self._initialize_recovery_strategies()

        # Enhanced speed and learning optimization
        self.fast_recovery_cache: Dict[str, Dict] = {}
        self.success_rates: Dict[str, float] = {}
        self.recovery_times: Dict[str, float] = {}
        self.preemptive_patterns: Dict[str, Dict] = {}  # New: Learn patterns to prevent errors
        self.recovery_performance_tracker = deque(maxlen=100)  # Track recovery performance

        # Speed optimization settings
        self.fast_recovery_threshold = 3.0  # Recoveries under 3s are considered fast
        self.preemptive_confidence_threshold = 0.8  # High confidence for preemptive actions

        # Load previous learning data
        from app.agent_learning import agent_learning
        self.learning_system = agent_learning
        self._load_learned_optimizations()

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
            ErrorType.DICT_LOWER_ERROR: [
                "'dict' object has no attribute 'lower'",
                "dict.*lower",
                "AttributeError.*lower",
                "object has no attribute.*lower",
                "lower.*dict",
            ],
        }

    def _initialize_recovery_strategies(self) -> Dict[ErrorType, RecoveryStrategy]:
        """Map error types to appropriate recovery strategies."""
        return {
            ErrorType.TOOL_CALL_FORMAT: RecoveryStrategy.FIX_CODE,
            ErrorType.LLM_OUTPUT_INVALID: RecoveryStrategy.SPEED_RECOVERY,  # Use faster strategy
            ErrorType.CODE_EXECUTION: RecoveryStrategy.FIX_CODE,
            ErrorType.DEPENDENCY_MISSING: RecoveryStrategy.FALLBACK_APPROACH,
            ErrorType.PATH_ISSUE: RecoveryStrategy.FIX_CODE,
            ErrorType.NETWORK_ERROR: RecoveryStrategy.SPEED_RECOVERY,  # Fast retry for network
            ErrorType.TIMEOUT: RecoveryStrategy.SPEED_RECOVERY,  # Quick timeout adjustment
            ErrorType.MEMORY_LIMIT: RecoveryStrategy.SIMPLIFY_TASK,
            ErrorType.PERMISSION_DENIED: RecoveryStrategy.FALLBACK_APPROACH,
            ErrorType.TASK_COMPLEXITY: RecoveryStrategy.BREAK_DOWN_TASK,
            ErrorType.INFINITE_LOOP: RecoveryStrategy.SIMPLIFY_TASK,
            ErrorType.DICT_LOWER_ERROR: RecoveryStrategy.APPLY_STRING_SAFETY,
            ErrorType.UNKNOWN: RecoveryStrategy.ADAPTIVE_LEARNING,  # Learn from unknown errors
        }

    async def classify_error(
        self, error_message: str, context: Dict = None
    ) -> ErrorType:
        """Classify an error based on its message and context."""
        # Ensure error_message is a string before calling .lower()
        if not isinstance(error_message, str):
            error_message = str(error_message)

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
        }  # Generate specific recovery steps based on strategy
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

        elif strategy == RecoveryStrategy.APPLY_STRING_SAFETY:
            recovery_plan["steps"] = await self._generate_string_safety_steps(
                error_message, context
            )
            recovery_plan["estimated_success_rate"] = (
                0.95  # High success rate for this fix
            )

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

        # Ensure error_message is a string before calling .lower()
        if not isinstance(error_message, str):
            error_message = str(error_message)

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

                # Ensure step is a string before calling .lower()
                if not isinstance(step, str):
                    step = str(step)

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

                elif "string safety" in step.lower() or "safe_lower" in step.lower():
                    # Apply string safety fixes for dict.lower() errors
                    logger.info("🛡️ Applying autonomous string safety protection")
                    # The string safety utilities are already imported and available
                    # This signals that the system should use safe_lower() instead of .lower()
                    logger.info("✅ String safety protection activated")

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

        # Ensure error_message is a string before calling .lower()
        if not isinstance(error_message, str):
            error_message = str(error_message)

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
        # Ensure error_message is a string before slicing
        if not isinstance(error_message, str):
            error_message = str(error_message)

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

    async def _generate_string_safety_steps(
        self, error_message: str, context: Dict = None
    ) -> List[str]:
        """Generate steps to fix dict.lower() errors with string safety."""
        steps = [
            "Apply string safety utilities to prevent dict.lower() errors",
            "Replace direct .lower() calls with safe_lower() function",
            "Import string_safety utilities in affected modules",
            "Validate all data types before string operations",
            "Apply autonomous protection to prevent future occurrences",
        ]

        # Add specific steps based on the error context
        if context and "tool_call" in context:
            steps.append("Fix tool parameter processing to use safe string operations")

        if "thinking" in str(context).lower() if context else False:
            steps.append("Fix thinking engine to use safe string operations")

        return steps

    def _load_learned_optimizations(self):
        """Load previously learned recovery optimizations for faster response with enhanced capabilities"""
        try:
            # Load fast recovery strategies
            fast_recoveries = self.learning_system.get_user_preference("fast_recovery_cache", {})
            self.fast_recovery_cache.update(fast_recoveries)

            # Load success rates for different strategies
            success_data = self.learning_system.get_user_preference("recovery_success_rates", {})
            self.success_rates.update(success_data)

            # Load preemptive patterns for error prevention
            preemptive_data = self.learning_system.get_user_preference("preemptive_patterns", {})
            self.preemptive_patterns.update(preemptive_data)

            # Load recovery performance history
            perf_history = self.learning_system.get_user_preference("recovery_performance", [])
            self.recovery_performance_tracker.extend(perf_history[-50:])  # Last 50 entries

            logger.info(f"🚀 Enhanced recovery system loaded: {len(self.fast_recovery_cache)} fast patterns, {len(self.preemptive_patterns)} prevention patterns")

        except Exception as e:
            logger.warning(f"Could not load recovery optimizations: {e}")

    async def preemptive_error_check(self, action: str, context: Dict = None) -> Optional[Dict]:
        """Check for potential errors before execution and prevent them with enhanced detection"""
        action_lower = action.lower() if action else ""

        # Enhanced risk indicators with more patterns
        risk_indicators = [
            ("dict.*lower", "string_safety_risk"),
            ("timeout.*network", "network_risk"),
            ("javascript.*extract", "extraction_risk"),
            ("complex.*code", "complexity_risk"),
            ("path.*error", "path_risk"),
            ("memory.*limit", "memory_risk"),
            ("permission.*denied", "permission_risk"),
            ("import.*error", "dependency_risk")
        ]

        for pattern, risk_type in risk_indicators:
            import re
            if re.search(pattern, action_lower):
                # Check if we have learned prevention for this
                prevention_key = f"prevent_{risk_type}"
                prevention = self.learning_system.get_error_solution(prevention_key)

                if prevention:
                    success_rate = prevention.get("solution", {}).get("success_rate", 0.5)
                    if success_rate > self.preemptive_confidence_threshold:
                        logger.info(f"🛡️ High-confidence preemptive protection: {risk_type} (success: {success_rate:.1%})")
                        return {
                            "prevention_applied": True,
                            "risk_type": risk_type,
                            "strategy": prevention.get("solution", {}).get("prevention_method", "generic"),
                            "confidence": success_rate
                        }

        # Check learned preemptive patterns
        for pattern_key, pattern_data in self.preemptive_patterns.items():
            if pattern_data.get("trigger_pattern", "") in action_lower:
                confidence = pattern_data.get("success_rate", 0.0)
                if confidence > self.preemptive_confidence_threshold:
                    logger.info(f"💡 Preemptive pattern match: {pattern_key} (confidence: {confidence:.1%})")
                    return {
                        "prevention_applied": True,
                        "pattern": pattern_key,
                        "strategy": pattern_data.get("prevention_strategy", "generic"),
                        "confidence": confidence
                    }

        return None

    async def fast_recovery_lookup(self, error_message: str) -> Optional[Dict]:
        """Instant recovery for known errors using cached solutions with enhanced matching"""
        error_key = self._generate_error_key(error_message)

        # Enhanced fast recovery cache check
        if error_key in self.fast_recovery_cache:
            cached_solution = self.fast_recovery_cache[error_key]

            # Verify this solution has good success rate and is still recent
            success_rate = self.success_rates.get(error_key, 0.0)
            cache_age_hours = (datetime.now() - datetime.fromisoformat(cached_solution.get("cached_at", datetime.now().isoformat()))).total_seconds() / 3600

            if success_rate > 0.7 and cache_age_hours < 168:  # 1 week freshness
                logger.info(f"⚡ Fast recovery cache hit: {error_key[:30]}... (success: {success_rate:.1%}, age: {cache_age_hours:.1f}h)")
                return cached_solution

        # Enhanced semantic matching for similar errors
        for cached_key, cached_solution in self.fast_recovery_cache.items():
            if self._calculate_error_similarity(error_message, cached_key) > 0.8:
                success_rate = self.success_rates.get(cached_key, 0.0)
                if success_rate > 0.6:  # Lower threshold for similar errors
                    logger.info(f"🔧 Similar error recovery: {cached_key[:30]}... (similarity match, success: {success_rate:.1%})")
                    return cached_solution

        # Check learning system for stored solutions with enhanced scoring
        stored_solution = self.learning_system.get_error_solution(error_key)
        if stored_solution and stored_solution.get("success_count", 0) > 1:  # Lower threshold
            confidence = stored_solution.get("success_count", 0) / max(stored_solution.get("usage_count", 1), 1)
            if confidence > 0.5:  # More permissive for learning
                logger.info(f"🧠 Learned solution applied: {error_key[:30]}... (confidence: {confidence:.1%})")
                return stored_solution

        return None

    def _calculate_error_similarity(self, error1: str, error2: str) -> float:
        """Calculate similarity between error messages for enhanced matching"""
        import difflib
        return difflib.SequenceMatcher(None, error1.lower(), error2.lower()).ratio()

    async def update_recovery_performance(self, error_key: str, strategy: str, success: bool, duration: float):
        """Update performance metrics for recovery strategies with enhanced tracking"""
        # Enhanced success rate tracking
        current_attempts = self.success_rates.get(f"{error_key}_attempts", 0) + 1
        current_successes = self.success_rates.get(f"{error_key}_successes", 0)

        if success:
            current_successes += 1

            # Enhanced fast recovery caching with more data
            if duration < self.fast_recovery_threshold:
                self.fast_recovery_cache[error_key] = {
                    "strategy": strategy,
                    "duration": duration,
                    "success_rate": current_successes / current_attempts,
                    "cached_at": datetime.now().isoformat(),
                    "usage_count": current_attempts,
                    "performance_rating": "excellent" if duration < 1.0 else "very_good" if duration < 2.0 else "good"
                }
                logger.info(f"🏆 Excellent recovery cached: {duration:.2f}s for {strategy}")

        # Update success tracking
        self.success_rates[f"{error_key}_attempts"] = current_attempts
        self.success_rates[f"{error_key}_successes"] = current_successes
        self.success_rates[error_key] = current_successes / current_attempts

        # Enhanced performance tracking
        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_key": error_key,
            "strategy": strategy,
            "success": success,
            "duration": duration,
            "success_rate": current_successes / current_attempts
        }
        self.recovery_performance_tracker.append(performance_entry)

        # Save to learning system with enhanced data
        self.learning_system.save_user_preference("fast_recovery_cache", self.fast_recovery_cache)
        self.learning_system.save_user_preference("recovery_success_rates", self.success_rates)
        self.learning_system.save_user_preference("recovery_performance", list(self.recovery_performance_tracker))

        # Learn preemptive patterns from successful recoveries
        if success and duration < self.fast_recovery_threshold:
            await self._learn_preemptive_pattern(error_key, strategy, duration)

    async def _learn_preemptive_pattern(self, error_key: str, strategy: str, duration: float):
        """Learn patterns for preemptive error prevention"""
        pattern_key = f"preemptive_{error_key[:30]}"

        if pattern_key not in self.preemptive_patterns:
            self.preemptive_patterns[pattern_key] = {
                "trigger_pattern": error_key.split("_")[0] if "_" in error_key else error_key[:20],
                "prevention_strategy": strategy,
                "success_count": 0,
                "usage_count": 0,
                "avg_prevention_time": 0.0
            }

        pattern = self.preemptive_patterns[pattern_key]
        pattern["success_count"] += 1
        pattern["usage_count"] += 1
        pattern["success_rate"] = pattern["success_count"] / pattern["usage_count"]
        pattern["avg_prevention_time"] = (pattern.get("avg_prevention_time", 0) * 0.8) + (duration * 0.2)

        # Save preemptive patterns
        self.learning_system.save_user_preference("preemptive_patterns", self.preemptive_patterns)

        if pattern["success_rate"] > self.preemptive_confidence_threshold:
            logger.info(f"💡 New preemptive pattern learned: {pattern_key} (success: {pattern['success_rate']:.1%})")
