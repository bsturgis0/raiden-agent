import os
from pathlib import Path
from typing import List
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from langchain_core.tools import tool

try:
    from app import WORKSPACE_DIR, _resolve_safe_path
except ImportError:
    WORKSPACE_DIR = Path("./raiden_workspace_srv")
    def _resolve_safe_path(filename: str) -> Path:
        return WORKSPACE_DIR / filename

@tool
def merge_pdfs(file_paths: List[str], output_filename: str) -> str:
    """Merges multiple PDF files into one."""
    try:
        merger = PyPDF2.PdfMerger()
        
        # Add each PDF to the merger
        for file_path in file_paths:
            pdf_path = _resolve_safe_path(file_path)
            if not pdf_path.exists():
                return f"Error: PDF file '{file_path}' not found"
            merger.append(str(pdf_path))
            
        # Save merged PDF
        output_path = _resolve_safe_path(output_filename)
        merger.write(str(output_path))
        merger.close()
        
        return f"PDFs merged successfully into '{output_filename}'"
    except Exception as e:
        return f"Error merging PDFs: {str(e)}"

@tool
def add_watermark(pdf_path: str, watermark_text: str, output_filename: str = None) -> str:
    """Adds a text watermark to each page of a PDF."""
    try:
        input_path = _resolve_safe_path(pdf_path)
        if not input_path.exists():
            return f"Error: PDF file '{pdf_path}' not found"
            
        output_path = _resolve_safe_path(output_filename or f"watermarked_{pdf_path}")
        
        # Create watermark
        watermark_path = _resolve_safe_path("temp_watermark.pdf")
        c = canvas.Canvas(str(watermark_path), pagesize=letter)
        c.setFillColorRGB(0.5, 0.5, 0.5, 0.3)  # Gray, 30% opacity
        c.setFont("Helvetica", 50)
        c.saveState()
        c.translate(300, 400)
        c.rotate(45)
        c.drawString(0, 0, watermark_text)
        c.restoreState()
        c.save()
        
        # Apply watermark to each page
        with open(input_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            watermark = PyPDF2.PdfReader(str(watermark_path))
            writer = PyPDF2.PdfWriter()
            
            for page in reader.pages:
                page.merge_page(watermark.pages[0])
                writer.add_page(page)
                
            with open(output_path, 'wb') as output:
                writer.write(output)
                
        # Clean up temporary watermark
        watermark_path.unlink()
        
        return f"Watermark added and saved as '{output_path.name}'"
    except Exception as e:
        return f"Error adding watermark: {str(e)}"

@tool
def extract_pdf_pages(pdf_path: str, pages: str, output_filename: str = None) -> str:
    """Extracts specific pages from a PDF. Pages format: '1,3-5,7'"""
    try:
        input_path = _resolve_safe_path(pdf_path)
        if not input_path.exists():
            return f"Error: PDF file '{pdf_path}' not found"
            
        output_path = _resolve_safe_path(output_filename or f"extracted_{pdf_path}")
        
        # Parse page ranges
        page_numbers = set()
        for part in pages.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                page_numbers.update(range(start, end + 1))
            else:
                page_numbers.add(int(part))
                
        # Extract pages
        writer = PyPDF2.PdfWriter()
        with open(input_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in sorted(page_numbers):
                if 1 <= page_num <= len(reader.pages):
                    writer.add_page(reader.pages[page_num - 1])
                    
            with open(output_path, 'wb') as output:
                writer.write(output)
                
        return f"Pages extracted and saved as '{output_path.name}'"
    except Exception as e:
        return f"Error extracting pages: {str(e)}"
