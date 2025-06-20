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
from .monitoring import (
    ActionHistory,
    FileManager,
    FileTracker,
    PatternDetector,
    ProgressAnalyzer,
    RecoveryManager,
    StatusReporter,
    TaskState,
    TimeoutManager,
)


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

        # Core tracking
        self.action_history: deque = deque(maxlen=50)
        self.task_state: Optional[TaskState] = None
        self.current_recovery_index = 0        # Configuration
        self.max_action_time = 120.0
        self.max_idle_time = 300.0
        self.min_actions_before_stuck_check = 8  # Increased from 3 to be less aggressive

        logger.info("🔧 Smart Agent Monitor initialized with modular components")

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

    async def monitor_action(self, action: str, timeout: float = None) -> Dict[str, Any]:
        """Monitor action execution with intelligent features"""
        if not self.task_state:
            await self.start_task("default_task")

        # Check circuit breaker
        if self.recovery_manager._is_circuit_broken():
            return await self.recovery_manager._handle_circuit_breaker_recovery()

        # Check for file duplicate prevention
        topic_keywords = self.pattern_detector.extract_topic_from_action(action.lower())
        if self.file_manager.should_prevent_duplicate(topic_keywords):
            logger.warning(f"🚫 Preventing duplicate file creation for topics: {topic_keywords}")
            return {
                "status": "duplicate_prevention",
                "message": f"Prevented duplicate creation for topics: {topic_keywords}",
                "topics": topic_keywords,
            }

        # Calculate smart timeout
        smart_timeout = timeout or self.timeout_manager.calculate_smart_timeout(
            action, self.max_action_time
        )

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
                self.file_manager.track_file_creation(f"simulated_file_{len(self.action_history)}.md", topic_keywords)
            
            # Update progress
            self.status_reporter.update_progress(self.task_state)
              # Reset circuit breaker on success
            self.recovery_manager.circuit_breaker_count = 0
            
            return {
                "status": "success",
                "result": result,
                "duration": duration,
                "smart_timeout_used": smart_timeout,
            }

        except asyncio.TimeoutError:
            duration = smart_timeout
            return await self.timeout_manager.handle_smart_timeout(action, smart_timeout)

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return await self.recovery_manager.handle_action_error(
                action, e, duration, self.task_state
            )

    async def _simulate_action_execution(self, action: str, timeout: float) -> str:
        """Simulate action execution for testing"""
        # Simulate some processing time
        await asyncio.sleep(min(0.1, timeout / 10))
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
            and action_count % 5 == 0  # Check every 5 actions instead of 3
        )

    async def _analyze_stuck_state(self) -> Dict[str, Any]:
        """Analyze if agent is stuck"""
        # Get pattern analysis
        pattern_analysis = self.pattern_detector.analyze_action_patterns(self.action_history)
        
        # Get comprehensive analysis
        analysis = self.progress_analyzer.comprehensive_analysis(
            self.task_state,
            self.action_history,
            pattern_analysis,
            self.min_actions_before_stuck_check
        )
        
        # Add recommendation
        recommendation = self.progress_analyzer.get_recommendation(
            analysis["is_stuck"],
            pattern_analysis,
            analysis["progress_analysis"]
        )
        analysis["recommendation"] = recommendation
        
        return analysis

    async def _handle_stuck_state(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle detected stuck state"""
        logger.warning("🔄 Stuck state detected, applying recovery")
        
        recovery_result = await self.recovery_manager.smart_recovery(analysis, self.task_state)
        
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
            self.recovery_manager._is_circuit_broken()
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

    # Legacy compatibility methods
    async def monitor_with_timeout(self, action: str, timeout: float = None) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        return await self.monitor_action(action, timeout)

    def is_stuck(self) -> bool:
        """Legacy stuck detection method"""
        if len(self.action_history) < self.min_actions_before_stuck_check:
            return False
        
        # Simple pattern check for backward compatibility
        return self.pattern_detector.is_action_pattern_repeating(
            self.action_history[-1].action if self.action_history else "",
            self.action_history
        )
