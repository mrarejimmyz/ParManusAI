"""
Enhanced Todo Manager Module
Comprehensive todo/task management with specialized update methods
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from app.logger import logger


class EnhancedTodoManager:
    """
    Enhanced todo manager with specialized methods for different task types
    """

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        self.default_todo_path = os.path.join(workspace_path, "todo.md")
        os.makedirs(workspace_path, exist_ok=True)

    def update_todo_with_next_steps(
        self, task_description: str, todo_path: Optional[str] = None
    ) -> None:
        """Update the todo.md file with intelligent next steps based on task type"""
        if todo_path is None:
            todo_path = self.default_todo_path

        task_type = self._determine_task_type(task_description)

        if task_type == "travel_waterloo":
            self._update_travel_todo(todo_path)
        elif task_type == "travel_kathmandu":
            self._update_kathmandu_todo(todo_path)
        elif task_type == "economic_analysis":
            self._update_economic_analysis_todo(task_description, todo_path)
        elif task_type == "political_analysis":
            self._update_political_analysis_todo(task_description, todo_path)
        elif task_type == "research":
            self._update_research_todo(task_description, todo_path)
        else:
            self._update_generic_todo(task_description, todo_path)

    def _determine_task_type(self, task_description: str) -> str:
        """Determine the type of task to apply appropriate todo template"""
        task_lower = task_description.lower()

        if "trip" in task_lower and "waterloo" in task_lower:
            return "travel_waterloo"
        elif "trip" in task_lower and "kathmandu" in task_lower:
            return "travel_kathmandu"
        elif any(
            word in task_lower for word in ["recession", "economic", "gdp", "inflation"]
        ):
            return "economic_analysis"
        elif any(word in task_lower for word in ["trump", "biden", "elon", "politics"]):
            return "political_analysis"
        elif any(
            word in task_lower
            for word in ["research", "analyze", "study", "investigate"]
        ):
            return "research"
        else:
            return "generic"

    def _update_travel_todo(self, todo_path: str) -> None:
        """Update todo with travel-specific research steps for Waterloo"""

        research_steps = """1. **Research Accommodations**
   - Search hotels in downtown Waterloo area
   - Compare university guest houses
   - Check Airbnb options for longer stays
   - Review pricing and availability for travel dates

2. **Transportation Planning**
   - Compare flight options to Toronto Pearson vs local airports
   - Research GO Transit routes from Toronto to Waterloo
   - Consider car rental for local flexibility
   - Check local public transportation options

3. **Attractions & Activities Research**
   - University of Waterloo campus tours and events
   - Waterloo Park and outdoor activities
   - Canadian Clay & Glass Gallery exhibitions
   - Local tech company tours (if available)
   - Seasonal events and festivals

4. **Food & Dining Research**
   - Uptown Waterloo restaurant scene
   - University area food options and student favorites
   - Local specialties and craft breweries
   - Make reservations for popular spots

5. **Weather & Seasonal Planning**
   - Check seasonal weather patterns for travel dates
   - Plan appropriate clothing and gear
   - Consider indoor backup activities for bad weather"""

        itinerary_steps = """1. **Day 1 Planning**
   - Arrival and hotel check-in process
   - Initial city orientation walk
   - Dinner at highly-rated local restaurant
   - Evening rest and preparation

2. **Day 2 Planning**
   - University of Waterloo campus visit and tours
   - Waterloo Park exploration and activities
   - Lunch at campus or nearby restaurant
   - Evening tech scene exploration or local events

3. **Day 3 Planning**
   - Canadian Clay & Glass Gallery visit
   - Uptown Waterloo shopping and dining
   - Final sightseeing or missed attractions
   - Departure preparations and checkout"""

        report_steps = """1. **Compile Research Findings**
   - Summarize accommodation options with pros/cons
   - Document final transportation plans and costs
   - List confirmed activities with times and locations
   - Create contact information compilation

2. **Create Final Itinerary**
   - Hour-by-hour schedule for each day
   - Backup plans for weather or unexpected changes
   - Budget breakdown and expense tracking
   - Packing checklist based on activities and weather

3. **Finalize Report**
   - Executive summary of complete trip plan
   - Detailed budget breakdown and cost analysis
   - Emergency contacts and important information
   - Post-trip evaluation criteria"""

        self._update_todo_sections(
            todo_path,
            {
                "research_steps": research_steps,
                "itinerary_steps": itinerary_steps,
                "report_steps": report_steps,
            },
        )

    def _update_kathmandu_todo(self, todo_path: str) -> None:
        """Update todo with Kathmandu travel-specific steps"""

        research_steps = """1. **Visa and Documentation**
   - Check Nepal visa requirements for your country
   - Prepare passport photos and required documents
   - Research visa-on-arrival vs. advance application
   - Verify passport validity (6+ months remaining)

2. **Cultural and Religious Sites Research**
   - Bhaktapur Durbar Square and restoration status
   - UNESCO World Heritage sites and access
   - Buddhist and Hindu temples etiquette and hours
   - Local festivals and cultural events during visit

3. **Practical Planning**
   - Altitude considerations (Kathmandu is at 1,400m)
   - Local currency (Nepalese Rupee) and exchange
   - Health recommendations and vaccinations
   - Weather patterns and appropriate clothing

4. **Accommodation and Transportation**
   - Hotels in Thamel area vs. other districts
   - Airport transfer options and costs
   - Local transportation (taxis, buses, rickshaws)
   - Day tour operators and guide services"""

        self._update_todo_sections(todo_path, {"research_steps": research_steps})

    def _update_economic_analysis_todo(
        self, task_description: str, todo_path: str
    ) -> None:
        """Update todo with economic analysis-specific steps"""

        analysis_steps = """1. **Data Collection Phase**
   - Gather latest GDP growth data and projections
   - Research unemployment rates and trends
   - Collect inflation data from Federal Reserve
   - Review market indicators and economic reports

2. **Source Verification Phase**
   - Cross-reference data from multiple authoritative sources
   - Verify publication dates and data currency
   - Check methodology and data collection methods
   - Identify any potential biases or limitations

3. **Analysis and Interpretation Phase**
   - Compare current data to historical trends
   - Identify correlation patterns and anomalies
   - Assess multiple economic scenarios
   - Consider external factors and global context

4. **Report Compilation Phase**
   - Structure findings with executive summary
   - Create visualizations and data presentations
   - Develop actionable recommendations
   - Prepare supporting documentation and sources"""

        self._update_todo_sections(todo_path, {"analysis_steps": analysis_steps})

    def _update_political_analysis_todo(
        self, task_description: str, todo_path: str
    ) -> None:
        """Update todo with political analysis-specific steps"""

        analysis_steps = """1. **Information Gathering Phase**
   - Research official statements and policy positions
   - Review recent news from multiple credible sources
   - Analyze public statements and social media activity
   - Gather background context and historical information

2. **Fact Verification Phase**
   - Cross-check claims against official records
   - Verify timeline of events and statements
   - Identify conflicting information or discrepancies
   - Assess source credibility and potential bias

3. **Impact Analysis Phase**
   - Evaluate potential policy implications
   - Assess public reaction and opinion trends
   - Consider broader political and economic context
   - Analyze stakeholder perspectives

4. **Synthesis and Reporting Phase**
   - Organize findings in neutral, fact-based manner
   - Present multiple viewpoints fairly
   - Develop balanced conclusions and insights
   - Cite all sources and maintain objectivity"""

        self._update_todo_sections(todo_path, {"analysis_steps": analysis_steps})

    def _update_research_todo(self, task_description: str, todo_path: str) -> None:
        """Update todo with general research-specific steps"""

        research_steps = """1. **Research Planning Phase**
   - Define specific research questions and objectives
   - Identify key terms and search strategies
   - Plan research methodology and approach
   - Set timeline and milestones for completion

2. **Information Collection Phase**
   - Search academic databases and scholarly sources
   - Review government reports and official statistics
   - Collect news articles and current event coverage
   - Gather expert opinions and analysis

3. **Analysis and Evaluation Phase**
   - Assess source credibility and reliability
   - Identify patterns, trends, and key insights
   - Compare different perspectives and viewpoints
   - Synthesize information into coherent findings

4. **Documentation and Reporting Phase**
   - Organize findings into structured report
   - Create executive summary with key points
   - Develop recommendations based on research
   - Cite all sources and maintain proper attribution"""

        self._update_todo_sections(todo_path, {"research_steps": research_steps})

    def _update_generic_todo(self, task_description: str, todo_path: str) -> None:
        """Update todo with generic task steps"""

        generic_steps = f"""1. **Initial Planning Phase**
   - Break down the task: "{task_description}" into smaller components
   - Identify required resources and tools
   - Set realistic timeline and milestones
   - Define success criteria and expected outcomes

2. **Research and Preparation Phase**
   - Gather necessary background information
   - Identify potential challenges and solutions
   - Review best practices and methodologies
   - Prepare required materials and tools

3. **Execution Phase**
   - Follow planned methodology step by step
   - Monitor progress against timeline
   - Document findings and observations
   - Adjust approach as needed based on results

4. **Review and Completion Phase**
   - Review all work for quality and completeness
   - Verify that success criteria are met
   - Document lessons learned and improvements
   - Prepare final deliverables and reports"""

        self._update_todo_sections(todo_path, {"generic_steps": generic_steps})

    def _update_todo_sections(self, todo_path: str, sections: Dict[str, str]) -> None:
        """Update specific sections in todo file"""
        try:
            # Read current todo content
            current_content = ""
            if os.path.exists(todo_path):
                with open(todo_path, "r", encoding="utf-8") as f:
                    current_content = f.read()

            # Update content with new sections
            updated_content = current_content

            for section_key, section_content in sections.items():
                if section_key == "research_steps":
                    updated_content = self._replace_steps_section(
                        updated_content, section_content, "**Steps:**"
                    )
                elif section_key == "itinerary_steps":
                    updated_content = self._replace_itinerary_section(
                        updated_content, section_content
                    )
                elif section_key == "report_steps":
                    updated_content = self._replace_report_section(
                        updated_content, section_content
                    )
                else:
                    # Generic section update
                    updated_content += f"\\n\\n## {section_key.replace('_', ' ').title()}\\n\\n{section_content}"

            # Write updated content
            with open(todo_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"📝 Updated todo file: {os.path.basename(todo_path)}")

        except Exception as e:
            logger.error(f"Error updating todo file: {e}")

    def _replace_steps_section(self, content: str, new_steps: str, marker: str) -> str:
        """Replace steps section in todo content"""
        if marker in content:
            return content.replace(marker, f"{marker}\\n{new_steps}")
        else:
            return content + f"\\n\\n{marker}\\n{new_steps}"

    def _replace_itinerary_section(self, content: str, new_steps: str) -> str:
        """Replace itinerary creation phase in todo content"""
        pattern = r"## Phase 2: Itinerary Creation Phase.*?\\*\\*Steps:\\*\\*"
        replacement = f"## Phase 2: Itinerary Creation Phase [PENDING]\\n\\n**Description:** Create a personalized itinerary for the trip\\n\\n**Success Criteria:** A detailed itinerary is created\\n\\n**Tools Needed:** Microsoft Excel, Google Calendar\\n\\n**Steps:**\\n{new_steps}"

        if re.search(pattern, content, re.DOTALL):
            return re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            return content + f"\\n\\n{replacement}"

    def _replace_report_section(self, content: str, new_steps: str) -> str:
        """Replace report generation phase in todo content"""
        pattern = r"## Phase 3: Report Generation Phase.*?\\*\\*Steps:\\*\\*"
        replacement = f"## Phase 3: Report Generation Phase [PENDING]\\n\\n**Description:** Create a report summarizing the trip plan\\n\\n**Success Criteria:** A comprehensive report is generated\\n\\n**Tools Needed:** Microsoft Word, Google Docs\\n\\n**Steps:**\\n{new_steps}"

        if re.search(pattern, content, re.DOTALL):
            return re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            return content + f"\\n\\n{replacement}"

    def create_new_todo_from_task(self, task_description: str) -> str:
        """Create a brand new todo file for a specific task"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        todo_filename = (
            f"todo_{task_description.lower().replace(' ', '_')[:30]}_{timestamp}.md"
        )
        todo_path = os.path.join(self.workspace_path, todo_filename)

        task_type = self._determine_task_type(task_description)

        # Create appropriate todo template
        if task_type == "travel_waterloo":
            content = self._create_travel_todo_template(task_description)
        elif task_type == "travel_kathmandu":
            content = self._create_kathmandu_todo_template(task_description)
        else:
            content = self._create_generic_todo_template(task_description)

        with open(todo_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"📝 Created new todo file: {todo_filename}")
        return todo_path

    def _create_travel_todo_template(self, task_description: str) -> str:
        """Create a travel-specific todo template"""
        return f"""# Todo: {task_description}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Phase 1: Research Phase [IN PROGRESS]

**Description:** Research and gather information for trip planning

**Success Criteria:** Comprehensive research completed on accommodations, transportation, and activities

**Tools Needed:** Internet browser, note-taking app

**Steps:**
[To be populated with specific research steps]

## Phase 2: Itinerary Creation Phase [PENDING]

**Description:** Create a personalized itinerary for the trip

**Success Criteria:** A detailed itinerary is created

**Tools Needed:** Microsoft Excel, Google Calendar

**Steps:**
[To be populated with itinerary steps]

## Phase 3: Report Generation Phase [PENDING]

**Description:** Create a report summarizing the trip plan

**Success Criteria:** A comprehensive report is generated

**Tools Needed:** Microsoft Word, Google Docs

**Steps:**
[To be populated with report steps]

---
*Todo generated by ParManus*
"""

    def _create_kathmandu_todo_template(self, task_description: str) -> str:
        """Create a Kathmandu-specific todo template"""
        return f"""# Todo: {task_description}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Phase 1: Documentation and Visa Phase [PENDING]

**Description:** Handle visa requirements and documentation

**Success Criteria:** All required documents and visas obtained

**Tools Needed:** Passport, photos, application forms

**Steps:**
[To be populated with visa steps]

## Phase 2: Cultural Research Phase [PENDING]

**Description:** Research cultural sites, customs, and etiquette

**Success Criteria:** Comprehensive understanding of local culture

**Tools Needed:** Research materials, guidebooks

**Steps:**
[To be populated with cultural research steps]

## Phase 3: Practical Planning Phase [PENDING]

**Description:** Plan practical aspects of travel

**Success Criteria:** All practical arrangements completed

**Tools Needed:** Booking websites, currency exchange

**Steps:**
[To be populated with practical planning steps]

---
*Todo generated by ParManus*
"""

    def _create_generic_todo_template(self, task_description: str) -> str:
        """Create a generic todo template"""
        return f"""# Todo: {task_description}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Phase 1: Planning Phase [PENDING]

**Description:** Plan and prepare for task execution

**Success Criteria:** Clear plan and preparation completed

**Tools Needed:** Planning tools, research materials

**Steps:**
[To be populated with planning steps]

## Phase 2: Execution Phase [PENDING]

**Description:** Execute the main task

**Success Criteria:** Task completed successfully

**Tools Needed:** Task-specific tools

**Steps:**
[To be populated with execution steps]

## Phase 3: Review Phase [PENDING]

**Description:** Review and finalize work

**Success Criteria:** Quality review completed

**Tools Needed:** Review tools

**Steps:**
[To be populated with review steps]

---
*Todo generated by ParManus*
"""
