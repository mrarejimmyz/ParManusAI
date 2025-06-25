"""
Advanced Smart Agent Monitor - Refactored Version
Comprehensive monitoring system using modular components for:
- Timeout management
- Pattern detection
- Progress analysis
- Recovery strategies
- File management
- Status reporting
"""

import asyncio
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.logger import logger

from .monitoring import (ActionHistory, FileManager, FileTracker,
                         PatternDetector, ProgressAnalyzer, RecoveryManager,
                         StatusReporter, TaskState, TimeoutManager)


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

        # Initialize modular components
        self.timeout_manager = TimeoutManager()
        self.pattern_detector = PatternDetector(workspace_path)
        self.progress_analyzer = ProgressAnalyzer()
        self.recovery_manager = RecoveryManager()
        self.file_manager = FileManager(workspace_path)
        self.status_reporter = StatusReporter()

        # Core tracking - enhanced for speed optimization
        self.action_history: deque = deque(maxlen=200)  # Increased for better learning
        self.task_state: Optional[TaskState] = None
        self.current_recovery_index = 0

        # Performance optimization - continuously improve speeds
        self.max_action_time = 25.0  # Start more aggressive, will adapt down
        self.max_idle_time = 60.0  # Reduced significantly for faster response
        self.max_task_duration = 600.0  # 10 minutes max, optimize for speed
        self.max_recovery_attempts = 3  # Faster failure recovery, less waiting
        self.min_actions_before_stuck_check = 5  # Check more frequently for speed

        # Speed optimization tracking - enhanced
        self.performance_metrics = {
            "average_action_time": 20.0,  # Start with optimistic baseline
            "fastest_action_time": float('inf'),
            "success_rate": 1.0,
            "optimization_factor": 1.0,
            "speed_improvements": 0,
            "performance_trend": []  # Track improvement over time
        }

        # Rolling performance metrics for real-time optimization
        self.rolling_durations = deque(maxlen=20)  # Last 20 actions for fast adaptation
        self.stuck_detection_threshold = 3  # Lower threshold for faster stuck detection

        # Continuous learning integration
        from app.agent_learning import agent_learning
        self.learning_system = agent_learning

        # Load learned performance optimizations
        self._load_performance_optimizations()

        logger.info("⚡ Smart Agent Monitor initialized with enhanced speed optimization and continuous learning")

    async def start_task(self, task_name: str, max_steps: int = 10):
        """Start monitoring a new task"""
        self.task_state = TaskState(
            task_name=task_name,
            start_time=datetime.now(),
            last_progress=datetime.now(),
            max_steps=max_steps,
        )

        self.action_history.clear()
        self.current_recovery_index = 0

        logger.info(f"📋 Started monitoring task: {task_name}")

    async def monitor_action(
        self, action: str, timeout: float = None
    ) -> Dict[str, Any]:
        """Monitor action execution with intelligent features"""
        if not self.task_state:
            await self.start_task("default_task")

        # Check circuit breaker
        if self.recovery_manager._is_circuit_broken():
            return (
                await self.recovery_manager._handle_circuit_breaker_recovery()
            )  # Check for file duplicate prevention
        action_str = str(action) if not isinstance(action, str) else action
        topic_keywords = self.pattern_detector.extract_topic_from_action(
            action_str.lower()
        )
        if self.file_manager.should_prevent_duplicate(topic_keywords):
            logger.warning(
                f"🚫 Preventing duplicate file creation for topics: {topic_keywords}"
            )
            return {
                "status": "duplicate_prevention",
                "message": f"Prevented duplicate creation for topics: {topic_keywords}",
                "topics": topic_keywords,
            }

        # Calculate smart timeout with performance optimization
        base_timeout = timeout or self.timeout_manager.calculate_smart_timeout(
            action, self.max_action_time
        )

        # Apply intelligent preemptive optimization
        smart_timeout = await self._intelligent_preemptive_optimization(action)
        if timeout is None:
            smart_timeout = min(smart_timeout, base_timeout)

        # Check for stuck state before action
        if await self._should_check_stuck_state():
            stuck_analysis = await self._analyze_stuck_state()
            if stuck_analysis["is_stuck"]:
                return await self._handle_stuck_state(stuck_analysis)

        # Record action start
        start_time = datetime.now()

        try:
            # This is where the actual action would be executed
            # For now, we just simulate and return success
            result = await self._simulate_action_execution(action, smart_timeout)

            duration = (datetime.now() - start_time).total_seconds()

            # Record successful action
            self.status_reporter.record_action(
                action, "success", duration, str(result), self.action_history
            )

            # Track file if one was created
            if "file" in str(result).lower():
                self.file_manager.track_file_creation(
                    f"simulated_file_{len(self.action_history)}.md", topic_keywords
                )  # Update progress
            self.status_reporter.update_progress(self.task_state)
            # Reset circuit breaker on success
            self.recovery_manager.circuit_breaker_count = 0

            # Optimize performance based on this action's success
            await self._optimize_performance_continuously(action, duration, True)

            # Learn from successful execution patterns
            await self._learn_from_successful_execution(action, result, duration)

            # Optimize performance based on this action's success
            await self._optimize_performance_continuously(action, duration, True)

            return {
                "status": "success",
                "result": result,
                "duration": duration,
                "smart_timeout_used": smart_timeout,
            }

        except asyncio.TimeoutError:
            duration = smart_timeout
            return await self.timeout_manager.handle_smart_timeout(
                action, smart_timeout
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            # Learn from error for faster future recovery
            await self._adaptive_error_learning(action, e, duration)

            return await self.recovery_manager.handle_action_error(
                action, e, duration, self.task_state
            )

    async def monitor_with_aggressive_timeout(self, action: str, timeout: float = 30.0):
        """Monitor action with aggressive timeout enforcement"""
        try:
            # Force maximum timeout of 30 seconds
            max_timeout = min(timeout, 30.0)
            result = await asyncio.wait_for(
                self._execute_action_fast(action), timeout=max_timeout
            )
            return {
                "status": "success",
                "result": result,
                "duration": max_timeout,
                "timeout_enforced": True,
            }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "result": f"Action '{action}' timed out after {max_timeout}s",
                "duration": max_timeout,
                "timeout_enforced": True,
            }

    async def _execute_action_fast(self, action: str) -> str:
        """Fast action execution without delays"""
        # Simulate fast execution for testing
        await asyncio.sleep(0.1)  # Minimal delay
        return f"Fast execution of: {action}"

    async def _simulate_action_execution(self, action: str, timeout: float) -> str:
        """Simulate action execution for testing - FIXED: Remove artificial delays that cause timeouts"""
        # REMOVED: Artificial sleep that was causing timeouts
        # await asyncio.sleep(min(0.1, timeout / 10))

        # Return immediately for testing to prevent timeout issues
        return f"Executed: {action}"

    async def _should_check_stuck_state(self) -> bool:
        """Determine if we should check for stuck state"""
        action_count = len(self.action_history)

        # Don't check until we have some history
        if action_count < self.min_actions_before_stuck_check:
            return False

        # Check periodically - every 5 actions after minimum
        # Only if we have enough actions and it's a check interval
        return (
            action_count >= self.min_actions_before_stuck_check
            and action_count % 10
            == 0  # Check every 10 actions to reduce over-triggering
        )

    async def _analyze_stuck_state(self) -> Dict[str, Any]:
        """Analyze if agent is stuck"""
        # Get pattern analysis
        pattern_analysis = self.pattern_detector.analyze_action_patterns(
            self.action_history
        )

        # Get comprehensive analysis
        analysis = self.progress_analyzer.comprehensive_analysis(
            self.task_state,
            self.action_history,
            pattern_analysis,
            self.min_actions_before_stuck_check,
        )

        # Add recommendation
        recommendation = self.progress_analyzer.get_recommendation(
            analysis["is_stuck"], pattern_analysis, analysis["progress_analysis"]
        )
        analysis["recommendation"] = recommendation

        return analysis

    async def _handle_stuck_state(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle detected stuck state with termination checks"""
        logger.warning("🔄 Stuck state detected, applying recovery")

        # Check if we should terminate instead of recovering
        if self._should_terminate_task(analysis):
            logger.warning(
                "🛑 Task termination triggered - too many recovery attempts or time exceeded"
            )
            return {
                "status": "task_terminated",
                "reason": "max_recovery_attempts_exceeded_or_timeout",
                "analysis": analysis,
                "recovery_attempts": self.current_recovery_index,
                "message": "Task terminated due to excessive recovery attempts or timeout",
            }

        recovery_result = await self.recovery_manager.smart_recovery(
            analysis, self.task_state
        )

        # Update recovery index
        self.current_recovery_index += 1

        return {
            "status": "stuck_recovery",
            "analysis": analysis,
            "recovery": recovery_result,
            "recovery_attempt": self.current_recovery_index,
        }

    async def cleanup_workspace(self):
        """Clean up workspace files"""
        await self.file_manager.cleanup_duplicate_files()

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return self.status_reporter.get_status_report(
            self.task_state,
            self.action_history,
            self.recovery_manager.circuit_breaker_count,
            self.recovery_manager._is_circuit_broken(),
        )

    async def force_reset(self):
        """Force reset monitor state"""
        self.task_state = None
        self.action_history.clear()
        self.recovery_manager.circuit_breaker_count = 0
        self.recovery_manager.last_circuit_break = None
        self.current_recovery_index = 0
        self.file_manager.file_tracker = FileTracker()

        logger.info("🔄 Smart monitor forcibly reset")

    def _should_terminate_task(self, analysis: Dict[str, Any]) -> bool:
        """Check if task should be terminated instead of recovered"""
        # Terminate if too many recovery attempts
        if self.current_recovery_index >= self.max_recovery_attempts:
            return True

        # Terminate if task has been running too long
        if self.task_state and self.task_state.start_time:
            duration = (datetime.now() - self.task_state.start_time).total_seconds()
            if duration > self.max_task_duration:
                return True

        # Terminate if pattern analysis shows excessive looping
        pattern_analysis = analysis.get("pattern_analysis", {})
        if pattern_analysis.get("pattern_strength", 0) > 25:
            return True

        return False

    def _load_performance_optimizations(self):
        """Load learned performance optimizations to start faster"""
        try:
            # Get optimal timeouts from learning system
            timeout_opts = self.learning_system.get_user_preference("optimal_timeouts", {})
            if timeout_opts:
                self.max_action_time = min(timeout_opts.get("action", 25.0), 25.0)  # Cap at 25s for speed
                self.max_idle_time = min(timeout_opts.get("idle", 60.0), 60.0)  # Cap at 60s for speed
                logger.info(f"🏃 Loaded optimized timeouts: action={self.max_action_time}s, idle={self.max_idle_time}s")

            # Get performance metrics from previous sessions
            perf_opts = self.learning_system.get_user_preference("performance_metrics", {})
            if perf_opts:
                self.performance_metrics.update(perf_opts)
                logger.info(f"📊 Loaded performance baseline: {self.performance_metrics['average_action_time']:.1f}s avg")

            # Load learned workflow patterns for instant optimization
            workflow_patterns = self.learning_system.get_workflow_patterns()
            fast_patterns = {k: v for k, v in workflow_patterns.items() if v.get("pattern", {}).get("speed_rating") == "fast"}
            if fast_patterns:
                logger.info(f"⚡ Loaded {len(fast_patterns)} fast workflow patterns for instant optimization")

        except Exception as e:
            logger.warning(f"Could not load performance optimizations: {e}")

    async def _optimize_performance_continuously(self, action: str, duration: float, success: bool):
        """Continuously optimize performance based on execution data with enhanced learning"""
        # Add to rolling metrics for real-time adaptation
        self.rolling_durations.append(duration)

        # Update performance metrics
        if success and duration > 0:
            # Track fastest times for optimization
            if duration < self.performance_metrics["fastest_action_time"]:
                self.performance_metrics["fastest_action_time"] = duration
                self.performance_metrics["speed_improvements"] += 1
                logger.info(f"🏆 New speed record: {duration:.1f}s for action type")

            # Update rolling average with more responsive weighting
            current_avg = self.performance_metrics["average_action_time"]
            self.performance_metrics["average_action_time"] = (current_avg * 0.8) + (duration * 0.2)

            # Dynamically adjust timeouts based on performance - more aggressive
            if len(self.rolling_durations) >= 5:
                recent_avg = sum(self.rolling_durations) / len(self.rolling_durations)

                if recent_avg < self.max_action_time * 0.4:
                    # If consistently very fast, reduce timeout aggressively for speed
                    old_timeout = self.max_action_time
                    self.max_action_time = max(recent_avg * 2.0, 10.0)  # Min 10s, but very responsive
                    if self.max_action_time < old_timeout:
                        logger.info(f"⚡ Aggressively optimized timeout: {old_timeout:.1f}s → {self.max_action_time:.1f}s")

                elif recent_avg < self.max_action_time * 0.6:
                    # If generally fast, optimize for speed
                    old_timeout = self.max_action_time
                    self.max_action_time = max(recent_avg * 1.8, 15.0)
                    if self.max_action_time < old_timeout:
                        logger.info(f"🚀 Speed-optimized timeout: {old_timeout:.1f}s → {self.max_action_time:.1f}s")

            # Track performance trend
            self.performance_metrics["performance_trend"].append({
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "action_type": action.split()[0] if action.split() else "generic"
            })

            # Keep only last 50 trend points for memory efficiency
            if len(self.performance_metrics["performance_trend"]) > 50:
                self.performance_metrics["performance_trend"] = self.performance_metrics["performance_trend"][-50:]

            # Save optimizations for future sessions
            self.learning_system.save_user_preference("optimal_timeouts", {
                "action": self.max_action_time,
                "idle": self.max_idle_time
            })

            self.learning_system.save_user_preference("performance_metrics", self.performance_metrics)

            # Continuous learning update
            self.learning_system.continuous_learning_update(action, "success", duration, True)

    async def _intelligent_preemptive_optimization(self, action: str):
        """Preemptively optimize based on learned patterns with enhanced speed focus"""
        # Check for learned optimizations for this action type
        action_type = action.split()[0] if action.split() else "generic"
        optimizations = self.learning_system.get_tool_optimizations(action_type)

        if optimizations:
            best_opt = optimizations[0]  # Best optimization
            success_rate = best_opt.get('success_count', 0) / max(best_opt.get('usage_count', 1), 1)
            avg_duration = best_opt.get('optimization', {}).get('duration', self.max_action_time)

            if success_rate > 0.8 and avg_duration < self.max_action_time * 0.7:
                # High success rate AND fast execution - optimize aggressively for speed
                self.performance_metrics["optimization_factor"] = 0.6  # Very aggressive
                optimized_timeout = max(avg_duration * 1.5, 8.0)  # Min 8s for very fast actions
                logger.info(f"⚡ Aggressive speed optimization: {action_type} (success: {success_rate:.1%}, avg: {avg_duration:.1f}s)")
                return optimized_timeout

            elif success_rate > 0.8:
                # High success rate - optimize for speed
                self.performance_metrics["optimization_factor"] = 0.8
                optimized_timeout = max(avg_duration * 1.8, 12.0)
                logger.info(f"🚀 Speed optimization applied: {action_type} (success: {success_rate:.1%})")
                return optimized_timeout

            elif success_rate < 0.4:
                # Low success rate - optimize for reliability but still fast
                self.performance_metrics["optimization_factor"] = 1.2
                logger.info(f"🛡️ Reliability optimization applied: {action_type} (success: {success_rate:.1%})")
                return self.max_action_time * self.performance_metrics["optimization_factor"]

        # Check for predictive suggestions from learning system
        suggestions = self.learning_system.get_predictive_suggestions(action)
        if suggestions:
            for suggestion in suggestions:
                if suggestion.get("type") == "optimization" and suggestion.get("confidence", 0) > 0.8:
                    self.performance_metrics["optimization_factor"] = 0.7  # Speed focus
                    logger.info(f"💡 Predictive optimization applied: {suggestion.get('suggestion', '')}")
                    return self.max_action_time * self.performance_metrics["optimization_factor"]

        # Default with slight speed optimization
        return self.max_action_time * 0.9  # Default 10% faster

    async def _learn_from_successful_execution(self, action: str, result: Any, duration: float):
        """Learn from successful execution to optimize future performance with enhanced patterns"""
        action_type = action.split()[0] if action.split() else "generic"

        # Enhanced speed optimization data
        optimization = {
            "action": action,
            "duration": duration,
            "result_quality": "excellent" if duration < self.performance_metrics["average_action_time"] * 0.6 else
                             "high" if duration < self.performance_metrics["average_action_time"] else "normal",
            "timeout_used": self.max_action_time,
            "success": True,
            "speed_rating": "very_fast" if duration < 10.0 else "fast" if duration < 20.0 else "normal",
            "timestamp": datetime.now().isoformat(),
            "optimization_applied": self.performance_metrics.get("optimization_factor", 1.0)
        }

        self.learning_system.save_tool_optimization(f"speed_{action_type}", optimization)

        # Enhanced workflow pattern learning with speed focus
        if len(self.action_history) >= 2:
            recent_actions = [ah.action for ah in list(self.action_history)[-4:]]  # Look at more context
            recent_actions.append(action)
            recent_durations = [ah.duration for ah in list(self.action_history)[-4:]]
            recent_durations.append(duration)

            pattern_name = f"fast_workflow_{'_'.join([a.split()[0] for a in recent_actions if a])}"
            total_duration = sum(recent_durations)
            avg_duration = total_duration / len(recent_durations)

            pattern_data = {
                "actions": recent_actions,
                "durations": recent_durations,
                "total_duration": total_duration,
                "avg_duration": avg_duration,
                "speed_rating": "very_fast" if avg_duration < 15.0 else "fast" if avg_duration < 25.0 else "normal",
                "success_sequence": True,
                "pattern_length": len(recent_actions),
                "optimization_potential": "high" if avg_duration < 20.0 else "medium"
            }

            self.learning_system.save_workflow_pattern(pattern_name, pattern_data)
            logger.info(f"🔄 Enhanced workflow pattern learned: {pattern_name} (avg: {avg_duration:.1f}s, rating: {pattern_data['speed_rating']})")

        # Learn error prevention patterns
        if duration < self.performance_metrics["average_action_time"] * 0.8:
            # This was a successful fast execution - learn to prevent slowdowns
            prevention_pattern = {
                "action_pattern": action_type,
                "success_factors": {
                    "timeout_used": self.max_action_time,
                    "duration": duration,
                    "optimization_factor": self.performance_metrics.get("optimization_factor", 1.0)
                },
                "prevention_method": "speed_optimization"
            }

            self.learning_system.save_error_solution(f"prevent_slowdown_{action_type}", prevention_pattern)
            logger.info(f"🛡️ Learned speed optimization pattern for {action_type}")

    async def _adaptive_error_learning(self, action: str, error: Exception, duration: float):
        """Learn from errors to prevent future occurrences and optimize recovery with enhanced speed focus"""
        # Record performance impact of errors
        await self._optimize_performance_continuously(action, duration, False)

        # Enhanced error learning for faster recovery
        error_signature = f"{type(error).__name__}_{str(error)[:50]}".lower()

        # Save error context for faster future recovery
        error_context = {
            "action": action,
            "error_type": type(error).__name__,
            "duration_before_error": duration,
            "recovery_strategy": "fast_recovery",
            "prevention_method": "preemptive_check",
            "speed_impact": "high" if duration > self.max_action_time * 0.8 else "medium",
            "learning_priority": "high"  # Prioritize error learning for speed
        }

        self.learning_system.save_error_solution(error_signature, error_context)
        logger.info(f"🔧 Enhanced error learning: {error_signature[:30]}... (speed impact: {error_context['speed_impact']})")

        # Adjust timeouts for this action type to prevent future timeouts - more aggressive
        if "timeout" in str(error).lower():
            action_type = action.split()[0] if action.split() else "generic"
            current_timeout = self.learning_system.get_user_preference(f"timeout_{action_type}", self.max_action_time)

            # More conservative timeout increase to balance speed and reliability
            optimized_timeout = min(current_timeout * 1.3, 60.0)  # Cap at 60s, smaller increase

            self.learning_system.save_user_preference(f"timeout_{action_type}", optimized_timeout)
            logger.info(f"⏱️ Balanced timeout optimization for {action_type}: {optimized_timeout:.1f}s")

        # Continuous learning update for errors
        self.learning_system.continuous_learning_update(action, error, duration, False)

    # Legacy compatibility methods
    async def monitor_with_timeout(
        self, action: str, timeout: float = None
    ) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        return await self.monitor_action(action, timeout)

    def is_stuck(self) -> bool:
        """Legacy stuck detection method"""
        if len(self.action_history) < self.min_actions_before_stuck_check:
            return False

        # Simple pattern check for backward compatibility
        return self.pattern_detector.is_action_pattern_repeating(
            self.action_history[-1].action if self.action_history else "",
            self.action_history,
        )
