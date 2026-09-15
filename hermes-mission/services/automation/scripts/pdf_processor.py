#!/usr/bin/env python3
"""
PDF Processor Automation Script
Merge, split, extract text, and watermark PDF files.
"""

import argparse
from pathlib import Path

try:
    from PyPDF2 import PdfReader, PdfWriter, PdfMerger
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def merge_pdfs(input_files, output_file):
    """Merge multiple PDF files into one."""
    if not HAS_PYPDF2:
        print("Error: PyPDF2 required for PDF operations.")
        return

    merger = PdfMerger()
    for pdf_file in input_files:
        if Path(pdf_file).exists():
            merger.append(pdf_file)
            print(f"Added: {pdf_file}")
        else:
            print(f"Warning: File not found: {pdf_file}")

    merger.write(output_file)
    merger.close()
    print(f"Merged PDF saved to: {output_file}")
    return output_file


def split_pdf(input_file, output_dir=None, pages_per_split=1):
    """Split a PDF into multiple files."""
    if not HAS_PYPDF2:
        print("Error: PyPDF2 required for PDF operations.")
        return

    input_path = Path(input_file)
    output_dir = Path(output_dir) if output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(input_file)
    total_pages = len(reader.pages)
    output_files = []

    for start in range(0, total_pages, pages_per_split):
        writer = PdfWriter()
        end = min(start + pages_per_split, total_pages)
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        output_file = output_dir / f"{input_path.stem}_part_{start // pages_per_split + 1}.pdf"
        with open(output_file, 'wb') as f:
            writer.write(f)
        output_files.append(str(output_file))
        print(f"Created: {output_file} (pages {start + 1}-{end})")

    print(f"\nSplit into {len(output_files)} files.")
    return output_files


def extract_text(input_file, output_file=None):
    """Extract text from a PDF."""
    if not HAS_PYPDF2:
        print("Error: PyPDF2 required for PDF operations.")
        return

    reader = PdfReader(input_file)
    text = ""
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text += f"\n--- Page {i + 1} ---\n{page_text}"

    if output_file:
        with open(output_file, 'w') as f:
            f.write(text)
        print(f"Text extracted to: {output_file}")
    else:
        print(text)
    return text


def add_watermark(input_file, watermark_text, output_file):
    """Add a text watermark to each page of a PDF."""
    if not HAS_PYPDF2 or not HAS_REPORTLAB:
        print("Error: PyPDF2 and reportlab required for watermarking.")
        return

    # Create watermark PDF
    watermark_file = "_watermark_temp.pdf"
    c = canvas.Canvas(watermark_file, pagesize=letter)
    c.setFont("Helvetica", 60)
    c.setFillAlpha(0.1)
    c.saveState()
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    c.save()

    # Apply watermark
    reader = PdfReader(input_file)
    watermark_reader = PdfReader(watermark_file)
    watermark_page = watermark_reader.pages[0]

    writer = PdfWriter()
    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    with open(output_file, 'wb') as f:
        writer.write(f)

    # Cleanup temp file
    Path(watermark_file).unlink()
    print(f"Watermarked PDF saved to: {output_file}")
    return output_file


def rotate_pages(input_file, rotation, output_file, pages=None):
    """Rotate pages in a PDF."""
    if not HAS_PYPDF2:
        print("Error: PyPDF2 required for PDF operations.")
        return

    reader = PdfReader(input_file)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if pages is None or (i + 1) in pages:
            page.rotate(rotation)
        writer.add_page(page)

    with open(output_file, 'wb') as f:
        writer.write(f)
    print(f"Rotated PDF saved to: {output_file}")
    return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process PDF files')
    subparsers = parser.add_subparsers(dest='command')

    # Merge
    merge_parser = subparsers.add_parser('merge', help='Merge PDF files')
    merge_parser.add_argument('files', nargs='+', help='PDF files to merge')
    merge_parser.add_argument('-o', '--output', default='merged.pdf', help='Output file')

    # Split
    split_parser = subparsers.add_parser('split', help='Split PDF file')
    split_parser.add_argument('file', help='PDF file to split')
    split_parser.add_argument('--pages-per-split', type=int, default=1)
    split_parser.add_argument('-o', '--output-dir', help='Output directory')

    # Extract text
    extract_parser = subparsers.add_parser('extract', help='Extract text from PDF')
    extract_parser.add_argument('file', help='PDF file')
    extract_parser.add_argument('-o', '--output', help='Output text file')

    # Watermark
    watermark_parser = subparsers.add_parser('watermark', help='Add watermark to PDF')
    watermark_parser.add_argument('file', help='PDF file')
    watermark_parser.add_argument('--text', required=True, help='Watermark text')
    watermark_parser.add_argument('-o', '--output', default='watermarked.pdf')

    # Rotate
    rotate_parser = subparsers.add_parser('rotate', help='Rotate PDF pages')
    rotate_parser.add_argument('file', help='PDF file')
    rotate_parser.add_argument('--degrees', type=int, choices=[90, 180, 270], required=True)
    rotate_parser.add_argument('-o', '--output', default='rotated.pdf')
    rotate_parser.add_argument('--pages', nargs='+', type=int, help='Specific pages to rotate')

    args = parser.parse_args()

    if args.command == 'merge':
        merge_pdfs(args.files, args.output)
    elif args.command == 'split':
        split_pdf(args.file, args.output_dir, args.pages_per_split)
    elif args.command == 'extract':
        extract_text(args.file, args.output)
    elif args.command == 'watermark':
        add_watermark(args.file, args.text, args.output)
    elif args.command == 'rotate':
        rotate_pages(args.file, args.degrees, args.output, args.pages)
    else:
        parser.print_help()
