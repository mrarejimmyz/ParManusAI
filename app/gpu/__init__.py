"""
GPU Management Module

Modular GPU management system with separated concerns:
- Detection: CUDA detection and device enumeration
- Monitoring: Memory tracking and performance monitoring
- Optimization: Model memory optimization and layer calculation
- Manager: Main interface coordinating all components
"""

from .detector import GPUDetector
from .manager import CUDAGPUManager, GPUManager
from .monitor import GPUMemoryMonitor
from .optimizer import GPUModelOptimizer
from .types import GPUConfig, GPUMemoryInfo, GPUState, ModelMemoryProfile

__all__ = [
    "GPUManager",
    "CUDAGPUManager",  # Backward compatibility
    "GPUDetector",
    "GPUMemoryMonitor",
    "GPUModelOptimizer",
    "GPUConfig",
    "GPUMemoryInfo",
    "GPUState",
    "ModelMemoryProfile",
]
