"""
GPU Model Memory Profiling and Optimization

Handles model memory estimation, layer optimization, and performance profiling.
"""

import os
import time
from typing import Dict, List, Optional

from app.gpu.types import GPUMemoryInfo, ModelMemoryProfile
from app.logger import logger


class GPUModelOptimizer:
    """Handles model memory optimization and profiling."""

    def __init__(self, memory_threshold: float = 0.8):
        self.memory_threshold = memory_threshold
        self.model_profiles: Dict[str, ModelMemoryProfile] = {}

    def estimate_model_size(self, model_path: str) -> float:
        """
        Estimate model size based on file size and format.

        Args:
            model_path: Path to the model file

        Returns:
            float: Estimated size in GB
        """
        try:
            if not os.path.exists(model_path):
                logger.warning(f"⚠️ Model file not found: {model_path}")
                return 0.0

            # Get file size
            file_size_bytes = os.path.getsize(model_path)
            file_size_gb = file_size_bytes / (1024**3)

            # Apply format-specific multipliers for memory overhead
            file_ext = os.path.splitext(model_path)[1].lower()

            if file_ext in [".gguf", ".ggml"]:
                # GGUF models are quantized, less memory overhead
                multiplier = 1.1
            elif file_ext in [".bin", ".pt", ".pth"]:
                # PyTorch models may need additional memory for optimization
                multiplier = 1.3
            elif file_ext in [".safetensors"]:
                # SafeTensors format, minimal overhead
                multiplier = 1.2
            else:
                # Unknown format, conservative estimate
                multiplier = 1.5

            estimated_size = file_size_gb * multiplier
            logger.debug(
                f"📊 Estimated memory for {os.path.basename(model_path)}: {estimated_size:.2f}GB"
            )

            return estimated_size

        except Exception as e:
            logger.error(f"❌ Error estimating model size for {model_path}: {e}")
            return 0.0

    def calculate_optimal_layers(
        self,
        model_size_gb: float,
        available_memory_gb: float,
        force_gpu_layers: int = 0,
    ) -> int:
        """
        Calculate optimal number of GPU layers based on available memory.

        Args:
            model_size_gb: Estimated model size in GB
            available_memory_gb: Available GPU memory in GB
            force_gpu_layers: Minimum forced GPU layers

        Returns:
            int: Optimal number of GPU layers
        """
        try:
            if model_size_gb <= 0:
                return force_gpu_layers

            # Reserve memory for operations and overhead
            usable_memory = available_memory_gb * self.memory_threshold

            # Estimate layers based on memory ratio
            if usable_memory >= model_size_gb:
                # Full model fits in GPU
                optimal_layers = -1  # -1 means all layers
            elif usable_memory >= model_size_gb * 0.5:
                # At least half the model fits
                ratio = usable_memory / model_size_gb
                # Estimate layers (assuming typical transformer has 32-48 layers)
                estimated_total_layers = 40  # Conservative estimate
                optimal_layers = int(estimated_total_layers * ratio)
            else:
                # Limited GPU memory, conservative approach
                optimal_layers = max(1, int(usable_memory / model_size_gb * 10))

            # Apply minimum forced layers
            if force_gpu_layers > 0:
                optimal_layers = max(optimal_layers, force_gpu_layers)

            logger.info(
                f"🧠 Optimal GPU layers: {optimal_layers} "
                f"(Model: {model_size_gb:.1f}GB, Available: {available_memory_gb:.1f}GB)"
            )

            return optimal_layers

        except Exception as e:
            logger.error(f"❌ Error calculating optimal layers: {e}")
            return force_gpu_layers

    def profile_model_loading(
        self, model_path: str, gpu_layers: int, memory_monitor
    ) -> ModelMemoryProfile:
        """
        Profile model loading performance and memory usage.

        Args:
            model_path: Path to model file
            gpu_layers: Number of GPU layers to use
            memory_monitor: GPU memory monitor instance

        Returns:
            ModelMemoryProfile: Performance profile
        """
        try:
            estimated_size = self.estimate_model_size(model_path)

            # Get baseline memory
            baseline_memory = memory_monitor.get_memory_info()
            start_time = time.time()

            # Simulate model loading (placeholder - actual implementation would load model)
            # This would be replaced with actual model loading code
            logger.info(f"📝 Profiling model: {os.path.basename(model_path)}")
            time.sleep(0.1)  # Simulate loading time

            # Get post-loading memory
            post_memory = memory_monitor.get_memory_info()
            load_time = time.time() - start_time

            # Calculate actual memory usage
            actual_size = post_memory.used - baseline_memory.used

            # Calculate performance score (placeholder)
            performance_score = min(1.0, max(0.1, 1.0 - (load_time / 10.0)))

            profile = ModelMemoryProfile(
                model_path=model_path,
                estimated_size=estimated_size,
                actual_size=max(0.0, actual_size),
                optimal_layers=gpu_layers,
                load_time=load_time,
                performance_score=performance_score,
            )

            # Cache the profile
            self.model_profiles[model_path] = profile

            logger.info(
                f"✅ Model profile created: {os.path.basename(model_path)} "
                f"({actual_size:.2f}GB actual, {load_time:.2f}s load time)"
            )

            return profile

        except Exception as e:
            logger.error(f"❌ Error profiling model {model_path}: {e}")
            return ModelMemoryProfile(
                model_path=model_path,
                estimated_size=0.0,
                actual_size=0.0,
                optimal_layers=0,
                load_time=0.0,
                performance_score=0.0,
            )

    def optimize_for_models(
        self, model_paths: List[str], available_memory_gb: float
    ) -> Dict[str, int]:
        """
        Optimize GPU layer allocation for multiple models.

        Args:
            model_paths: List of model file paths
            available_memory_gb: Available GPU memory

        Returns:
            Dict mapping model paths to optimal layer counts
        """
        try:
            optimization_results = {}
            total_estimated_size = 0.0

            # Estimate sizes for all models
            model_sizes = {}
            for model_path in model_paths:
                size = self.estimate_model_size(model_path)
                model_sizes[model_path] = size
                total_estimated_size += size

            # If total size fits in memory, optimize each model individually
            if total_estimated_size <= available_memory_gb * self.memory_threshold:
                for model_path in model_paths:
                    layers = self.calculate_optimal_layers(
                        model_sizes[model_path], available_memory_gb / len(model_paths)
                    )
                    optimization_results[model_path] = layers
            else:
                # Need to prioritize and distribute memory
                # Sort by size (smaller models get priority for full GPU usage)
                sorted_models = sorted(model_paths, key=lambda x: model_sizes[x])

                remaining_memory = available_memory_gb * self.memory_threshold

                for model_path in sorted_models:
                    model_size = model_sizes[model_path]

                    if remaining_memory >= model_size:
                        # Can fit full model
                        layers = -1
                        remaining_memory -= model_size
                    else:
                        # Partial allocation
                        layers = self.calculate_optimal_layers(
                            model_size, remaining_memory
                        )
                        remaining_memory = max(0, remaining_memory - model_size * 0.3)

                    optimization_results[model_path] = layers

            logger.info(
                f"🎯 Multi-model optimization complete. "
                f"Total estimated size: {total_estimated_size:.2f}GB, "
                f"Available: {available_memory_gb:.2f}GB"
            )

            return optimization_results

        except Exception as e:
            logger.error(f"❌ Error in multi-model optimization: {e}")
            return {path: 0 for path in model_paths}

    def can_allocate(
        self, required_memory_gb: float, current_memory: GPUMemoryInfo
    ) -> bool:
        """
        Check if required memory can be allocated.

        Args:
            required_memory_gb: Required memory in GB
            current_memory: Current memory status

        Returns:
            bool: True if allocation is possible
        """
        try:
            available = current_memory.free
            threshold_available = (
                current_memory.total * self.memory_threshold - current_memory.used
            )

            can_allocate = required_memory_gb <= min(available, threshold_available)

            if not can_allocate:
                logger.warning(
                    f"⚠️ Cannot allocate {required_memory_gb:.2f}GB. "
                    f"Available: {available:.2f}GB, "
                    f"Threshold available: {threshold_available:.2f}GB"
                )

            return can_allocate

        except Exception as e:
            logger.error(f"❌ Error checking allocation: {e}")
            return False

    def should_use_gpu(
        self, model_size_gb: float, current_memory: GPUMemoryInfo
    ) -> bool:
        """
        Determine if GPU should be used for a model.

        Args:
            model_size_gb: Model size in GB
            current_memory: Current memory status

        Returns:
            bool: True if GPU should be used
        """
        try:
            # Check basic allocation capability
            if not self.can_allocate(model_size_gb, current_memory):
                return False

            # Consider performance benefits
            # Small models (< 1GB) might not benefit much from GPU
            if model_size_gb < 1.0:
                return current_memory.utilization < 0.3  # Only if GPU is mostly free

            # Large models benefit significantly from GPU
            return True

        except Exception as e:
            logger.error(f"❌ Error determining GPU usage: {e}")
            return False
