"""
Convert Markdown to PDF using Python
"""
import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import sys

def md_to_pdf(md_file_path, output_pdf_path=None):
    """Convert Markdown file to PDF"""
    
    # Read the markdown file
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # Add basic CSS styling
    styled_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 0.75in;
            }}
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 10px;
            }}
            ul, ol {{
                padding-left: 20px;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 0;
                padding-left: 20px;
                font-style: italic;
            }}
            code {{
                background-color: #f8f9fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #f8f9fa;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    
    # Set output path
    if output_pdf_path is None:
        md_path = Path(md_file_path)
        output_pdf_path = md_path.with_suffix('.pdf')
    
    try:
        # Convert HTML to PDF using weasyprint
        html_doc = HTML(string=styled_html)
        html_doc.write_pdf(output_pdf_path)
        print(f"✅ Successfully converted to PDF: {output_pdf_path}")
        return str(output_pdf_path)
    except Exception as e:
        print(f"❌ Error converting to PDF: {e}")
        print("💡 Make sure weasyprint is installed: pip install weasyprint")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf.py <markdown_file> [output_pdf]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    md_to_pdf(md_file, output_file)
