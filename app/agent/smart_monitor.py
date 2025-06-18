"""
Advanced Smart Agent Monitor
Comprehensive monitoring system that handles timeouts, prevents duplicate files,
manages stuck states, and provides intelligent recovery mechanisms
"""

import asyncio
import glob
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from app.logger import logger


@dataclass
class ActionHistory:
    """Track action history for pattern detection"""

    action: str
    timestamp: datetime
    outcome: str
    duration: float
    output_snippet: str


@dataclass
class FileTracker:
    """Track file creation to prevent duplicates"""

    created_files: Set[str] = field(default_factory=set)
    file_patterns: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_cleanup: datetime = field(default_factory=datetime.now)


@dataclass
class TaskState:
    """Enhanced task state tracking"""

    task_name: str
    start_time: datetime
    last_progress: datetime
    phase: str = "unknown"
    step: int = 0
    max_steps: int = 10
    progress_percentage: float = 0.0
    deliverables: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class SmartAgentMonitor:
    """
    Advanced monitoring system for AI agents that:
    1. Handles timeouts intelligently
    2. Prevents duplicate file creation
    3. Detects and resolves stuck states
    4. Provides smart recovery mechanisms
    5. Manages task completion
    """

    def __init__(self, llm=None, workspace_path: str = "workspace"):
        self.llm = llm
        self.workspace_path = workspace_path

        # Enhanced tracking
        self.action_history: deque = deque(maxlen=50)  # Keep last 50 actions
        self.file_tracker = FileTracker()
        self.task_state: Optional[TaskState] = None

        # Advanced thresholds
        self.max_action_time = 60.0  # Max time per action
        self.max_idle_time = 180.0  # Max time without progress
        self.max_repeated_patterns = 3
        self.duplicate_file_threshold = 2

        # Circuit breaker
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_count = 0
        self.circuit_breaker_cooldown = 300  # 5 minutes
        self.last_circuit_break = None

        # Recovery strategies
        self.recovery_strategies = [
            "simplify_task",
            "change_approach",
            "skip_current_step",
            "restart_phase",
            "complete_with_partial",
        ]
        self.current_recovery_index = 0

    async def start_task_monitoring(self, task_name: str, estimated_steps: int = 10):
        """Initialize monitoring for a new task"""
        self.task_state = TaskState(
            task_name=task_name,
            start_time=datetime.now(),
            last_progress=datetime.now(),
            max_steps=estimated_steps,
        )
        self.circuit_breaker_count = 0
        self.current_recovery_index = 0

        # Clean up old files if needed
        await self._cleanup_old_files()

        logger.info(f"🎯 Started monitoring task: {task_name}")

    async def monitor_action(
        self, action: str, timeout: float = 60.0, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Monitor a single action with comprehensive analysis
        """
        if not self.task_state:
            await self.start_task_monitoring("Unknown Task")

        start_time = time.time()
        action_id = f"{action}_{int(start_time)}"

        # Check circuit breaker
        if self._is_circuit_broken():
            return await self._handle_circuit_breaker(action)

        # Pre-action analysis
        pre_analysis = await self._pre_action_analysis(action)
        if pre_analysis.get("should_skip"):
            return pre_analysis

        try:
            # Execute with timeout monitoring
            result = await self._execute_with_smart_timeout(action, timeout, context)

            # Post-action analysis
            duration = time.time() - start_time
            outcome = result.get("status", "completed")

            # Record action
            self._record_action(action, outcome, duration, result.get("output", ""))

            # Analyze patterns and detect issues
            analysis = await self._comprehensive_analysis()

            # Handle stuck states
            if analysis.get("is_stuck"):
                recovery = await self._smart_recovery(analysis)
                analysis["recovery"] = recovery

            # Update progress if successful
            if outcome == "completed" and not analysis.get("is_stuck"):
                self._update_progress()

            return {
                "action_id": action_id,
                "status": outcome,
                "duration": duration,
                "analysis": analysis,
                **result,
            }

        except Exception as e:
            # Handle errors with context
            return await self._handle_action_error(action, e, time.time() - start_time)

    async def _execute_with_smart_timeout(
        self, action: str, timeout: float, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute action with intelligent timeout handling"""

        # Adjust timeout based on action type and history
        adjusted_timeout = self._calculate_smart_timeout(action, timeout)

        try:
            # Create timeout task
            timeout_task = asyncio.create_task(asyncio.sleep(adjusted_timeout))
            action_task = asyncio.create_task(
                self._simulate_action_execution(action, context)
            )

            # Wait for first completion
            done, pending = await asyncio.wait(
                [action_task, timeout_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            if action_task in done:
                # Action completed
                return await action_task
            else:
                # Timeout occurred
                return await self._handle_smart_timeout(action, adjusted_timeout)

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "output": f"Action execution failed: {e}",
            }

    async def _simulate_action_execution(
        self, action: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Simulate actual action execution (replace with real execution)"""
        # This would be replaced with actual agent action execution
        await asyncio.sleep(0.1)  # Minimal delay for testing
        return {
            "status": "completed",
            "output": f"Action '{action}' completed successfully",
            "files_created": [],
            "context": context or {},
        }

    def _calculate_smart_timeout(self, action: str, base_timeout: float) -> float:
        """Calculate intelligent timeout based on action history"""
        # Get historical data for similar actions
        similar_actions = [
            h
            for h in self.action_history
            if action.lower() in h.action.lower() or h.action.lower() in action.lower()
        ]

        if similar_actions:
            avg_duration = sum(h.duration for h in similar_actions) / len(
                similar_actions
            )
            # Add 50% buffer to average duration
            smart_timeout = avg_duration * 1.5
            # But don't exceed 3x base timeout or go below base timeout
            return max(base_timeout, min(smart_timeout, base_timeout * 3))

        return base_timeout

    async def _handle_smart_timeout(
        self, action: str, timeout: float
    ) -> Dict[str, Any]:
        """Handle timeout with intelligent recovery"""
        logger.warning(f"⏱️ Action '{action}' timed out after {timeout}s")

        # Analyze why timeout occurred
        timeout_analysis = await self._analyze_timeout_cause(action)

        # Suggest recovery based on analysis
        if timeout_analysis.get("likely_cause") == "heavy_computation":
            return {
                "status": "timeout_retry",
                "message": "Heavy computation detected, will retry with longer timeout",
                "suggested_timeout": timeout * 2,
                "output": f"Timeout due to heavy computation",
            }
        elif timeout_analysis.get("likely_cause") == "network_delay":
            return {
                "status": "timeout_network",
                "message": "Network delay detected, will retry with exponential backoff",
                "output": f"Timeout due to network issues",
            }
        else:
            return {
                "status": "timeout_stuck",
                "message": "Agent appears stuck, triggering recovery",
                "output": f"Action stuck - timeout after {timeout}s",
            }

    async def _analyze_timeout_cause(self, action: str) -> Dict[str, Any]:
        """Analyze likely cause of timeout"""
        # Check recent actions for patterns
        recent_actions = list(self.action_history)[-5:]

        # Check for computation-heavy actions
        computation_keywords = ["search", "analyze", "process", "generate", "scrape"]
        if any(keyword in action.lower() for keyword in computation_keywords):
            return {"likely_cause": "heavy_computation"}

        # Check for network-related actions
        network_keywords = ["web", "url", "download", "fetch", "api"]
        if any(keyword in action.lower() for keyword in network_keywords):
            return {"likely_cause": "network_delay"}

        # Check for repeated similar actions (stuck pattern)
        similar_recent = sum(
            1 for h in recent_actions if action.lower() in h.action.lower()
        )
        if similar_recent >= 2:
            return {"likely_cause": "stuck_pattern"}

        return {"likely_cause": "unknown"}

    async def _pre_action_analysis(self, action: str) -> Dict[str, Any]:
        """Analyze before executing action to prevent known issues"""
        analysis = {"should_skip": False, "reason": None}

        # Check for duplicate file creation
        if await self._would_create_duplicate_file(action):
            analysis.update(
                {
                    "should_skip": True,
                    "reason": "Would create duplicate file",
                    "status": "skipped_duplicate",
                    "suggestion": "Use existing file instead",
                }
            )
            return analysis

        # Check for repeated action patterns
        if self._is_action_pattern_repeating(action):
            analysis.update(
                {
                    "should_skip": True,
                    "reason": "Repeated action pattern detected",
                    "status": "skipped_pattern",
                    "suggestion": "Try alternative approach",
                }
            )
            return analysis

        # Check resource availability
        if not await self._check_resource_availability():
            analysis.update(
                {
                    "should_skip": True,
                    "reason": "Insufficient resources",
                    "status": "skipped_resources",
                    "suggestion": "Wait for resources or cleanup",
                }
            )
            return analysis

        return analysis

    async def _would_create_duplicate_file(self, action: str) -> bool:
        """Check if action would create a duplicate file"""
        # Extract potential filename patterns from action
        create_keywords = ["create", "generate", "write", "save"]
        if not any(keyword in action.lower() for keyword in create_keywords):
            return False

        # Check workspace for similar files
        existing_files = glob.glob(os.path.join(self.workspace_path, "*.md"))

        # Extract topic/subject from action
        action_lower = action.lower()
        for keyword in ["ai", "artificial intelligence", "report", "analysis"]:
            if keyword in action_lower:
                # Count files with similar topics
                similar_files = [
                    f
                    for f in existing_files
                    if keyword.replace(" ", "_") in os.path.basename(f).lower()
                ]

                if len(similar_files) >= self.duplicate_file_threshold:
                    logger.warning(
                        f"🚫 Would create duplicate: {len(similar_files)} similar files exist"
                    )
                    return True

        return False

    def _is_action_pattern_repeating(self, action: str) -> bool:
        """Check if action is part of a repeating pattern"""
        if len(self.action_history) < 3:
            return False

        recent_actions = list(self.action_history)[-6:]  # Last 6 actions
        action_lower = action.lower()

        # Count similar actions in recent history
        similar_count = sum(
            1
            for h in recent_actions
            if action_lower in h.action.lower() or h.action.lower() in action_lower
        )

        return similar_count >= self.max_repeated_patterns

    async def _check_resource_availability(self) -> bool:
        """Check if system resources are available"""
        # Check disk space
        try:
            import shutil

            _, _, free = shutil.disk_usage(self.workspace_path)
            if free < 100 * 1024 * 1024:  # Less than 100MB
                return False
        except:
            pass

        # Check if too many files in workspace
        try:
            file_count = len(glob.glob(os.path.join(self.workspace_path, "*")))
            if file_count > 100:  # Too many files
                logger.warning(
                    f"⚠️ Workspace has {file_count} files - cleanup recommended"
                )
                return False
        except:
            pass

        return True

    async def _comprehensive_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of agent state"""
        if not self.task_state:
            return {"is_stuck": False}

        current_time = datetime.now()

        # Time-based analysis
        time_since_progress = (
            current_time - self.task_state.last_progress
        ).total_seconds()
        task_duration = (current_time - self.task_state.start_time).total_seconds()

        # Pattern analysis
        pattern_analysis = self._analyze_action_patterns()

        # Progress analysis
        progress_analysis = self._analyze_progress()

        # Error analysis
        error_analysis = self._analyze_errors()

        # Determine if stuck
        is_stuck = (
            time_since_progress > self.max_idle_time
            or pattern_analysis.get("has_loops", False)
            or error_analysis.get("error_rate_high", False)
            or progress_analysis.get("stalled", False)
        )

        return {
            "is_stuck": is_stuck,
            "time_since_progress": time_since_progress,
            "task_duration": task_duration,
            "progress_percentage": self.task_state.progress_percentage,
            "pattern_analysis": pattern_analysis,
            "progress_analysis": progress_analysis,
            "error_analysis": error_analysis,
            "recommendation": self._get_recommendation(
                is_stuck, pattern_analysis, progress_analysis
            ),
        }

    def _analyze_action_patterns(self) -> Dict[str, Any]:
        """Analyze action patterns for loops and inefficiencies"""
        if len(self.action_history) < 5:
            return {"has_loops": False}

        recent_actions = list(self.action_history)[-10:]
        action_sequence = [h.action for h in recent_actions]

        # Detect loops
        for i in range(len(action_sequence) - 2):
            for j in range(i + 2, len(action_sequence)):
                if action_sequence[i] == action_sequence[j]:
                    # Potential loop detected
                    loop_length = j - i
                    if loop_length <= 4:  # Short loops are problematic
                        return {
                            "has_loops": True,
                            "loop_length": loop_length,
                            "loop_action": action_sequence[i],
                        }

        return {"has_loops": False}

    def _analyze_progress(self) -> Dict[str, Any]:
        """Analyze task progress"""
        if not self.task_state:
            return {"stalled": True}

        # Check if making progress
        expected_progress = (self.task_state.step / self.task_state.max_steps) * 100
        actual_progress = self.task_state.progress_percentage

        stalled = (
            self.task_state.step == 0  # Never started
            or actual_progress < expected_progress * 0.5  # Way behind
            or len(self.task_state.deliverables) == 0  # No outputs
        )

        return {
            "stalled": stalled,
            "expected_progress": expected_progress,
            "actual_progress": actual_progress,
            "deliverables_count": len(self.task_state.deliverables),
        }

    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not self.task_state:
            return {"error_rate_high": False}

        recent_errors = [
            h
            for h in self.action_history
            if h.outcome == "error"
            and (datetime.now() - h.timestamp).total_seconds() < 300  # Last 5 minutes
        ]

        error_rate = len(recent_errors) / max(len(self.action_history), 1)

        return {
            "error_rate_high": error_rate > 0.3,  # More than 30% errors
            "recent_errors": len(recent_errors),
            "error_rate": error_rate,
        }

    def _get_recommendation(
        self, is_stuck: bool, pattern_analysis: Dict, progress_analysis: Dict
    ) -> str:
        """Get recommendation based on analysis"""
        if not is_stuck:
            return "continue"

        if pattern_analysis.get("has_loops"):
            return "break_loop"
        elif progress_analysis.get("stalled"):
            return "restart_task"
        else:
            return "change_strategy"

    async def _smart_recovery(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Implement smart recovery strategy"""
        recommendation = analysis.get("recommendation", "continue")

        if self.current_recovery_index >= len(self.recovery_strategies):
            # All strategies exhausted
            return await self._final_recovery()

        strategy = self.recovery_strategies[self.current_recovery_index]
        self.current_recovery_index += 1

        logger.info(f"🔧 Applying recovery strategy: {strategy}")

        recovery_actions = {
            "simplify_task": self._simplify_current_task,
            "change_approach": self._change_approach,
            "skip_current_step": self._skip_current_step,
            "restart_phase": self._restart_current_phase,
            "complete_with_partial": self._complete_with_partial_results,
        }

        action_func = recovery_actions.get(strategy, self._default_recovery)
        return await action_func()

    async def _simplify_current_task(self) -> Dict[str, Any]:
        """Simplify the current task"""
        if self.task_state:
            self.task_state.max_steps = max(3, self.task_state.max_steps // 2)

        return {
            "strategy": "simplify_task",
            "action": "Break current task into smaller, simpler steps",
            "message": "Task simplified to reduce complexity",
        }

    async def _change_approach(self) -> Dict[str, Any]:
        """Change the current approach"""
        return {
            "strategy": "change_approach",
            "action": "Try alternative method or tool",
            "message": "Switching to alternative approach",
        }

    async def _skip_current_step(self) -> Dict[str, Any]:
        """Skip the current step if non-critical"""
        if self.task_state:
            self.task_state.step += 1
            self._update_progress()

        return {
            "strategy": "skip_current_step",
            "action": "Move to next step",
            "message": "Skipped current step as non-critical",
        }

    async def _restart_current_phase(self) -> Dict[str, Any]:
        """Restart the current phase"""
        if self.task_state:
            self.task_state.step = max(0, self.task_state.step - 2)
            self.task_state.last_progress = datetime.now()

        # Clear recent action history
        if len(self.action_history) > 5:
            for _ in range(5):
                self.action_history.pop()

        return {
            "strategy": "restart_phase",
            "action": "Restart current phase with fresh approach",
            "message": "Phase restarted with clean state",
        }

    async def _complete_with_partial_results(self) -> Dict[str, Any]:
        """Complete task with current partial results"""
        if self.task_state:
            self.task_state.progress_percentage = 100.0

        return {
            "strategy": "complete_with_partial",
            "action": "Mark task as complete with current results",
            "message": "Task completed with available partial results",
        }

    async def _default_recovery(self) -> Dict[str, Any]:
        """Default recovery when other strategies fail"""
        return {
            "strategy": "default",
            "action": "Apply generic recovery measures",
            "message": "Applied default recovery strategy",
        }

    async def _final_recovery(self) -> Dict[str, Any]:
        """Final recovery when all strategies are exhausted"""
        logger.error(
            "🚨 All recovery strategies exhausted - requesting manual intervention"
        )

        return {
            "strategy": "manual_intervention",
            "action": "Request human assistance",
            "message": "All automated recovery attempts failed - manual intervention required",
            "requires_human": True,
        }

    def _is_circuit_broken(self) -> bool:
        """Check if circuit breaker is active"""
        if self.circuit_breaker_count >= self.circuit_breaker_threshold:
            if self.last_circuit_break:
                time_since_break = (
                    datetime.now() - self.last_circuit_break
                ).total_seconds()
                return time_since_break < self.circuit_breaker_cooldown
            return True
        return False

    async def _handle_circuit_breaker(self, action: str) -> Dict[str, Any]:
        """Handle circuit breaker activation"""
        logger.warning("🔌 Circuit breaker active - preventing action execution")

        return {
            "status": "circuit_breaker",
            "message": "Too many failures - circuit breaker active",
            "cooldown_remaining": self.circuit_breaker_cooldown,
            "action_blocked": action,
        }

    async def _handle_action_error(
        self, action: str, error: Exception, duration: float
    ) -> Dict[str, Any]:
        """Handle action execution errors"""
        self.circuit_breaker_count += 1

        if self.circuit_breaker_count >= self.circuit_breaker_threshold:
            self.last_circuit_break = datetime.now()

        if self.task_state:
            self.task_state.errors.append(str(error))

        self._record_action(action, "error", duration, str(error))

        return {
            "status": "error",
            "error": str(error),
            "duration": duration,
            "circuit_breaker_count": self.circuit_breaker_count,
        }

    def _record_action(self, action: str, outcome: str, duration: float, output: str):
        """Record action in history"""
        history_entry = ActionHistory(
            action=action,
            timestamp=datetime.now(),
            outcome=outcome,
            duration=duration,
            output_snippet=output[:200],
        )
        self.action_history.append(history_entry)

    def _update_progress(self):
        """Update task progress"""
        if self.task_state:
            self.task_state.step += 1
            self.task_state.progress_percentage = min(
                100.0, (self.task_state.step / self.task_state.max_steps) * 100
            )
            self.task_state.last_progress = datetime.now()

    async def _cleanup_old_files(self):
        """Clean up old duplicate files"""
        now = datetime.now()

        # Only cleanup if it's been a while since last cleanup
        if (now - self.file_tracker.last_cleanup).total_seconds() < 3600:  # 1 hour
            return

        try:
            # Find potential duplicate files
            all_files = glob.glob(os.path.join(self.workspace_path, "analysis_*.md"))

            # Group by base pattern
            file_groups = defaultdict(list)
            for file_path in all_files:
                basename = os.path.basename(file_path)
                # Extract base pattern (remove timestamp)
                base_pattern = "_".join(basename.split("_")[:-2])  # Remove date/time
                file_groups[base_pattern].append(file_path)

            # Remove duplicates, keep the most recent
            for pattern, files in file_groups.items():
                if len(files) > 1:
                    # Sort by modification time, keep the newest
                    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
                    files_to_remove = files[1:]  # Remove all but the newest

                    for file_path in files_to_remove:
                        try:
                            os.remove(file_path)
                            logger.info(
                                f"🗑️ Cleaned up duplicate file: {os.path.basename(file_path)}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to remove {file_path}: {e}")

            self.file_tracker.last_cleanup = now

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        if not self.task_state:
            return {"status": "no_active_task"}

        current_time = datetime.now()

        return {
            "task_name": self.task_state.task_name,
            "progress_percentage": self.task_state.progress_percentage,
            "current_step": self.task_state.step,
            "max_steps": self.task_state.max_steps,
            "task_duration": (
                current_time - self.task_state.start_time
            ).total_seconds(),
            "time_since_progress": (
                current_time - self.task_state.last_progress
            ).total_seconds(),
            "circuit_breaker_count": self.circuit_breaker_count,
            "circuit_breaker_active": self._is_circuit_broken(),
            "recent_actions": len(self.action_history),
            "error_count": len(self.task_state.errors),
            "deliverables": len(self.task_state.deliverables),
            "health_status": self._get_health_status(),
        }

    def _get_health_status(self) -> str:
        """Get overall health status"""
        if not self.task_state:
            return "unknown"

        current_time = datetime.now()
        time_since_progress = (
            current_time - self.task_state.last_progress
        ).total_seconds()

        if self._is_circuit_broken():
            return "critical"
        elif time_since_progress > 300:  # 5 minutes
            return "warning"
        elif len(self.task_state.errors) > 3:
            return "warning"
        else:
            return "healthy"

    async def force_reset(self):
        """Force reset monitor state"""
        self.task_state = None
        self.action_history.clear()
        self.circuit_breaker_count = 0
        self.last_circuit_break = None
        self.current_recovery_index = 0
        self.file_tracker = FileTracker()

        logger.info("🔄 Smart monitor forcibly reset")
