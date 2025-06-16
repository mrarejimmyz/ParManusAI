"""
GPU Memory Monitoring and Management

Handles memory tracking, monitoring, and optimization operations.
"""

import gc
import threading
import time
from typing import Any, Dict, List, Optional

from app.gpu.types import GPUMemoryInfo, GPUState
from app.logger import logger


class GPUMemoryMonitor:
    """Handles GPU memory monitoring and tracking."""

    def __init__(self, monitoring_interval: float = 5.0):
        self.monitoring_interval = monitoring_interval
        self.memory_history: List[GPUMemoryInfo] = []
        self.max_history_size = 100
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self._lock = threading.Lock()

    def get_memory_info(self, device: int = None) -> GPUMemoryInfo:
        """
        Get current GPU memory information.

        Args:
            device: GPU device ID (None for primary device)

        Returns:
            GPUMemoryInfo: Current memory information
        """
        try:
            # Method 1: PyTorch
            try:
                import torch

                if torch.cuda.is_available():
                    if device is None:
                        device = 0

                    torch.cuda.synchronize(device)

                    # Get memory stats in bytes, convert to GB
                    memory_stats = torch.cuda.memory_stats(device)

                    total_memory = torch.cuda.get_device_properties(
                        device
                    ).total_memory / (1024**3)
                    allocated_memory = torch.cuda.memory_allocated(device) / (1024**3)
                    reserved_memory = torch.cuda.memory_reserved(device) / (1024**3)
                    free_memory = total_memory - reserved_memory
                    used_memory = allocated_memory
                    utilization = (
                        allocated_memory / total_memory if total_memory > 0 else 0.0
                    )

                    return GPUMemoryInfo(
                        total=total_memory,
                        used=used_memory,
                        free=free_memory,
                        allocated=allocated_memory,
                        reserved=reserved_memory,
                        utilization=utilization,
                        timestamp=time.time(),
                    )
            except ImportError:
                pass

            # Method 2: nvidia-ml-py (if available)
            try:
                import pynvml

                pynvml.nvmlInit()
                if device is None:
                    device = 0

                handle = pynvml.nvmlDeviceGetHandleByIndex(device)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                total_memory = mem_info.total / (1024**3)
                used_memory = mem_info.used / (1024**3)
                free_memory = mem_info.free / (1024**3)
                utilization = used_memory / total_memory if total_memory > 0 else 0.0

                return GPUMemoryInfo(
                    total=total_memory,
                    used=used_memory,
                    free=free_memory,
                    allocated=used_memory,  # Approximation
                    reserved=used_memory,  # Approximation
                    utilization=utilization,
                    timestamp=time.time(),
                )
            except ImportError:
                pass

            # Fallback: Return default/empty values
            logger.warning(
                "⚠️ Could not get GPU memory info - no monitoring library available"
            )
            return GPUMemoryInfo(
                total=0.0,
                used=0.0,
                free=0.0,
                allocated=0.0,
                reserved=0.0,
                utilization=0.0,
                timestamp=time.time(),
            )

        except Exception as e:
            logger.error(f"❌ Error getting GPU memory info: {e}")
            return GPUMemoryInfo(
                total=0.0,
                used=0.0,
                free=0.0,
                allocated=0.0,
                reserved=0.0,
                utilization=0.0,
                timestamp=time.time(),
            )

    def start_monitoring(self):
        """Start background memory monitoring."""
        if self.monitoring_active:
            logger.warning("⚠️ GPU monitoring already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self.monitoring_thread.start()
        logger.info(
            f"🔍 Started GPU memory monitoring (interval: {self.monitoring_interval}s)"
        )

    def stop_monitoring(self):
        """Stop background memory monitoring."""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
        logger.info("🛑 Stopped GPU memory monitoring")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                memory_info = self.get_memory_info()

                with self._lock:
                    self.memory_history.append(memory_info)

                    # Limit history size
                    if len(self.memory_history) > self.max_history_size:
                        self.memory_history = self.memory_history[
                            -self.max_history_size :
                        ]

                # Log high memory usage
                if memory_info.utilization > 0.8:
                    logger.warning(
                        f"⚠️ High GPU memory usage: {memory_info.utilization:.1%} "
                        f"({memory_info.used:.1f}GB / {memory_info.total:.1f}GB)"
                    )

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"❌ Error in GPU monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def cleanup_memory(self, force: bool = False) -> bool:
        """
        Clean up GPU memory.

        Args:
            force: Force aggressive cleanup

        Returns:
            bool: True if cleanup was performed
        """
        try:
            logger.info("🧹 Performing GPU memory cleanup...")

            # Python garbage collection
            gc.collect()

            # PyTorch cleanup
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    logger.info("✅ PyTorch GPU cache cleared")
            except ImportError:
                pass

            # Force additional cleanup if requested
            if force:
                try:
                    import torch

                    if torch.cuda.is_available():
                        # Clear all caches
                        for device in range(torch.cuda.device_count()):
                            torch.cuda.set_device(device)
                            torch.cuda.empty_cache()
                            torch.cuda.synchronize()
                        logger.info("✅ Aggressive GPU cleanup completed")
                except ImportError:
                    pass

            return True

        except Exception as e:
            logger.error(f"❌ Error during GPU cleanup: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.

        Returns:
            Dict with memory statistics
        """
        with self._lock:
            if not self.memory_history:
                return {"status": "no_data"}

            recent_info = self.memory_history[-1]

            # Calculate averages over recent history
            recent_history = self.memory_history[-10:]  # Last 10 readings
            avg_utilization = sum(info.utilization for info in recent_history) / len(
                recent_history
            )
            peak_utilization = max(info.utilization for info in recent_history)

            return {
                "current_memory_gb": recent_info.used,
                "total_memory_gb": recent_info.total,
                "current_utilization": recent_info.utilization,
                "average_utilization": avg_utilization,
                "peak_utilization": peak_utilization,
                "memory_efficiency": (
                    1.0 - (recent_info.free / recent_info.total)
                    if recent_info.total > 0
                    else 0.0
                ),
                "last_updated": recent_info.timestamp,
                "monitoring_active": self.monitoring_active,
                "history_size": len(self.memory_history),
            }
