"""
Generate PDF API documentation from markdown using xhtml2pdf (Windows-friendly).
"""
import sys
from pathlib import Path

try:
    import markdown
    from xhtml2pdf import pisa
except ImportError as e:
    print(
        f"❌ Missing dependency: {e}\n"
        "Install the docs extras with: uv sync --group docs"
    )
    sys.exit(1)

def generate_pdf(markdown_path: Path, output_path: Path):
    """Convert markdown to PDF with styling using xhtml2pdf."""
    
    # Custom CSS for professional documentation styling
    css_content = """
    body {
        font-family: Helvetica, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.6;
        color: #333;
        margin: 40px;
    }
    
    h1 {
        color: #0066cc;
        font-size: 22pt;
        margin-top: 20pt;
        padding-bottom: 8px;
        border-bottom: 3px solid #0066cc;
    }
    
    h2 {
        color: #0066cc;
        font-size: 16pt;
        margin-top: 18pt;
        margin-bottom: 8pt;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 4px;
    }
    
    h3 {
        color: #0088cc;
        font-size: 13pt;
        margin-top: 14pt;
        margin-bottom: 6pt;
    }
    
    h4 {
        color: #0088cc;
        font-size: 11pt;
        margin-top: 10pt;
        margin-bottom: 5pt;
    }
    
    code {
        font-family: Courier, monospace;
        background-color: #f5f5f5;
        padding: 2px 4px;
        font-size: 9pt;
        color: #c7254e;
    }
    
    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-left: 4px solid #0066cc;
        padding: 10px;
        font-size: 8pt;
        font-family: Courier, monospace;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
        color: #333;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 8pt;
    }
    
    table th {
        background-color: #0066cc;
        color: white;
        padding: 8px;
        text-align: left;
        font-weight: bold;
    }
    
    table td {
        border: 1px solid #ddd;
        padding: 6px;
    }
    
    table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    blockquote {
        border-left: 4px solid #0066cc;
        padding-left: 12px;
        margin-left: 0;
        color: #666;
        font-style: italic;
    }
    
    a {
        color: #0066cc;
        text-decoration: none;
    }
    
    hr {
        border: none;
        border-top: 2px solid #e0e0e0;
        margin: 15px 0;
    }
    
    .page-break {
        page-break-after: always;
    }
    
    @page {
        size: a4;
        margin: 2cm;
        @frame footer {
            -pdf-frame-content: footerContent;
            bottom: 1cm;
            margin-left: 1cm;
            margin-right: 1cm;
            height: 1cm;
        }
    }
    """
    
    # Read markdown content
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML with Python markdown library
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
    
    md = markdown.Markdown(extensions=[
        TableExtension(),
        FencedCodeExtension(),
        'extra'
    ])
    
    html_content = md.convert(markdown_content)
    
    # Wrap in full HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>AeroInsight API Documentation</title>
        <style>
            {css_content}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generate PDF using xhtml2pdf
    with open(output_path, 'wb') as pdf_file:
        pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
    
    if pisa_status.err:
        print(f"❌ Error generating PDF: {pisa_status.err}")
        sys.exit(1)
    
    print(f"✅ PDF generated: {output_path}")
    print(f"📄 Size: {output_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    markdown_path = root / "docs" / "API_DOCUMENTATION.md"
    output_path = root / "docs" / "API_DOCUMENTATION.pdf"
    
    if not markdown_path.exists():
        print(f"❌ Error: {markdown_path} not found")
        sys.exit(1)
    
    # Ensure docs directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    generate_pdf(markdown_path, output_path)
