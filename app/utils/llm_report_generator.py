"""
LLM-Driven Report Generator
Uses the LLM to transform raw research data into high-quality, well-formatted analysis reports.
"""

import json
from typing import Any, Dict, List, Optional

from app.logger import logger


class LLMReportGenerator:
    """Generates high-quality reports using LLM intelligence."""

    def __init__(self, llm):
        self.llm = llm

    async def generate_analysis_report(
        self, query: str, research_data: List[Dict], confidence_level: str = "High"
    ) -> str:
        """
        Generate a comprehensive analysis report using LLM intelligence.

        Args:
            query: The original user query
            research_data: List of search results and data
            confidence_level: Confidence level for the analysis

        Returns:
            Well-formatted markdown report
        """

        # Prepare the research context for the LLM
        research_context = self._prepare_research_context(research_data)

        # Create the report generation prompt
        prompt = self._create_report_prompt(query, research_context, confidence_level)

        try:
            # Generate the report using LLM
            response = await self.llm.ask(prompt)

            # Post-process and validate the report
            formatted_report = self._post_process_report(response, query)

            logger.info(
                f"✅ Generated high-quality analysis report for: {query[:50]}..."
            )
            return formatted_report

        except Exception as e:
            logger.error(f"❌ Error generating LLM report: {e}")
            # Fallback to basic report structure
            return self._create_fallback_report(query, research_data, confidence_level)

    def _prepare_research_context(self, research_data: List[Dict]) -> str:
        """Prepare research data for LLM consumption."""
        context_parts = []

        for i, data in enumerate(research_data, 1):
            if isinstance(data, dict):
                # Extract meaningful information from search results
                if "query" in data and "results" in data:
                    context_parts.append(f"Search {i}: {data['query']}")

                    if isinstance(data["results"], list):
                        for j, result in enumerate(data["results"], 1):
                            if isinstance(result, dict):
                                title = result.get("title", f"Result {j}")
                                url = result.get("url", "No URL")
                                snippet = result.get(
                                    "snippet", "No description available"
                                )

                                # Clean up the snippet
                                snippet = self._clean_snippet(snippet)

                                context_parts.append(f"  {j}. {title}")
                                context_parts.append(f"     Source: {url}")
                                context_parts.append(f"     Content: {snippet}")
                                context_parts.append("")

                elif "title" in data:
                    # Direct result format
                    title = data.get("title", "Untitled")
                    url = data.get("url", "No URL")
                    snippet = data.get("snippet", "No description")
                    snippet = self._clean_snippet(snippet)

                    context_parts.append(f"Source {i}: {title}")
                    context_parts.append(f"URL: {url}")
                    context_parts.append(f"Content: {snippet}")
                    context_parts.append("")
            else:
                # Handle other data types
                context_parts.append(f"Data {i}: {str(data)}")
                context_parts.append("")

        return "\n".join(context_parts)

    def _clean_snippet(self, snippet: str) -> str:
        """Clean and format snippet text."""
        if not isinstance(snippet, str):
            return str(snippet)

        # Remove JSON artifacts
        import re

        snippet = re.sub(r'[{}"\']', "", snippet)
        snippet = re.sub(r"position:\s*\d+", "", snippet)
        snippet = re.sub(r"source:\s*\w+", "", snippet)
        snippet = re.sub(r"content_method:\s*\w+", "", snippet)

        # Clean whitespace
        snippet = re.sub(r"\s+", " ", snippet.strip())

        # Ensure reasonable length
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."

        return snippet

    def _create_report_prompt(
        self, query: str, research_context: str, confidence_level: str
    ) -> str:
        """Create the LLM prompt for report generation."""

        prompt = f"""You are an expert research analyst. Generate a comprehensive, professional analysis report based on the research data provided.

USER QUERY: "{query}"

RESEARCH DATA:
{research_context}

Please create a well-structured, professional analysis report with the following requirements:

1. **Format**: Use clear markdown formatting with proper headers and sections
2. **Quality**: Synthesize the information intelligently, avoid raw data dumps
3. **Structure**: Include executive summary, key findings, analysis, and recommendations
4. **Accuracy**: Only include information supported by the research data
5. **Currency**: Note any data freshness concerns (dates, outdated information)
6. **Readability**: Write in professional, clear language suitable for business reports

REQUIRED SECTIONS:
- Executive Summary
- Key Findings (synthesized from research)
- Detailed Analysis (organized by themes)
- Market/Industry Context (if applicable)
- Recommendations
- Data Sources Summary

FORMATTING GUIDELINES:
- Use proper markdown headers (##, ###)
- Include bullet points for key insights
- Add source attribution where relevant
- Highlight important metrics or data points
- Ensure no raw JSON or technical artifacts appear

CONFIDENCE LEVEL: {confidence_level}

Generate a professional, actionable analysis report now:"""

        return prompt

    def _post_process_report(self, report: str, query: str) -> str:
        """Post-process the LLM-generated report."""

        # Add header if not present
        if not report.strip().startswith("#"):
            title = self._generate_title(query)
            report = f"# {title}\n\n{report}"

        # Add data freshness warning if this appears to be LLM-generated content
        if self._is_likely_llm_generated(report):
            warning_section = f"""

## ⚠️ Data Freshness Warning

**IMPORTANT**: This report may contain AI-generated content due to web search limitations. Please verify information through independent sources before making decisions based on this analysis.

- **Data Sources**: Limited to AI model training data
- **Currency**: Information may not reflect recent developments
- **Verification**: Cross-check facts with authoritative sources
- **Confidence**: Treat as preliminary analysis requiring validation"""

            # Insert warning before any existing conclusion or footer
            if "## Conclusion" in report:
                report = report.replace("## Conclusion", warning_section + "\n\n## Conclusion")
            elif "---" in report:
                report = report.replace("---", warning_section + "\n\n---")
            else:
                report += warning_section

        # Add metadata footer
        from datetime import datetime

        current_date = datetime.now().strftime("%B %d, %Y")

        footer = f"""

---

*📊 **Report Generated**: {current_date} using AI-powered research synthesis*
*🔍 **Analysis Quality**: Enhanced through LLM-driven content generation*
*⚡ **Data Processing**: Intelligent extraction and synthesis from multiple sources*
*⚠️ **Note**: Information accuracy depends on available data sources*"""

        report += footer

        # Clean up any remaining artifacts
        import re

        report = re.sub(r"\n{3,}", "\n\n", report)  # Remove excessive blank lines

        return report

    def _generate_title(self, query: str) -> str:
        """Generate an appropriate title for the report."""
        # Capitalize and clean up the query for use as title
        title = query.strip()
        if title.lower().startswith(("write", "create", "generate", "make")):
            # Remove action words and focus on the subject
            words = title.split()
            if len(words) > 1:
                title = " ".join(words[1:])

        # Capitalize properly
        title = " ".join(word.capitalize() for word in title.split())

        # Add "Analysis Report" if not already present
        if "analysis" not in title.lower() and "report" not in title.lower():
            title += " - Analysis Report"

        return title

    def _create_fallback_report(
        self, query: str, research_data: List[Dict], confidence_level: str
    ) -> str:
        """Create a basic fallback report if LLM generation fails."""

        title = self._generate_title(query)
        from datetime import datetime

        current_date = datetime.now().strftime("%B %d, %Y")

        fallback_report = f"""# {title}

## Executive Summary

This analysis was generated in response to: "{query}"

Due to processing limitations, this report provides a basic summary of the available research data.

## Research Data Summary

Total data sources analyzed: {len(research_data)}
Confidence level: {confidence_level}

## Key Sources

"""

        # Add basic source information
        for i, data in enumerate(research_data[:5], 1):  # Limit to 5 sources
            if isinstance(data, dict) and "results" in data:
                if isinstance(data["results"], list) and data["results"]:
                    first_result = data["results"][0]
                    if isinstance(first_result, dict):
                        title = first_result.get("title", f"Source {i}")
                        url = first_result.get("url", "URL not available")
                        fallback_report += f"{i}. **{title}**\n   - Source: {url}\n\n"

        fallback_report += f"""
## Recommendations

For a more comprehensive analysis, please review the individual sources listed above.

---

*📊 **Report Generated**: {current_date}*
*⚠️ **Note**: This is a fallback report due to processing limitations*"""

        return fallback_report

    def _is_likely_llm_generated(self, report: str) -> bool:
        """Detect if report contains likely LLM-generated content."""
        # Check for indicators that suggest LLM fallback was used
        llm_indicators = [
            "LLM-driven intelligent content generation",
            "LLM generated",
            "intelligent search results",
            "LLM-driven",
            "AI-powered research synthesis"
        ]

        report_lower = report.lower()
        for indicator in llm_indicators:
            if indicator.lower() in report_lower:
                return True

        # Check for fake URLs (common in LLM hallucination)
        import re
        fake_url_patterns = [
            r'https://www\.[^/]+/[^/]+/[^/]*-\d{4}-\d{2}-\d{2}[^/]*/',
            r'Source: \[[^\]]+\] [A-Z][^:]+: "[^"]*"',
        ]

        for pattern in fake_url_patterns:
            if re.search(pattern, report):
                return True

        return False


class SearchResultFormatter:
    """Helper class to format search results for LLM consumption."""

    @staticmethod
    def format_for_llm_analysis(search_results: Any) -> Dict[str, Any]:
        """
        Format search results for optimal LLM analysis.

        Args:
            search_results: Raw search results from any source

        Returns:
            Structured data suitable for LLM analysis
        """

        if isinstance(search_results, str):
            try:
                # Try to parse if it's JSON string
                parsed = json.loads(search_results)
                return SearchResultFormatter.format_for_llm_analysis(parsed)
            except json.JSONDecodeError:
                # Treat as plain text
                return {
                    "type": "text_content",
                    "content": search_results,
                    "source": "text_input",
                }

        elif isinstance(search_results, dict):
            return {
                "type": "search_result",
                "query": search_results.get("query", ""),
                "results": SearchResultFormatter._format_result_list(
                    search_results.get("results", [])
                ),
                "metadata": {
                    k: v
                    for k, v in search_results.items()
                    if k not in ["query", "results"]
                },
            }

        elif isinstance(search_results, list):
            return {
                "type": "result_list",
                "results": SearchResultFormatter._format_result_list(search_results),
                "count": len(search_results),
            }

        else:
            return {
                "type": "unknown",
                "content": str(search_results),
                "original_type": type(search_results).__name__,
            }

    @staticmethod
    def _format_result_list(results: List) -> List[Dict]:
        """Format a list of search results."""
        formatted = []

        for result in results:
            if isinstance(result, dict):
                formatted_result = {
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                    "snippet": SearchResultFormatter._clean_snippet(
                        result.get("snippet", "")
                    ),
                    "metadata": {
                        k: v
                        for k, v in result.items()
                        if k not in ["title", "url", "snippet"]
                    },
                }
                formatted.append(formatted_result)
            else:
                formatted.append(
                    {
                        "title": "Raw Data",
                        "url": "",
                        "snippet": str(result),
                        "metadata": {"type": "non_dict_result"},
                    }
                )

        return formatted

    @staticmethod
    def _clean_snippet(snippet: str) -> str:
        """Clean snippet text for better LLM processing."""
        if not isinstance(snippet, str):
            return str(snippet)

        import re

        # Remove JSON-like artifacts
        snippet = re.sub(r'[{}"\']', "", snippet)
        snippet = re.sub(r"position:\s*\d+", "", snippet)
        snippet = re.sub(r"source:\s*\w+", "", snippet)
        snippet = re.sub(r"content_method:\s*\w+", "", snippet)

        # Clean whitespace
        snippet = re.sub(r"\s+", " ", snippet.strip())

        # Ensure reasonable length for LLM processing
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."

        return snippet
