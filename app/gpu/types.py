"""
GPU Data Structures and Enums

Defines core data structures and enumerations for GPU management.
"""

from dataclasses import dataclass
from enum import Enum


class GPUState(Enum):
    """GPU state enumeration."""

    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    ERROR = "error"


@dataclass
class GPUMemoryInfo:
    """GPU memory information structure."""

    total: float  # Total GPU memory in GB
    used: float  # Used GPU memory in GB
    free: float  # Free GPU memory in GB
    allocated: float  # Allocated by current process in GB
    reserved: float  # Reserved by current process in GB
    utilization: float  # Memory utilization ratio (0-1)
    timestamp: float  # Timestamp of measurement


@dataclass
class ModelMemoryProfile:
    """Memory profile for a model."""

    model_path: str
    estimated_size: float  # Estimated size in GB
    actual_size: float  # Actual loaded size in GB
    optimal_layers: int  # Optimal number of GPU layers
    load_time: float  # Time taken to load
    performance_score: float  # Performance score (0-1)


@dataclass
class GPUConfig:
    """GPU configuration parameters."""

    memory_threshold: float = 0.8
    cleanup_threshold: float = 0.9
    monitoring_interval: float = 5.0
    force_cuda: bool = False
    force_gpu_layers: int = 0
