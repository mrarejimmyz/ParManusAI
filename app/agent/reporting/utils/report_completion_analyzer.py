"""
Report Completion Analyzer for ParManus
Analyzes report completeness and adds tracking checkboxes
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Tuple

from app.logger import logger


class ReportCompletionAnalyzer:
    """Analyzes and tracks report completion status"""

    def __init__(self):
        self.required_sections = {
            "Executive Summary": "A brief overview of the main findings and recommendations",
            "Key Findings": "Main research results and important discoveries",
            "Detailed Analysis": "In-depth analysis of the data and information",
            "Recommendations": "Actionable recommendations based on the analysis",
            "Sources": "References and sources used in the research",
        }

        self.travel_specific_sections = {
            "Transportation Options": "How to get to Ontario and transportation within the province",
            "Accommodation Recommendations": "Where to stay - hotels, resorts, camping options",
            "Top Attractions": "Must-see places and activities in Ontario",
            "Itinerary Planning": "Suggested routes and daily schedules",
            "Budget Estimation": "Estimated costs for different types of trips",
            "Best Time to Visit": "Seasonal recommendations and weather considerations",
            "Local Tips": "Insider knowledge and practical travel tips",
        }

    def analyze_report_completeness(self, report_path: str) -> Dict:
        """Analyze how complete a report is"""
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()

            analysis = {
                "file_path": report_path,
                "total_sections": 0,
                "completed_sections": 0,
                "missing_sections": [],
                "placeholder_sections": [],
                "completion_percentage": 0,
                "has_research_data": False,
                "sections_analysis": {},
            }

            # Determine if this is a travel report
            is_travel_report = any(
                keyword in content.lower()
                for keyword in ["trip", "travel", "ontario", "vacation", "tour"]
            )

            # Combine required sections with travel-specific if needed
            sections_to_check = self.required_sections.copy()
            if is_travel_report:
                sections_to_check.update(self.travel_specific_sections)

            analysis["total_sections"] = len(sections_to_check)

            # Check each section
            for section_name, description in sections_to_check.items():
                section_status = self._analyze_section(content, section_name)
                analysis["sections_analysis"][section_name] = {
                    "description": description,
                    "status": section_status["status"],
                    "content_length": section_status["content_length"],
                    "has_placeholders": section_status["has_placeholders"],
                }

                if section_status["status"] == "complete":
                    analysis["completed_sections"] += 1
                elif section_status["status"] == "missing":
                    analysis["missing_sections"].append(section_name)
                elif section_status["status"] == "placeholder":
                    analysis["placeholder_sections"].append(section_name)

            # Check for research data
            analysis["has_research_data"] = (
                "## Research Data" in content or "### Source" in content
            )

            # Calculate completion percentage
            analysis["completion_percentage"] = (
                (analysis["completed_sections"] / analysis["total_sections"] * 100)
                if analysis["total_sections"] > 0
                else 0
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing report completeness: {e}")
            return {"error": str(e)}

    def _analyze_section(self, content: str, section_name: str) -> Dict:
        """Analyze a specific section of the report"""
        # Look for the section header
        section_pattern = rf"## {re.escape(section_name)}\s*\n(.*?)(?=\n## |\n---|\Z)"
        match = re.search(section_pattern, content, re.DOTALL | re.IGNORECASE)

        if not match:
            return {"status": "missing", "content_length": 0, "has_placeholders": False}

        section_content = match.group(1).strip()
        content_length = len(section_content)

        # Check for placeholders
        placeholders = [
            "[Summary of findings will be added here]",
            "[Research findings will be added here]",
            "[Detailed analysis will be added here]",
            "[Recommendations will be added here]",
            "[Sources and references will be added here]",
            "[Content will be added here]",
            "[To be completed]",
        ]

        has_placeholders = any(
            placeholder in section_content for placeholder in placeholders
        )

        # Determine status
        if content_length < 50 or has_placeholders:
            status = "placeholder"
        elif content_length >= 100:
            status = "complete"
        else:
            status = "incomplete"

        return {
            "status": status,
            "content_length": content_length,
            "has_placeholders": has_placeholders,
        }

    def generate_completion_checklist(self, analysis: Dict) -> str:
        """Generate a completion checklist for the report"""
        checklist = "\n## Report Completion Checklist\n\n"
        checklist += f"**Overall Progress: {analysis['completion_percentage']:.1f}% Complete**\n\n"

        for section_name, section_info in analysis["sections_analysis"].items():
            status = section_info["status"]

            if status == "complete":
                checkbox = "- [x]"
                status_emoji = "✅"
            elif status == "placeholder":
                checkbox = "- [ ]"
                status_emoji = "📝"
            elif status == "incomplete":
                checkbox = "- [~]"
                status_emoji = "⚠️"
            else:  # missing
                checkbox = "- [ ]"
                status_emoji = "❌"

            checklist += f"{checkbox} {status_emoji} **{section_name}** - {section_info['description']}\n"

        # Add special items
        checklist += "\n### Additional Requirements:\n"

        if analysis.get("has_research_data"):
            checklist += (
                "- [x] ✅ **Research Data** - Sources and references collected\n"
            )
        else:
            checklist += (
                "- [ ] ❌ **Research Data** - Collect and add research sources\n"
            )

        # Add priority recommendations
        checklist += "\n### Priority Actions:\n"

        if analysis["placeholder_sections"]:
            checklist += f"1. **Replace placeholders** in: {', '.join(analysis['placeholder_sections'])}\n"

        if analysis["missing_sections"]:
            checklist += f"2. **Add missing sections**: {', '.join(analysis['missing_sections'])}\n"

        if analysis["completion_percentage"] < 50:
            checklist += "3. **Focus on core content** - Complete Executive Summary and Key Findings first\n"

        checklist += "\n---\n*Checklist generated by ParManus Report Analyzer*\n"

        return checklist

    def update_report_with_checklist(self, report_path: str) -> bool:
        """Add or update the completion checklist in a report"""
        try:
            # Analyze the report
            analysis = self.analyze_report_completeness(report_path)

            if "error" in analysis:
                logger.error(f"Cannot update report: {analysis['error']}")
                return False

            # Read current content
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Generate checklist
            checklist = self.generate_completion_checklist(analysis)

            # Remove existing checklist if present
            content = re.sub(
                r"\n## Report Completion Checklist.*?(?=\n## |\n---\n\*Report generated|\Z)",
                "",
                content,
                flags=re.DOTALL,
            )

            # Find insertion point (before the final "Report generated" line)
            if "---\n*Report generated by ParManus AI Agent System*" in content:
                content = content.replace(
                    "---\n*Report generated by ParManus AI Agent System*",
                    f"{checklist}\n---\n*Report generated by ParManus AI Agent System*",
                )
            else:
                # Add to the end
                content += checklist

            # Write updated content
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(
                f"✅ Updated report with completion checklist: {os.path.basename(report_path)}"
            )
            logger.info(
                f"📊 Report is {analysis['completion_percentage']:.1f}% complete"
            )

            return True

        except Exception as e:
            logger.error(f"Error updating report with checklist: {e}")
            return False

    def get_completion_reasoning(self, analysis: Dict) -> str:
        """Generate reasoning about what needs to be completed"""
        reasoning = f"## Report Completion Analysis\n\n"
        reasoning += (
            f"**Current Status:** {analysis['completion_percentage']:.1f}% Complete\n\n"
        )

        if analysis["completion_percentage"] >= 80:
            reasoning += (
                "🎉 **Excellent Progress!** This report is nearly complete.\n\n"
            )
        elif analysis["completion_percentage"] >= 50:
            reasoning += "👍 **Good Progress!** This report is well underway.\n\n"
        else:
            reasoning += (
                "🚧 **Needs Attention!** This report requires significant work.\n\n"
            )

        # Specific recommendations
        reasoning += "### Next Steps:\n\n"

        if analysis["placeholder_sections"]:
            reasoning += f"1. **Replace placeholder content** in {len(analysis['placeholder_sections'])} sections:\n"
            for section in analysis["placeholder_sections"]:
                reasoning += f"   - {section}\n"
            reasoning += "\n"

        if analysis["missing_sections"]:
            reasoning += f"2. **Add missing sections** ({len(analysis['missing_sections'])} required):\n"
            for section in analysis["missing_sections"]:
                reasoning += f"   - {section}\n"
            reasoning += "\n"

        if not analysis.get("has_research_data"):
            reasoning += "3. **Gather research data** - The report needs sources and references\n\n"

        reasoning += "### Priority Order:\n"
        reasoning += "1. Executive Summary (gives overview)\n"
        reasoning += "2. Key Findings (core content)\n"
        reasoning += "3. Recommendations (actionable items)\n"
        reasoning += "4. Detailed Analysis (supporting details)\n"
        reasoning += "5. Additional specialized sections\n"

        return reasoning
