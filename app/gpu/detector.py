"""
GPU Detection and Device Management

Handles CUDA detection, device enumeration, and availability checks.
"""

import os
import subprocess
from typing import Optional

from app.logger import logger


class GPUDetector:
    """Handles GPU detection and device enumeration."""

    @staticmethod
    def check_cuda_availability() -> bool:
        """
        Check if CUDA is available on the system.

        Returns:
            bool: True if CUDA is available, False otherwise
        """
        try:
            # Method 1: Check torch CUDA
            try:
                import torch

                if torch.cuda.is_available():
                    logger.info("✅ CUDA detected via PyTorch")
                    return True
            except ImportError:
                logger.debug("PyTorch not available for CUDA detection")

            # Method 2: Check nvidia-smi command
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    logger.info("✅ CUDA detected via nvidia-smi")
                    return True
            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                logger.debug("nvidia-smi not available or failed")

            # Method 3: Check environment variables
            cuda_env_vars = [
                "CUDA_HOME",
                "CUDA_PATH",
                "CUDA_ROOT",
                "CUDA_TOOLKIT_ROOT_DIR",
            ]
            for var in cuda_env_vars:
                if os.environ.get(var):
                    logger.info(f"✅ CUDA detected via environment variable: {var}")
                    return True

            # Method 4: Check common CUDA installation paths
            common_paths = [
                "/usr/local/cuda",
                "/opt/cuda",
                "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA",
                "C:\\CUDA",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"✅ CUDA detected at path: {path}")
                    return True

            logger.warning("❌ CUDA not detected on system")
            return False

        except Exception as e:
            logger.error(f"❌ Error during CUDA detection: {e}")
            return False

    @staticmethod
    def get_device_count() -> int:
        """
        Get the number of available GPU devices.

        Returns:
            int: Number of GPU devices available
        """
        try:
            # Method 1: PyTorch
            try:
                import torch

                if torch.cuda.is_available():
                    count = torch.cuda.device_count()
                    logger.info(f"🔍 Found {count} GPU device(s) via PyTorch")
                    return count
            except ImportError:
                pass

            # Method 2: nvidia-ml-py
            try:
                import pynvml

                pynvml.nvmlInit()
                count = pynvml.nvmlDeviceGetCount()
                logger.info(f"🔍 Found {count} GPU device(s) via pynvml")
                return count
            except ImportError:
                pass

            # Method 3: nvidia-smi
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--list-gpus"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    count = len(
                        [line for line in result.stdout.split("\n") if line.strip()]
                    )
                    logger.info(f"🔍 Found {count} GPU device(s) via nvidia-smi")
                    return count
            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                pass

            logger.warning("⚠️ Could not determine GPU device count")
            return 0

        except Exception as e:
            logger.error(f"❌ Error getting GPU device count: {e}")
            return 0

    @staticmethod
    def get_device_name(device_id: int = 0) -> Optional[str]:
        """
        Get the name of a specific GPU device.

        Args:
            device_id: GPU device ID

        Returns:
            str: Device name or None if not available
        """
        try:
            # Method 1: PyTorch
            try:
                import torch

                if torch.cuda.is_available() and device_id < torch.cuda.device_count():
                    name = torch.cuda.get_device_name(device_id)
                    logger.debug(f"🔍 Device {device_id} name via PyTorch: {name}")
                    return name
            except ImportError:
                pass

            # Method 2: nvidia-smi
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    names = result.stdout.strip().split("\n")
                    if device_id < len(names):
                        name = names[device_id].strip()
                        logger.debug(
                            f"🔍 Device {device_id} name via nvidia-smi: {name}"
                        )
                        return name
            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                pass

            return None

        except Exception as e:
            logger.error(f"❌ Error getting device name for device {device_id}: {e}")
            return None
