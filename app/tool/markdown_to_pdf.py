"""
Markdown to PDF Conversion Tool for ParManus AI Agent
"""
import markdown
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from pathlib import Path
import re
from html import unescape
from typing import Optional, Dict, Any

from app.tool.core.base import BaseTool, ToolConfig, ToolResult


class MarkdownToPDFTool(BaseTool):
    """Tool for converting Markdown files to PDF format."""
    
    def __init__(self, **kwargs):
        if "config" not in kwargs:
            kwargs["config"] = ToolConfig(
                name="markdown_to_pdf",
                description="Convert Markdown files to PDF format with professional styling",
                parameters={
                    "input_file": {
                        "type": "string",
                        "description": "Path to the input markdown file"
                    },
                    "output_file": {
                        "type": "string", 
                        "description": "Optional: Path for the output PDF file. If not provided, will use input filename with .pdf extension",
                        "required": False
                    },
                    "style": {
                        "type": "string",
                        "description": "PDF styling option: 'professional', 'simple', or 'report'",
                        "default": "professional",
                        "required": False
                    }
                }
            )
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        """Get tool name for compatibility."""
        return self.config.name

    def _execute(self, input_file: str, output_file: Optional[str] = None, style: str = "professional") -> ToolResult:
        """Execute the markdown to PDF conversion."""
        try:
            # Validate input file
            input_path = Path(input_file)
            if not input_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Input file not found: {input_file}"
                )
            
            if not input_path.suffix.lower() in ['.md', '.markdown']:
                return ToolResult(
                    success=False,
                    error=f"Input file must be a markdown file (.md or .markdown): {input_file}"
                )
            
            # Set output path
            if output_file is None:
                output_path = input_path.with_suffix('.pdf')
            else:
                output_path = Path(output_file)
                # Ensure .pdf extension
                if output_path.suffix.lower() != '.pdf':
                    output_path = output_path.with_suffix('.pdf')
            
            # Read markdown content
            with open(input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to HTML
            html = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'nl2br'])
            
            # Convert to PDF
            result_path = self._create_pdf(html, output_path, style)
            
            if result_path:
                file_size = output_path.stat().st_size
                return ToolResult(
                    success=True,
                    result={
                        "message": "Successfully converted markdown to PDF",
                        "input_file": str(input_path),
                        "output_file": str(output_path),
                        "file_size": file_size,
                        "style": style
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error="Failed to create PDF file"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error converting markdown to PDF: {str(e)}"
            )
    
    def _create_pdf(self, html_content: str, output_path: Path, style: str) -> Optional[str]:
        """Create PDF from HTML content with specified styling."""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path), 
                pagesize=A4,
                rightMargin=72, 
                leftMargin=72,
                topMargin=72, 
                bottomMargin=72
            )
            
            # Get and customize styles based on style parameter
            styles = getSampleStyleSheet()
            
            if style == "professional":
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=20,
                    spaceAfter=30,
                    textColor=colors.darkblue,
                    alignment=1  # Center alignment
                )
                
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=15,
                    spaceBefore=20,
                    textColor=colors.darkblue,
                    borderWidth=1,
                    borderColor=colors.lightgrey,
                    borderPadding=5
                )
                
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontSize=11,
                    spaceAfter=12,
                    leading=16
                )
                
            elif style == "report":
                title_style = ParagraphStyle(
                    'ReportTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=25,
                    textColor=colors.black,
                    alignment=1,
                    borderWidth=2,
                    borderColor=colors.darkblue,
                    borderPadding=10
                )
                
                heading_style = ParagraphStyle(
                    'ReportHeading',
                    parent=styles['Heading2'],
                    fontSize=13,
                    spaceAfter=12,
                    spaceBefore=15,
                    textColor=colors.darkred,
                    leftIndent=20
                )
                
                normal_style = ParagraphStyle(
                    'ReportNormal',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceAfter=10,
                    leading=14,
                    leftIndent=10
                )
                
            else:  # simple
                title_style = styles['Heading1']
                heading_style = styles['Heading2'] 
                normal_style = styles['Normal']
            
            # Story container
            story = []
            
            # Parse HTML and create PDF elements
            lines = html_content.split('\n')
            current_text = ""
            in_list = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_text:
                        clean_text = self._clean_html(current_text)
                        if clean_text.strip():
                            story.append(Paragraph(clean_text, normal_style))
                            story.append(Spacer(1, 12))
                        current_text = ""
                    continue
                
                # Handle headers
                if line.startswith('<h1>'):
                    if current_text:
                        clean_text = self._clean_html(current_text)
                        if clean_text.strip():
                            story.append(Paragraph(clean_text, normal_style))
                        current_text = ""
                    
                    title_text = self._clean_html(line)
                    story.append(Paragraph(title_text, title_style))
                    story.append(Spacer(1, 12))
                    
                elif line.startswith(('<h2>', '<h3>', '<h4>')):
                    if current_text:
                        clean_text = self._clean_html(current_text)
                        if clean_text.strip():
                            story.append(Paragraph(clean_text, normal_style))
                        current_text = ""
                    
                    heading_text = self._clean_html(line)
                    story.append(Paragraph(heading_text, heading_style))
                    story.append(Spacer(1, 8))
                    
                # Handle list items
                elif line.startswith('<li>'):
                    if current_text:
                        clean_text = self._clean_html(current_text)
                        if clean_text.strip():
                            story.append(Paragraph(clean_text, normal_style))
                        current_text = ""
                    
                    list_text = self._clean_html(line)
                    story.append(Paragraph(f"• {list_text}", normal_style))
                    in_list = True
                    
                elif line.startswith('</ul>') or line.startswith('</ol>'):
                    in_list = False
                    story.append(Spacer(1, 6))
                    
                # Handle horizontal rules
                elif line.startswith('<hr'):
                    if current_text:
                        clean_text = self._clean_html(current_text)
                        if clean_text.strip():
                            story.append(Paragraph(clean_text, normal_style))
                        current_text = ""
                    story.append(Spacer(1, 12))
                    
                # Accumulate other content
                else:
                    if not line.startswith(('<ul>', '<ol>', '<p>', '</p>')):
                        current_text += " " + line
            
            # Add any remaining text
            if current_text:
                clean_text = self._clean_html(current_text)
                if clean_text.strip():
                    story.append(Paragraph(clean_text, normal_style))
            
            # Build PDF
            doc.build(story)
            return str(output_path)
            
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return None
    
    def _clean_html(self, html_text: str) -> str:
        """Clean HTML tags and decode entities."""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        # Decode HTML entities
        clean_text = unescape(clean_text)
        # Clean up extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
