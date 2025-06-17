"""
LLM Response Parser Module
Handles parsing and extracting information from LLM responses
"""

import re
from typing import Dict, List, Optional, Tuple

from app.logger import logger


class LLMResponseParser:
    """
    Specialized module for parsing LLM responses and extracting structured information
    """

    def __init__(self):
        self.relevance_patterns = self._initialize_relevance_patterns()

    def _initialize_relevance_patterns(self) -> List[str]:
        """Initialize patterns for parsing relevance decisions"""
        return [
            r"(\d+)\.\s*(RELEVANT|IRRELEVANT)",
            r"(\d+):\s*(RELEVANT|IRRELEVANT)",
            r"Result\s*(\d+):\s*(RELEVANT|IRRELEVANT)",
            r"(\d+)\s*-\s*(RELEVANT|IRRELEVANT)",
        ]

    def parse_relevance_decisions(
        self, llm_response: str, search_results: List[Dict]
    ) -> Tuple[List[Dict], List[str]]:
        """
        Parse LLM relevance decisions and return filtered results

        Args:
            llm_response: The raw response from LLM
            search_results: Original search results list

        Returns:
            Tuple of (relevant_results, parsing_errors)
        """
        relevant_results = []
        parsing_errors = []

        lines = self._clean_response_lines(llm_response)

        for line in lines:
            try:
                result_index, decision = self._extract_relevance_decision(line)

                if result_index is not None and decision is not None:
                    # Convert to 0-based index
                    idx = result_index - 1

                    if 0 <= idx < len(search_results):
                        if decision.upper() == "RELEVANT":
                            search_results[idx][
                                "relevance_score"
                            ] = 5  # High score for LLM-validated
                            relevant_results.append(search_results[idx])
                            logger.info(
                                f"✅ LLM kept: {search_results[idx].get('title', '')[:50]}..."
                            )
                        else:
                            logger.warning(
                                f"🚫 LLM filtered: {search_results[idx].get('title', '')[:50]}..."
                            )
                    else:
                        parsing_errors.append(
                            f"Index {result_index} out of range for line: {line}"
                        )

            except Exception as e:
                parsing_errors.append(f"Error parsing line '{line}': {str(e)}")
                continue

        # Sort by relevance score
        relevant_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        logger.info(
            f"🤖 LLM validation: {len(relevant_results)} relevant, "
            f"{len(search_results) - len(relevant_results)} filtered out"
        )

        return relevant_results, parsing_errors

    def _clean_response_lines(self, response: str) -> List[str]:
        """Clean and split response into parseable lines"""
        lines = response.strip().split("\\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line and not self._is_header_or_instruction(line):
                cleaned_lines.append(line)

        return cleaned_lines

    def _is_header_or_instruction(self, line: str) -> bool:
        """Check if line is a header or instruction rather than a decision"""
        header_patterns = [
            "output format",
            "analysis",
            "results",
            "for each result",
            "analyze",
            "determine",
            "filter",
            "keep",
            "be strict",
        ]

        return any(pattern in line.lower() for pattern in header_patterns)

    def _extract_relevance_decision(
        self, line: str
    ) -> Tuple[Optional[int], Optional[str]]:
        """Extract result index and relevance decision from a line"""
        for pattern in self.relevance_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    result_index = int(match.group(1))
                    decision = match.group(2).upper()
                    return result_index, decision
                except (ValueError, IndexError):
                    continue

        return None, None

    def parse_structured_content(self, llm_response: str) -> Dict[str, str]:
        """
        Parse LLM response into structured sections (Executive Summary, Key Findings, etc.)

        Args:
            llm_response: The raw LLM response

        Returns:
            Dictionary with section names as keys and content as values
        """
        sections = {}
        current_section = None
        current_content = []

        lines = llm_response.split("\\n")

        for line in lines:
            line = line.strip()

            # Check if this is a section header
            section_name = self._identify_section_header(line)

            if section_name:
                # Save previous section if it exists
                if current_section and current_content:
                    sections[current_section] = "\\n".join(current_content).strip()

                # Start new section
                current_section = section_name
                current_content = []
            elif current_section and line:
                # Add content to current section
                current_content.append(line)

        # Save the last section
        if current_section and current_content:
            sections[current_section] = "\\n".join(current_content).strip()

        return sections

    def _identify_section_header(self, line: str) -> Optional[str]:
        """Identify if a line is a section header and return standardized section name"""
        line_lower = line.lower()

        section_mappings = {
            "executive summary": "executive_summary",
            "key findings": "key_findings",
            "recommendations": "recommendations",
            "next steps": "next_steps",
            "analysis": "analysis",
            "conclusion": "conclusion",
            "data analysis": "data_analysis",
            "research findings": "research_findings",
        }

        for header, section_name in section_mappings.items():
            if header in line_lower and (
                line.startswith("#")
                or line.endswith(":")
                or line.isupper()
                or "**" in line
            ):
                return section_name

        return None

    def extract_key_points(self, text: str) -> List[str]:
        """Extract bullet points or numbered lists from text"""
        key_points = []

        # Look for bullet points
        bullet_pattern = r"^[•\\-\\*]\\s*(.+)$"

        # Look for numbered points
        number_pattern = r"^\\d+\\.\\s*(.+)$"

        lines = text.split("\\n")

        for line in lines:
            line = line.strip()

            # Check bullet points
            bullet_match = re.match(bullet_pattern, line)
            if bullet_match:
                key_points.append(bullet_match.group(1).strip())
                continue

            # Check numbered points
            number_match = re.match(number_pattern, line)
            if number_match:
                key_points.append(number_match.group(1).strip())

        return key_points

    def validate_response_completeness(
        self, sections: Dict[str, str]
    ) -> Dict[str, bool]:
        """Validate that LLM response contains expected sections"""
        required_sections = [
            "executive_summary",
            "key_findings",
            "recommendations",
            "next_steps",
        ]

        validation_results = {}

        for section in required_sections:
            has_content = section in sections and len(sections[section].strip()) > 20
            validation_results[section] = has_content

        return validation_results
