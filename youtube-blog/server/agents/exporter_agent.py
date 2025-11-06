from docx import Document
from reportlab.pdfgen import canvas
import os
from datetime import datetime

def export_blog(blog_markdown: str, include_images: bool = True):
    # Get the server directory
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_dir = os.path.join(server_dir, "server")
    
    # Create outputs directory if it doesn't exist
    outputs_dir = os.path.join(server_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    # Generate unique filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    docx_filename = f"blog_output_{timestamp}.docx"
    pdf_filename = f"blog_output_{timestamp}.pdf"
    
    docx_path = os.path.join(outputs_dir, docx_filename)
    pdf_path = os.path.join(outputs_dir, pdf_filename)
    
    # Create DOCX
    doc = Document()
    # Split markdown into paragraphs for better formatting
    for line in blog_markdown.split('\n'):
        if line.strip():
            doc.add_paragraph(line.strip())
    doc.save(docx_path)
    
    # Create PDF
    c = canvas.Canvas(pdf_path)
    y_position = 800
    for line in blog_markdown.split('\n'):
        if line.strip():
            c.drawString(50, y_position, line.strip()[:100])
            y_position -= 15
            if y_position < 50:
                c.showPage()
                y_position = 800
    c.save()
    
    return {
        "docx_url": f"outputs/{docx_filename}",
        "pdf_url": f"outputs/{pdf_filename}"
    }