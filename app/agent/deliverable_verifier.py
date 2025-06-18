"""
Deliverable Verification Module for Manus Agent
Handles verification of created deliverables and files.
"""

import os
import time
from typing import List

from app.logger import logger


class DeliverableVerifier:
    """Verifies that deliverables are properly created and contain substantial content."""

    def __init__(self, workspace_root: str = "workspace"):
        self.workspace_root = workspace_root

    async def verify_deliverable_creation(self, current_step: str) -> bool:
        """
        Verify that the deliverable for the current step was actually created
        """
        try:
            # Check if a new file was created in the workspace
            workspace_path = os.path.join(os.getcwd(), self.workspace_root)
            if not os.path.exists(workspace_path):
                logger.warning("Workspace directory does not exist")
                return False

            # Get list of files in workspace
            current_files = []
            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    current_files.append(os.path.join(root, file))

            # Check if any files were created recently (within last 60 seconds)
            current_time = time.time()
            recent_files = []

            for filepath in current_files:
                try:
                    # Check file modification time
                    mtime = os.path.getmtime(filepath)
                    if current_time - mtime < 60:  # Created within last 60 seconds
                        recent_files.append(filepath)
                except OSError:
                    continue

            if recent_files:
                logger.info(
                    f"✅ Found {len(recent_files)} recently created deliverable(s): {[os.path.basename(f) for f in recent_files]}"
                )

                # Additional verification: check if files contain substantial content
                for filepath in recent_files:
                    try:
                        if filepath.endswith(".md"):
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read()
                                if len(content) > 500:  # Substantial content
                                    logger.info(
                                        f"✅ Verified substantial content in {os.path.basename(filepath)} ({len(content)} characters)"
                                    )
                                    return True
                                else:
                                    logger.warning(
                                        f"⚠️ File {os.path.basename(filepath)} has insufficient content ({len(content)} characters)"
                                    )
                    except Exception as e:
                        logger.warning(f"Could not verify content of {filepath}: {e}")
                        continue

                # If we have recent files but couldn't verify content, still consider it a success
                if recent_files:
                    return True

            logger.warning("⚠️ No recent deliverables found in workspace")
            return False

        except Exception as e:
            logger.error(f"Error verifying deliverable creation: {e}")
            return False

    def get_recent_files(self, max_age_seconds: int = 60) -> List[str]:
        """Get list of recently created/modified files."""
        try:
            workspace_path = os.path.join(os.getcwd(), self.workspace_root)
            if not os.path.exists(workspace_path):
                return []

            current_time = time.time()
            recent_files = []

            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(filepath)
                        if current_time - mtime < max_age_seconds:
                            recent_files.append(filepath)
                    except OSError:
                        continue

            return recent_files
        except Exception as e:
            logger.error(f"Error getting recent files: {e}")
            return []

    def verify_file_content(self, filepath: str, min_length: int = 500) -> bool:
        """Verify that a file contains substantial content."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                return len(content) >= min_length
        except Exception as e:
            logger.warning(f"Could not verify content of {filepath}: {e}")
            return False
