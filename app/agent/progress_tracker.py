"""
Todo Progress Tracker
Manages updating todo.md file when tasks are completed
"""

import os
import re
from datetime import datetime
from typing import List, Optional, Dict
from app.logger import logger


class TodoProgressTracker:
    """Tracks and updates progress in todo.md file"""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.todo_file_path = os.path.join(workspace_path, "todo.md")

    async def mark_step_complete(self, step_description: str, phase_name: Optional[str] = None) -> bool:
        """Mark a specific step as complete in todo.md"""
        try:
            if not os.path.exists(self.todo_file_path):
                logger.warning("No todo.md file found to update")
                return False

            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find the step and mark it complete
            updated_content = self._mark_checkbox_complete(content, step_description, phase_name)
            
            if updated_content != content:
                with open(self.todo_file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                
                logger.info(f" Marked step complete in todo.md: {step_description[:50]}...")
                return True
            else:
                logger.debug(f"Step not found in todo.md: {step_description[:50]}...")
                return False

        except Exception as e:
            logger.error(f"Error updating todo.md progress: {e}")
            return False

    def _mark_checkbox_complete(self, content: str, step_description: str, phase_name: Optional[str] = None) -> str:
        """Find and mark checkbox as complete"""
        lines = content.split('\n')
        updated_lines = []
        
        # Look for the step using fuzzy matching
        step_keywords = self._extract_keywords(step_description.lower())
        
        for line in lines:
            # Check for both markdown checkboxes (- [ ]) and numbered checkboxes (1. [ ])
            if '- [ ]' in line or ('] ' in line and '[ ]' in line):
                line_text = line.lower()
                # Check if this line matches the step description
                if self._is_matching_step(line_text, step_keywords):
                    # Mark as complete - handle both formats
                    if '- [ ]' in line:
                        updated_line = line.replace('- [ ]', '- [x]')
                    elif '] ' in line and '[ ]' in line:
                        updated_line = line.replace('[ ]', '[x]')
                    else:
                        updated_line = line
                    updated_lines.append(updated_line)
                    logger.info(f" Found and marked complete: {line.strip()}")
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key words from step description for matching"""
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        return keywords[:5]  # Take top 5 keywords

    def _is_matching_step(self, line_text: str, step_keywords: List[str]) -> bool:
        """Check if a line matches the step description using keyword matching"""
        if not step_keywords:
            return False
            
        # Count how many keywords match
        matches = sum(1 for keyword in step_keywords if keyword in line_text)
        
        # Consider it a match if at least 2 keywords match (or 1 for short descriptions)
        threshold = 1 if len(step_keywords) <= 2 else 2
        return matches >= threshold

    def get_completion_status(self) -> Dict[str, any]:
        """Get current completion status from todo.md"""
        try:
            if not os.path.exists(self.todo_file_path):
                return {"error": "No todo.md file found"}

            with open(self.todo_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Count completed vs total checkboxes
            total_tasks = len(re.findall(r'- \[[ x]\]', content)) + len(re.findall(r'\d+\. \[[ x]\]', content))
            completed_tasks = len(re.findall(r'- \[x\]', content)) + len(re.findall(r'\d+\. \[x\]', content))
            
            completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_percentage": completion_percentage,
                "is_complete": completion_percentage >= 100
            }

        except Exception as e:
            logger.error(f"Error getting completion status: {e}")
            return {"error": str(e)}
