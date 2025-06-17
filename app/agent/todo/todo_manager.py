"""
Todo Management Module
Handles todo file creation and updates for different project types
"""

import os
from datetime import datetime

from app.logger import logger


class TodoManager:
    """Manages todo files and task tracking"""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        os.makedirs(workspace_path, exist_ok=True)

    def update_todo_with_next_steps(
        self, task_description: str, next_steps: str = None
    ) -> bool:
        """Update todo.md with next steps based on task type"""
        try:
            todo_path = os.path.join(self.workspace_path, "todo.md")

            task_lower = task_description.lower()

            if "waterloo" in task_lower and (
                "trip" in task_lower or "visit" in task_lower
            ):
                self._update_travel_todo(todo_path)
            else:
                self._update_generic_todo(task_description, todo_path)

            logger.info(f"✅ Updated todo.md with next steps for: {task_description}")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating todo: {e}")
            return False

    def _update_travel_todo(self, todo_path: str) -> None:
        """Update todo.md with travel-specific content"""

        todo_content = (
            """# Travel Planning Todo List

**Goal:** Plan comprehensive trip to Waterloo, Ontario

**Complexity:** moderate
**Estimated Duration:** 2-3 weeks planning + trip duration

## Phase 1: Research & Planning [CURRENT]

**Description:** Gather information about Waterloo and plan the trip

**Success Criteria:** Complete research on accommodations, transportation, and activities

**Tools Needed:** Internet research, travel websites, booking platforms

**Steps:**
1. Research accommodation options in Waterloo
2. Compare transportation methods (flight + car rental vs driving)
3. Identify must-see attractions and activities
4. Check weather and seasonal considerations
5. Create preliminary budget estimate

## Phase 2: Booking & Arrangements [PENDING]

**Description:** Make all necessary reservations and arrangements

**Success Criteria:** All major bookings confirmed and itinerary finalized

**Tools Needed:** Booking websites, payment methods, calendar

**Steps:**
1. Book accommodation
2. Reserve transportation (flights/car rental)
3. Make restaurant reservations for special meals
4. Book any tours or special activities
5. Confirm all arrangements and create backup plans

## Phase 3: Preparation & Execution [PENDING]

**Description:** Final preparations and trip execution

**Success Criteria:** Successful and enjoyable trip to Waterloo

**Tools Needed:** Luggage, travel documents, local apps

**Steps:**
1. Pack appropriately for season and activities
2. Download local maps and travel apps
3. Prepare travel documents and confirmations
4. Check weather forecast and adjust plans if needed
5. Execute trip and enjoy the experience

---
*Updated: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "*"
        )

        with open(todo_path, "w", encoding="utf-8") as f:
            f.write(todo_content)

    def _update_generic_todo(self, task_description: str, todo_path: str) -> None:
        """Update todo.md with generic task content"""

        # Determine complexity and duration based on task
        complexity = "moderate"
        duration = "1-2 weeks"

        if any(
            word in task_description.lower()
            for word in ["complex", "comprehensive", "detailed"]
        ):
            complexity = "high"
            duration = "2-4 weeks"
        elif any(
            word in task_description.lower() for word in ["simple", "quick", "brief"]
        ):
            complexity = "low"
            duration = "2-3 days"

        todo_content = (
            f"""# Task Todo List

**Goal:** {task_description}

**Complexity:** {complexity}
**Estimated Duration:** {duration}

## Phase 1: Research Phase [CURRENT]

**Description:** Gather information and understand the task requirements

**Success Criteria:** Comprehensive understanding of the task and available resources

**Tools Needed:** Research tools, databases, expert consultations

**Steps:**
1. Define task scope and objectives clearly
2. Identify relevant information sources
3. Conduct preliminary research and data collection
4. Analyze initial findings and identify gaps
5. Create detailed research plan for remaining work

## Phase 2: Analysis Phase [PENDING]

**Description:** Analyze collected information and develop insights

**Success Criteria:** Clear analysis with actionable insights and recommendations

**Tools Needed:** Analytical frameworks, data analysis tools

**Steps:**
1. Apply appropriate analytical methods to collected data
2. Identify patterns, trends, and key insights
3. Develop preliminary conclusions and recommendations
4. Validate findings through additional research if needed
5. Prepare comprehensive analysis report

## Phase 3: Implementation Phase [PENDING]

**Description:** Implement recommendations and monitor outcomes

**Success Criteria:** Successful implementation with measurable results

**Tools Needed:** Implementation resources, monitoring tools

**Steps:**
1. Develop detailed implementation plan
2. Identify required resources and stakeholders
3. Execute implementation plan with regular monitoring
4. Adjust approach based on feedback and results
5. Document lessons learned and final outcomes

---
*Updated: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "*"
        )

        with open(todo_path, "w", encoding="utf-8") as f:
            f.write(todo_content)

    def create_project_todo(
        self, task_description: str, project_type: str = "analysis"
    ) -> str:
        """Create a new todo file for a specific project"""

        todo_path = os.path.join(self.workspace_path, "todo.md")

        if project_type == "travel" or "travel" in task_description.lower():
            self._update_travel_todo(todo_path)
        else:
            self._update_generic_todo(task_description, todo_path)

        logger.info(f"📝 Created todo file for: {task_description}")
        return todo_path

    def get_current_phase(self, todo_path: str = None) -> str:
        """Extract current phase from todo file"""
        try:
            if not todo_path:
                todo_path = os.path.join(self.workspace_path, "todo.md")

            if not os.path.exists(todo_path):
                return "Research Phase"

            with open(todo_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for [CURRENT] marker
            lines = content.split("\n")
            for line in lines:
                if "[CURRENT]" in line and "##" in line:
                    # Extract phase name
                    phase = line.split("##")[-1].replace("[CURRENT]", "").strip()
                    return phase

            return "Research Phase"

        except Exception as e:
            logger.error(f"Error getting current phase: {e}")
            return "Research Phase"

    def mark_phase_complete(self, phase_name: str, todo_path: str = None) -> bool:
        """Mark a phase as complete and move to next phase"""
        try:
            if not todo_path:
                todo_path = os.path.join(self.workspace_path, "todo.md")

            if not os.path.exists(todo_path):
                logger.warning("Todo file not found")
                return False

            with open(todo_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace [CURRENT] with [COMPLETED] and move to next phase
            updated_content = content.replace(
                f"{phase_name} [CURRENT]", f"{phase_name} [COMPLETED]"
            )

            # Find next phase and mark as current
            phases = ["Research Phase", "Analysis Phase", "Implementation Phase"]
            try:
                current_index = next(
                    i for i, p in enumerate(phases) if phase_name.startswith(p)
                )
                if current_index < len(phases) - 1:
                    next_phase = phases[current_index + 1]
                    updated_content = updated_content.replace(
                        f"{next_phase} [PENDING]", f"{next_phase} [CURRENT]"
                    )
            except (StopIteration, IndexError):
                pass

            with open(todo_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"✅ Marked phase complete: {phase_name}")
            return True

        except Exception as e:
            logger.error(f"Error marking phase complete: {e}")
            return False
