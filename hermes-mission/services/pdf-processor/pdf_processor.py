#!/usr/bin/env python3
"""
PDF Processing/OCR Service for Mr Bubba Services
Extracts text, tables, and data from PDFs into structured formats (CSV, Excel, Word).
"""

import argparse
import csv
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

# PDF text extraction
try:
    import PyPDF2
except ImportError:
    print("ERROR: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)

# OCR
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("WARNING: pytesseract/Pillow not available. OCR disabled.")

# Excel output
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("WARNING: openpyxl not available. Excel output disabled.")

# Word output
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    WORD_AVAILABLE = True
except ImportError:
    WORD_AVAILABLE = False
    print("WARNING: python-docx not available. Word output disabled.")


class PDFProcessor:
    """Process PDF files and extract text, tables, and data."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            "source_file": "",
            "pages": 0,
            "text_content": [],
            "tables": [],
            "ocr_text": [],
            "metadata": {},
        }

    def extract_text_pypdf2(self, pdf_path: str) -> list[str]:
        """Extract text using PyPDF2 (fast, good for text-based PDFs)."""
        texts = []
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                self.results["pages"] = len(reader.pages)
                self.results["metadata"] = reader.metadata or {}
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        texts.append(text.strip())
                    else:
                        texts.append("")  # Empty page flag for OCR fallback
        except Exception as e:
            print(f"PyPDF2 extraction error: {e}")
        return texts

    def extract_text_pdfplumber(self, pdf_path: str) -> list[str]:
        """Extract text using pdfplumber (better accuracy for complex layouts)."""
        texts = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        texts.append(text.strip())
                    else:
                        texts.append("")
        except Exception as e:
            print(f"pdfplumber extraction error: {e}")
        return texts

    def extract_tables_pdfplumber(self, pdf_path: str) -> list[list[list[str]]]:
        """Extract tables from PDF using pdfplumber."""
        all_tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            # Clean up None values
                            cleaned = []
                            for row in table:
                                cleaned_row = [
                                    cell.strip() if cell else ""
                                    for cell in row
                                ]
                                cleaned.append(cleaned_row)
                            all_tables.append({
                                "page": page_num,
                                "data": cleaned,
                            })
        except Exception as e:
            print(f"Table extraction error: {e}")
        return all_tables

    def extract_tables_camelot(self, pdf_path: str) -> list[dict]:
        """Extract tables using camelot (high accuracy for complex tables)."""
        try:
            import camelot
            tables = camelot.read_pdf(pdf_path, pages="all")
            results = []
            for table in tables:
                results.append({
                    "page": table.page,
                    "accuracy": table.accuracy,
                    "data": table.df.values.tolist(),
                    "headers": table.df.columns.tolist(),
                })
            return results
        except ImportError:
            print("camelot not available, using pdfplumber for tables")
            return []
        except Exception as e:
            print(f"Camelot extraction error: {e}")
            return []

    def ocr_pdf(self, pdf_path: str, lang: str = "eng") -> list[str]:
        """OCR PDF pages using pytesseract (for scanned/image-based PDFs)."""
        if not OCR_AVAILABLE:
            print("OCR not available (pytesseract/Pillow not installed)")
            return []

        ocr_texts = []
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(pdf_path, dpi=300)
            for i, image in enumerate(images, 1):
                text = pytesseract.image_to_string(image, lang=lang)
                if text.strip():
                    ocr_texts.append(text.strip())
                else:
                    ocr_texts.append("")
        except ImportError:
            print("pdf2image not installed. Install with: pip install pdf2image")
            print("Also requires poppler: sudo apt install poppler-utils")
        except Exception as e:
            print(f"OCR error: {e}")

        return ocr_texts

    def extract_images(self, pdf_path: str) -> list[dict]:
        """Extract images from PDF."""
        images_info = []
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    if "/XObject" in page["/Resources"]:
                        xobjects = page["/Resources"]["/XObject"]
                        for obj_name, obj_ref in xobjects.items():
                            obj = obj_ref.get_object()
                            if obj.get("/Subtype") == "/Image":
                                images_info.append({
                                    "page": page_num,
                                    "name": obj_name,
                                    "width": obj.get("/Width", 0),
                                    "height": obj.get("/Height", 0),
                                    "filter": str(obj.get("/Filter", "")),
                                })
        except Exception as e:
            print(f"Image extraction error: {e}")
        return images_info

    def process_pdf(
        self,
        pdf_path: str,
        extract_text: bool = True,
        extract_tables: bool = True,
        use_ocr: bool = False,
        ocr_lang: str = "eng",
    ) -> dict:
        """Process a PDF file with all enabled extraction methods."""
        self.results["source_file"] = str(Path(pdf_path).name)

        # Text extraction
        if extract_text:
            # Try pdfplumber first for accuracy
            texts = self.extract_text_pdfplumber(pdf_path)
            if not any(texts):
                # Fall back to PyPDF2
                texts = self.extract_text_pypdf2(pdf_path)
            self.results["text_content"] = texts

        # Table extraction
        if extract_tables:
            tables = self.extract_tables_pdfplumber(pdf_path)
            self.results["tables"] = tables

        # OCR (for scanned PDFs)
        if use_ocr:
            ocr_texts = self.ocr_pdf(pdf_path, lang=ocr_lang)
            self.results["ocr_text"] = ocr_texts

        return self.results

    def save_to_csv(self, tables: list = None, filename: str = "extracted_data.csv") -> str:
        """Save extracted tables to CSV file."""
        if tables is None:
            tables = self.results.get("tables", [])

        output_path = self.output_dir / filename

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for i, table_info in enumerate(tables):
                writer.writerow([f"--- Table {i + 1} (Page {table_info['page']}) ---"])
                for row in table_info["data"]:
                    writer.writerow(row)
                writer.writerow([])  # Blank separator

        print(f"CSV saved: {output_path}")
        return str(output_path)

    def save_to_excel(self, tables: list = None, text: list = None, filename: str = "extracted_data.xlsx") -> str:
        """Save extracted data to Excel workbook."""
        if not EXCEL_AVAILABLE:
            print("Excel output not available (openpyxl not installed)")
            return ""

        if tables is None:
            tables = self.results.get("tables", [])
        if text is None:
            text = self.results.get("text_content", [])

        output_path = self.output_dir / filename
        wb = Workbook()

        # Text content sheet
        if text:
            ws_text = wb.active
            ws_text.title = "Text Content"
            ws_text.append(["Page", "Text"])
            ws_text["A1"].font = Font(bold=True)
            ws_text["B1"].font = Font(bold=True)

            for i, page_text in enumerate(text, 1):
                ws_text.append([i, page_text])

            # Auto-width for text column
            ws_text.column_dimensions["A"].width = 8
            ws_text.column_dimensions["B"].width = 100

        # Table sheets
        for i, table_info in enumerate(tables):
            sheet_name = f"Table_{i + 1}_P{table_info['page']}"
            ws_table = wb.create_sheet(title=sheet_name[:31])  # Excel sheet name max 31 chars

            for row_idx, row_data in enumerate(table_info["data"], 1):
                ws_table.append(row_data)
                if row_idx == 1 and row_data:
                    for col_idx in range(len(row_data)):
                        cell = ws_table.cell(row=1, column=col_idx + 1)
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(
                            start_color="4472C4",
                            end_color="4472C4",
                            fill_type="solid",
                        )
                        cell.font = Font(bold=True, color="FFFFFF")

        wb.save(output_path)
        print(f"Excel saved: {output_path}")
        return str(output_path)

    def save_to_word(self, text: list = None, tables: list = None, filename: str = "extracted_data.docx") -> str:
        """Save extracted data to Word document."""
        if not WORD_AVAILABLE:
            print("Word output not available (python-docx not installed)")
            return ""

        if text is None:
            text = self.results.get("text_content", [])
        if tables is None:
            tables = self.results.get("tables", [])

        output_path = self.output_dir / filename
        doc = Document()

        # Title
        title = doc.add_heading("Extracted PDF Content", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Source file info
        doc.add_paragraph(f"Source: {self.results.get('source_file', 'Unknown')}")
        doc.add_paragraph(f"Pages: {self.results.get('pages', 0)}")
        doc.add_paragraph("")

        # Text content
        if text:
            doc.add_heading("Text Content", level=1)
            for i, page_text in enumerate(text, 1):
                doc.add_heading(f"Page {i}", level=3)
                doc.add_paragraph(page_text)

        # Tables
        if tables:
            doc.add_heading("Extracted Tables", level=1)
            for i, table_info in enumerate(tables):
                doc.add_heading(f"Table {i + 1} (Page {table_info['page']})", level=3)

                data = table_info["data"]
                if data:
                    num_cols = max(len(row) for row in data)
                    table = doc.add_table(rows=len(data), cols=num_cols)
                    table.style = "Table Grid"

                    for row_idx, row_data in enumerate(data):
                        for col_idx in range(num_cols):
                            cell = table.cell(row_idx, col_idx)
                            cell.text = row_data[col_idx] if col_idx < len(row_data) else ""
                            if row_idx == 0:
                                for paragraph in cell.paragraphs:
                                    for run in paragraph.runs:
                                        run.bold = True

                doc.add_paragraph("")  # Spacing

        doc.save(output_path)
        print(f"Word document saved: {output_path}")
        return str(output_path)

    def save_text(self, filename: str = "extracted_text.txt") -> str:
        """Save extracted text to plain text file."""
        text = self.results.get("text_content", [])
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Source: {self.results.get('source_file', 'Unknown')}\n")
            f.write(f"Pages: {self.results.get('pages', 0)}\n")
            f.write("=" * 80 + "\n\n")
            for i, page_text in enumerate(text, 1):
                f.write(f"--- Page {i} ---\n")
                f.write(page_text + "\n\n")

        print(f"Text file saved: {output_path}")
        return str(output_path)

    def save_json(self, filename: str = "extraction_report.json") -> str:
        """Save full extraction results as JSON."""
        output_path = self.output_dir / filename

        # Make a copy for JSON serialization
        report = {
            "source_file": self.results["source_file"],
            "pages": self.results["pages"],
            "metadata": str(self.results.get("metadata", {})),
            "num_text_pages": len(self.results.get("text_content", [])),
            "num_tables": len(self.results.get("tables", [])),
            "num_ocr_pages": len(self.results.get("ocr_text", [])),
            "text_content": self.results.get("text_content", []),
            "tables": self.results.get("tables", []),
            "ocr_text": self.results.get("ocr_text", []),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"JSON report saved: {output_path}")
        return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="PDF Processing/OCR Service - Extract text, tables, and data from PDFs"
    )
    parser.add_argument("pdf_file", help="Path to PDF file to process")
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Output directory for extracted files (default: output)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "excel", "word", "txt", "json", "all"],
        default="all",
        help="Output format (default: all)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR for scanned/image-based PDFs",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="OCR language (default: eng)",
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Skip table extraction",
    )
    parser.add_argument(
        "--no-text",
        action="store_true",
        help="Skip text extraction",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.pdf_file):
        print(f"ERROR: File not found: {args.pdf_file}")
        sys.exit(1)

    processor = PDFProcessor(output_dir=args.output_dir)

    print(f"Processing: {args.pdf_file}")
    print(f"Output directory: {args.output_dir}")
    if args.ocr:
        print(f"OCR enabled (language: {args.ocr_lang})")
    print("-" * 60)

    results = processor.process_pdf(
        args.pdf_file,
        extract_text=not args.no_text,
        extract_tables=not args.no_tables,
        use_ocr=args.ocr,
        ocr_lang=args.ocr_lang,
    )

    print(f"Pages: {results['pages']}")
    print(f"Text pages extracted: {len(results['text_content'])}")
    print(f"Tables found: {len(results['tables'])}")
    if args.ocr:
        print(f"OCR pages processed: {len(results['ocr_text'])}")
    print("-" * 60)

    # Generate outputs
    output_format = args.format.lower()
    generated_files = []

    if output_format in ("txt", "all") and not args.no_text:
        f = processor.save_text()
        if f:
            generated_files.append(f)

    if output_format in ("csv", "all") and not args.no_tables:
        f = processor.save_to_csv()
        if f:
            generated_files.append(f)

    if output_format in ("excel", "all"):
        f = processor.save_to_excel()
        if f:
            generated_files.append(f)

    if output_format in ("word", "all"):
        f = processor.save_to_word()
        if f:
            generated_files.append(f)

    if output_format in ("json", "all"):
        f = processor.save_json()
        if f:
            generated_files.append(f)

    print("-" * 60)
    print("Processing complete!")
    print(f"Generated {len(generated_files)} output file(s)")
    for f in generated_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
