"""
Convert Markdown to PDF using Python (Windows-friendly version)
"""
import re
import sys
from html import unescape
from pathlib import Path

import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)


def md_to_pdf_simple(md_file_path, output_pdf_path=None):
    """Convert Markdown file to PDF using reportlab"""

    # Read the markdown file
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert markdown to HTML
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

    # Set output path
    if output_pdf_path is None:
        md_path = Path(md_file_path)
        output_pdf_path = md_path.with_suffix('.pdf')

    # Create PDF document
    doc = SimpleDocTemplate(str(output_pdf_path), pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)

    # Get styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue,
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
    )

    # Story container
    story = []

    # Parse HTML and create PDF elements
    lines = html.split('\n')
    current_text = ""

    for line in lines:
        line = line.strip()
        if not line:
            if current_text:
                # Add accumulated text as paragraph
                clean_text = re.sub(r'<[^>]+>', '', current_text)
                clean_text = unescape(clean_text)
                if clean_text.strip():
                    story.append(Paragraph(clean_text, normal_style))
                    story.append(Spacer(1, 12))
                current_text = ""
            continue

        # Handle headers
        if line.startswith('<h1>'):
            if current_text:
                clean_text = re.sub(r'<[^>]+>', '', current_text)
                clean_text = unescape(clean_text)
                if clean_text.strip():
                    story.append(Paragraph(clean_text, normal_style))
                current_text = ""

            title_text = re.sub(r'<[^>]+>', '', line)
            title_text = unescape(title_text)
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 12))

        elif line.startswith('<h2>') or line.startswith('<h3>'):
            if current_text:
                clean_text = re.sub(r'<[^>]+>', '', current_text)
                clean_text = unescape(clean_text)
                if clean_text.strip():
                    story.append(Paragraph(clean_text, normal_style))
                current_text = ""

            heading_text = re.sub(r'<[^>]+>', '', line)
            heading_text = unescape(heading_text)
            story.append(Paragraph(heading_text, heading_style))
            story.append(Spacer(1, 12))

        # Handle list items
        elif line.startswith('<li>'):
            if current_text:
                clean_text = re.sub(r'<[^>]+>', '', current_text)
                clean_text = unescape(clean_text)
                if clean_text.strip():
                    story.append(Paragraph(clean_text, normal_style))
                current_text = ""

            list_text = re.sub(r'<[^>]+>', '', line)
            list_text = unescape(list_text)
            story.append(Paragraph(f"• {list_text}", normal_style))

        # Accumulate other content
        else:
            current_text += " " + line

    # Add any remaining text
    if current_text:
        clean_text = re.sub(r'<[^>]+>', '', current_text)
        clean_text = unescape(clean_text)
        if clean_text.strip():
            story.append(Paragraph(clean_text, normal_style))

    try:
        # Build PDF
        doc.build(story)
        print(f"✅ Successfully converted to PDF: {output_pdf_path}")
        return str(output_pdf_path)
    except Exception as e:
        print(f"❌ Error converting to PDF: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf_simple.py <markdown_file> [output_pdf]")
        sys.exit(1)

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    md_to_pdf_simple(md_file, output_file)
