#!/usr/bin/env python3
"""
Automatic High-Quality Report Generator
This script integrates LLM-driven report generation into the agent workflow.
It can be called whenever the agent needs to create analysis reports.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent))

from app.config import load_config
from app.llm import create_llm
from app.logger import logger
from app.utils.llm_report_generator import LLMReportGenerator, SearchResultFormatter


async def generate_high_quality_report(
    query: str,
    research_data: Any,
    output_filename: Optional[str] = None,
    confidence_level: str = "Medium",
) -> Dict[str, Any]:
    """
    Generate a high-quality analysis report using LLM intelligence.

    Args:
        query: The original research query
        research_data: Raw research data (can be JSON string, dict, or list)
        output_filename: Optional custom filename
        confidence_level: Confidence level for the analysis

    Returns:
        Dictionary with generation results
    """

    logger.info(f"🎯 Generating high-quality report for: {query[:50]}...")

    try:
        # Initialize LLM and report generator
        config = load_config()
        llm = create_llm(config.llm)
        report_generator = LLMReportGenerator(llm)

        # Parse research data if it's a string
        if isinstance(research_data, str):
            try:
                if research_data.strip().startswith(("[", "{")):
                    research_data = json.loads(research_data)
                else:
                    # Treat as plain text
                    research_data = [{"content": research_data, "type": "text"}]
            except json.JSONDecodeError:
                research_data = [{"content": research_data, "type": "text"}]

        # Ensure research_data is a list
        if not isinstance(research_data, list):
            research_data = [research_data]

        # Format data for LLM
        formatted_data = []
        for item in research_data:
            formatted_item = SearchResultFormatter.format_for_llm_analysis(item)
            formatted_data.append(formatted_item)

        # Generate the report
        report_content = await report_generator.generate_analysis_report(
            query=query, research_data=formatted_data, confidence_level=confidence_level
        )

        # Determine output filename
        if not output_filename:
            # Generate filename from query
            clean_query = "".join(
                c for c in query if c.isalnum() or c.isspace()
            ).strip()
            clean_query = "_".join(clean_query.lower().split()[:6])  # Max 6 words
            output_filename = f"{clean_query}_analysis.md"

        # Ensure .md extension
        if not output_filename.endswith(".md"):
            output_filename += ".md"

        # Save to workspace
        workspace_root = Path("workspace")
        output_path = workspace_root / output_filename

        workspace_root.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        result = {
            "success": True,
            "output_file": str(output_path),
            "query": query,
            "confidence_level": confidence_level,
            "data_sources": len(formatted_data),
            "report_length": len(report_content),
            "message": "High-quality analysis report generated successfully",
        }

        logger.info(f"✅ Report generated: {output_path}")
        return result

    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
        return {"success": False, "error": str(e), "query": query}


def main():
    """Command line interface for report generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate high-quality analysis reports using LLM"
    )
    parser.add_argument("query", help="Research query or topic")
    parser.add_argument("--data", help="Research data (JSON string or file path)")
    parser.add_argument("--data-file", help="Path to file containing research data")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument(
        "--confidence",
        choices=["High", "Medium", "Low"],
        default="Medium",
        help="Confidence level",
    )

    args = parser.parse_args()

    # Get research data
    research_data = None
    if args.data:
        research_data = args.data
    elif args.data_file:
        try:
            with open(args.data_file, "r", encoding="utf-8") as f:
                research_data = f.read()
        except Exception as e:
            print(f"❌ Error reading data file: {e}")
            return False
    else:
        print("❌ Either --data or --data-file must be provided")
        return False

    # Generate report
    print(f"🚀 Generating report for: {args.query}")

    result = asyncio.run(
        generate_high_quality_report(
            query=args.query,
            research_data=research_data,
            output_filename=args.output,
            confidence_level=args.confidence,
        )
    )

    if result["success"]:
        print(f"✅ Success: {result['message']}")
        print(f"📄 Output: {result['output_file']}")
        print(f"📊 Sources: {result['data_sources']}")
        print(f"📏 Length: {result['report_length']} characters")
    else:
        print(f"❌ Failed: {result['error']}")
        return False

    return True


# Example usage functions for integration
async def process_search_results_into_report(
    search_results: List[Dict], query: str
) -> str:
    """
    Process search results into a high-quality report.
    This function can be called from the agent workflow.
    """
    result = await generate_high_quality_report(
        query=query, research_data=search_results, confidence_level="High"
    )

    if result["success"]:
        return result["output_file"]
    else:
        raise Exception(f"Report generation failed: {result['error']}")


async def enhance_existing_report(existing_report_path: str, query: str) -> str:
    """
    Enhance an existing report using LLM intelligence.
    """
    try:
        # Read existing report
        with open(existing_report_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Extract research data from existing report (basic approach)
        research_data = [{"content": existing_content, "type": "existing_report"}]

        # Generate enhanced report
        result = await generate_high_quality_report(
            query=f"Enhance and improve this analysis: {query}",
            research_data=research_data,
            output_filename=f"enhanced_{Path(existing_report_path).name}",
            confidence_level="High",
        )

        if result["success"]:
            return result["output_file"]
        else:
            raise Exception(f"Report enhancement failed: {result['error']}")

    except Exception as e:
        logger.error(f"❌ Error enhancing report: {e}")
        raise


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
