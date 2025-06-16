"""
Modern GPU Manager - Refactored and Optimized

A clean, modular GPU management system with separated concerns.
"""

import time
from typing import Any, Dict, List, Optional

from app.gpu.detector import GPUDetector
from app.gpu.monitor import GPUMemoryMonitor
from app.gpu.optimizer import GPUModelOptimizer
from app.gpu.types import GPUConfig, GPUMemoryInfo, GPUState, ModelMemoryProfile
from app.logger import logger


class GPUManager:
    """
    Modern GPU Manager with modular design.

    Combines detection, monitoring, and optimization in a clean interface.
    """

    def __init__(self, config: Optional[GPUConfig] = None):
        """
        Initialize GPU manager with configuration.

        Args:
            config: GPU configuration parameters
        """
        self.config = config or GPUConfig()

        # Initialize components
        self.detector = GPUDetector()
        self.monitor = GPUMemoryMonitor(self.config.monitoring_interval)
        self.optimizer = GPUModelOptimizer(self.config.memory_threshold)

        # GPU state
        self.cuda_available = self._initialize_cuda()
        self.device_count = (
            self.detector.get_device_count() if self.cuda_available else 0
        )
        self.primary_device = 0

        logger.info(
            f"🚀 GPU Manager initialized - CUDA: {self.cuda_available}, Devices: {self.device_count}"
        )

    def _initialize_cuda(self) -> bool:
        """Initialize CUDA detection with configuration overrides."""
        cuda_detected = self.detector.check_cuda_availability()

        if self.config.force_cuda and not cuda_detected:
            logger.warning("⚠️ Force CUDA enabled - overriding detection failure")
            return True

        return cuda_detected

    # === Public Interface ===

    def get_state(self) -> GPUState:
        """Get current GPU state."""
        if not self.cuda_available:
            return GPUState.ERROR

        try:
            memory_info = self.get_memory_info()

            if memory_info.utilization < 0.3:
                return GPUState.AVAILABLE
            elif memory_info.utilization < 0.8:
                return GPUState.BUSY
            else:
                return GPUState.OVERLOADED

        except Exception:
            return GPUState.ERROR

    def get_memory_info(self, device: int = None) -> GPUMemoryInfo:
        """Get current GPU memory information."""
        return self.monitor.get_memory_info(device or self.primary_device)

    def start_monitoring(self):
        """Start background memory monitoring."""
        self.monitor.start_monitoring()

    def stop_monitoring(self):
        """Stop background memory monitoring."""
        self.monitor.stop_monitoring()

    def cleanup_memory(self, force: bool = False) -> bool:
        """Clean up GPU memory."""
        return self.monitor.cleanup_memory(force)

    # === Model Optimization ===

    def optimize_gpu_layers(self, model_path: str, force_layers: int = None) -> int:
        """
        Get optimal GPU layers for a model.

        Args:
            model_path: Path to model file
            force_layers: Override with specific layer count

        Returns:
            int: Optimal number of GPU layers
        """
        if not self.cuda_available:
            return 0

        if force_layers is not None:
            return force_layers

        try:
            model_size = self.optimizer.estimate_model_size(model_path)
            memory_info = self.get_memory_info()

            return self.optimizer.calculate_optimal_layers(
                model_size, memory_info.free, self.config.force_gpu_layers
            )

        except Exception as e:
            logger.error(f"❌ Error optimizing GPU layers: {e}")
            return self.config.force_gpu_layers

    def should_use_gpu(self, model_path: str) -> bool:
        """Determine if GPU should be used for a model."""
        if not self.cuda_available:
            return False

        try:
            model_size = self.optimizer.estimate_model_size(model_path)
            memory_info = self.get_memory_info()

            return self.optimizer.should_use_gpu(model_size, memory_info)

        except Exception as e:
            logger.error(f"❌ Error determining GPU usage: {e}")
            return False

    def can_allocate(self, required_memory_gb: float) -> bool:
        """Check if required memory can be allocated."""
        if not self.cuda_available:
            return False

        try:
            memory_info = self.get_memory_info()
            return self.optimizer.can_allocate(required_memory_gb, memory_info)

        except Exception as e:
            logger.error(f"❌ Error checking allocation: {e}")
            return False

    def profile_model_loading(
        self, model_path: str, gpu_layers: int
    ) -> ModelMemoryProfile:
        """Profile model loading performance."""
        return self.optimizer.profile_model_loading(
            model_path, gpu_layers, self.monitor
        )

    def optimize_for_models(self, model_paths: List[str]) -> Dict[str, int]:
        """Optimize GPU allocation for multiple models."""
        if not self.cuda_available:
            return {path: 0 for path in model_paths}

        try:
            memory_info = self.get_memory_info()
            return self.optimizer.optimize_for_models(model_paths, memory_info.free)

        except Exception as e:
            logger.error(f"❌ Error in multi-model optimization: {e}")
            return {path: 0 for path in model_paths}

    # === Statistics and Info ===

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive GPU statistics."""
        base_stats = {
            "cuda_available": self.cuda_available,
            "device_count": self.device_count,
            "state": self.get_state().value,
            "config": {
                "memory_threshold": self.config.memory_threshold,
                "cleanup_threshold": self.config.cleanup_threshold,
                "monitoring_interval": self.config.monitoring_interval,
                "force_cuda": self.config.force_cuda,
                "force_gpu_layers": self.config.force_gpu_layers,
            },
        }

        if self.cuda_available:
            memory_stats = self.monitor.get_statistics()
            base_stats.update(memory_stats)

            # Add device info
            device_name = self.detector.get_device_name(self.primary_device)
            if device_name:
                base_stats["device_name"] = device_name

        return base_stats

    def get_gpu_memory_info(self) -> Dict[str, float]:
        """Get simplified memory info for backward compatibility."""
        if not self.cuda_available:
            return {
                "total_memory": 0.0,
                "used_memory": 0.0,
                "free_memory": 0.0,
                "utilization": 0.0,
            }

        memory_info = self.get_memory_info()
        return {
            "total_memory": memory_info.total,
            "used_memory": memory_info.used,
            "free_memory": memory_info.free,
            "utilization": memory_info.utilization,
        }

    # === Cleanup ===

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.stop_monitoring()
        except:
            pass


# === Backward Compatibility ===


class CUDAGPUManager(GPUManager):
    """Backward compatibility alias for the old GPU manager."""

    def __init__(
        self,
        memory_threshold: float = 0.8,
        cleanup_threshold: float = 0.9,
        monitoring_interval: float = 5.0,
        force_cuda: bool = False,
        force_gpu_layers: int = 0,
    ):
        """Initialize with old parameter style."""
        config = GPUConfig(
            memory_threshold=memory_threshold,
            cleanup_threshold=cleanup_threshold,
            monitoring_interval=monitoring_interval,
            force_cuda=force_cuda,
            force_gpu_layers=force_gpu_layers,
        )
        super().__init__(config)

    # Legacy method aliases
    def _check_cuda_availability(self) -> bool:
        return self.cuda_available

    def _get_device_count(self) -> int:
        return self.device_count

    def estimate_model_size(self, model_path: str) -> float:
        return self.optimizer.estimate_model_size(model_path)

    def calculate_optimal_layers(
        self,
        model_size_gb: float,
        available_memory_gb: float,
        safety_margin: float = 0.15,
        force_gpu_layers: int = 0,
    ) -> int:
        return self.optimizer.calculate_optimal_layers(
            model_size_gb, available_memory_gb, force_gpu_layers
        )
