"""Create a PDF from a text resume and print verification info.

Usage (from project root):
python scripts/create_pdf.py resumes\resume_john_doe_python_dev.txt

The script writes a PDF next to the input file with suffix .pdf and prints a small JSON-like report.
"""
from __future__ import annotations
import sys
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None


def text_to_pdf(txt_path: str, pdf_path: str) -> None:
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    margin = 72
    y = height - margin
    line_height = 12
    for line in lines:
        if y < margin + line_height:
            c.showPage()
            y = height - margin
        # simple wrapping: if too long, split
        if len(line) > 100:
            # naive wrap
            chunks = [line[i:i+100] for i in range(0, len(line), 100)]
            for chunk in chunks:
                c.drawString(margin, y, chunk)
                y -= line_height
        else:
            c.drawString(margin, y, line)
            y -= line_height
    c.save()


def extract_pdf_text(pdf_path: str) -> str:
    if PdfReader is None:
        return "PyPDF2 not available"
    reader = PdfReader(pdf_path)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(texts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_pdf.py <path-to-txt-resume>")
        sys.exit(1)
    txt_path = sys.argv[1]
    if not os.path.exists(txt_path):
        print(json.dumps({"success": False, "error": "Input file not found", "path": txt_path}))
        sys.exit(1)
    base = os.path.splitext(txt_path)[0]
    pdf_path = base + ".pdf"
    try:
        text_to_pdf(txt_path, pdf_path)
        report = {"success": True, "pdf_path": os.path.abspath(pdf_path)}
        # extract small snippet
        snippet = extract_pdf_text(pdf_path)
        report["snippet_preview"] = snippet[:800]
        report["size"] = os.path.getsize(pdf_path)
        print(json.dumps(report, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == '__main__':
    main()

