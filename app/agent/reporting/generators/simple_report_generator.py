"""
Simple Report Generator Module
Handles basic report creation and LLM-driven content generation
"""

import os
from datetime import datetime
from typing import Dict, List

from app.logger import logger


class SimpleReportGenerator:
    """Simple, focused report generator"""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        os.makedirs(workspace_path, exist_ok=True)

    async def create_llm_report(
        self, task_description: str, search_results: List[Dict], report_name: str
    ) -> str:
        """Create intelligent report using LLM analysis"""
        try:
            from app.config import load_config
            from app.llm import LLM

            config = load_config()
            llm = LLM(config.llm)

            if not search_results:
                # Generate knowledge-based report
                return await self._create_knowledge_based_report(
                    llm, task_description, report_name
                )
            else:
                # Generate data-driven report
                return await self._create_data_driven_report(
                    llm, task_description, search_results, report_name
                )

        except Exception as e:
            logger.error(f"Error creating LLM report: {e}")
            return self._create_fallback_report(task_description, report_name)

    async def _create_knowledge_based_report(
        self, llm, task_description: str, report_name: str
    ) -> str:
        """Create report based on LLM knowledge when no search data available"""

        prompt = f"""Create a comprehensive, factual report for this task:

TASK: {task_description}

Since no relevant search data was found, use your knowledge to provide a factual analysis.

REQUIREMENTS:
- Be factual and accurate - no speculation or made-up details
- Provide logical reasoning and analysis
- Use clear structure with Executive Summary, Key Findings, Recommendations
- Clearly state when information is based on general knowledge vs. specific sources
- If the topic involves current events you're not sure about, acknowledge limitations

FORMAT:
# Report: [Task Title]

**Generated:** [Date]

## Executive Summary
[Brief overview and key insights]

## Key Findings
[Main points and analysis]

## Recommendations
[Actionable advice]

## Next Steps
[Implementation suggestions]

---
*Report generated using AI knowledge base*"""

        content = await llm.ask(prompt)
        report_path = os.path.join(self.workspace_path, report_name)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"📝 Created knowledge-based report: {report_name}")
        return report_path

    async def _create_data_driven_report(
        self, llm, task_description: str, search_results: List[Dict], report_name: str
    ) -> str:
        """Create report based on validated search results"""

        # Prepare search data for LLM
        sources_text = ""
        for i, result in enumerate(search_results[:5], 1):
            title = result.get("title", "N/A")
            content = result.get("content", result.get("snippet", ""))[:300]
            url = result.get("url", "N/A")
            sources_text += (
                f"\nSource {i}:\nTitle: {title}\nURL: {url}\nContent: {content}...\n"
            )

        prompt = f"""Create a comprehensive report based on the provided sources:

TASK: {task_description}

SOURCES:
{sources_text}

REQUIREMENTS:
- Base analysis on the provided sources
- Synthesize information from multiple sources
- Provide clear executive summary and key findings
- Include actionable recommendations
- Reference sources appropriately
- Be factual - don't add information not supported by sources

FORMAT:
# Report: [Task Title]

**Generated:** [Date]

## Executive Summary
[Overview based on sources]

## Key Findings
[Analysis of source information]

## Recommendations
[Actionable advice based on findings]

## Next Steps
[Implementation suggestions]

## Sources
[List the sources used]

---
*Report generated from validated search results*"""

        content = await llm.ask(prompt)
        report_path = os.path.join(self.workspace_path, report_name)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"📝 Created data-driven report: {report_name}")
        return report_path

    def _create_fallback_report(self, task_description: str, report_name: str) -> str:
        """Create basic fallback report when LLM is unavailable"""

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Report: {task_description}

**Generated:** {current_time}

## Executive Summary

This report was generated for the task: "{task_description}"

## Key Findings

- Task analysis is pending
- Additional research may be required
- Report generated in fallback mode

## Recommendations

1. Review task requirements
2. Gather additional information if needed
3. Update report with specific findings

## Next Steps

1. **Research Phase** - Collect relevant information
2. **Analysis Phase** - Process collected data
3. **Implementation Phase** - Execute recommendations

---
*Fallback report generated by ParManus*
"""

        report_path = os.path.join(self.workspace_path, report_name)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"📝 Created fallback report: {report_name}")
        return report_path

    def generate_report_name(
        self, task_description: str, report_type: str = "analysis"
    ) -> str:
        """Generate a unique report filename"""
        import re

        clean_task = re.sub(r"[^\w\s-]", "", task_description.lower())
        clean_task = re.sub(r"[-\s]+", "_", clean_task)

        if len(clean_task) > 50:
            clean_task = clean_task[:50].rstrip("_")

        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{report_type}_{clean_task}_{date_str}.md"
