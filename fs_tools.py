"""fs_tools.py

Core filesystem tools for reading, listing, writing, and searching files.
Supports .txt, .pdf, .docx for reading text content.

Functions:
- read_file(filepath: str) -> dict
- list_files(directory: str, extension: str = None) -> list
- write_file(filepath: str, content: str) -> dict
- search_in_file(filepath: str, keyword: str) -> dict

Each function returns structured dicts and handles errors gracefully.
"""
from __future__ import annotations
import os
import datetime
import io
import re
from typing import Optional, List, Dict, Any

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    from docx import Document
except Exception:
    Document = None


def _file_metadata(path: str) -> Dict[str, Any]:
    st = os.stat(path)
    return {
        "path": os.path.abspath(path),
        "name": os.path.basename(path),
        "size": st.st_size,
        "modified": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(),
        "extension": os.path.splitext(path)[1].lower(),
    }


def read_file(filepath: str) -> Dict[str, Any]:
    """Read a file and extract text content and metadata.

    Supports .txt, .docx, .pdf. Returns dict with keys:
    - success: bool
    - content: str (if success)
    - metadata: dict
    - error: str (if not success)
    """
    try:
        if not os.path.exists(filepath):
            return {"success": False, "error": "File does not exist", "metadata": {"path": filepath}}

        ext = os.path.splitext(filepath)[1].lower()
        content = ""

        if ext in (".txt", ".md", ".csv"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        elif ext == ".pdf":
            if PdfReader is None:
                return {"success": False, "error": "PyPDF2 not installed", "metadata": _file_metadata(filepath)}
            try:
                reader = PdfReader(filepath)
                texts = []
                for page in reader.pages:
                    try:
                        texts.append(page.extract_text() or "")
                    except Exception:
                        # continue despite page-level errors
                        continue
                content = "\n".join(texts)
            except Exception as e:
                return {"success": False, "error": f"PDF read error: {e}", "metadata": _file_metadata(filepath)}

        elif ext in (".docx",):
            if Document is None:
                return {"success": False, "error": "python-docx not installed", "metadata": _file_metadata(filepath)}
            try:
                doc = Document(filepath)
                paragraphs = [p.text for p in doc.paragraphs]
                content = "\n".join(paragraphs)
            except Exception as e:
                return {"success": False, "error": f"DOCX read error: {e}", "metadata": _file_metadata(filepath)}

        else:
            # attempt to read as text as a fallback
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                return {"success": False, "error": f"Unsupported or unreadable file type: {e}", "metadata": _file_metadata(filepath)}

        return {"success": True, "content": content, "metadata": _file_metadata(filepath)}
    except Exception as exc:
        return {"success": False, "error": str(exc), "metadata": {"path": filepath}}


def list_files(directory: str, extension: Optional[str] = None) -> List[Dict[str, Any]]:
    """List files in a directory. Optionally filter by extension (e.g. '.pdf').

    Returns a list of metadata dictionaries for each file.
    """
    try:
        if not os.path.isdir(directory):
            return []
        files = []
        ext = None
        if extension:
            ext = extension.lower()
            if not ext.startswith("."):
                ext = "." + ext

        with os.scandir(directory) as it:
            for entry in it:
                if not entry.is_file():
                    continue
                if ext and os.path.splitext(entry.name)[1].lower() != ext:
                    continue
                try:
                    files.append(_file_metadata(entry.path))
                except Exception:
                    # skip unreadable files
                    continue
        return files
    except Exception:
        return []


def write_file(filepath: str, content: str) -> Dict[str, Any]:
    """Write content to a file. Creates parent directories if needed.

    Returns {success: bool, path: str, error?: str}
    """
    try:
        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": os.path.abspath(filepath)}
    except Exception as exc:
        return {"success": False, "error": str(exc), "path": filepath}


def search_in_file(filepath: str, keyword: str, context_chars: int = 50) -> Dict[str, Any]:
    """Search for a keyword in a file (case-insensitive).

    Returns dict with keys:
    - success: bool
    - matches: list of {start, end, snippet, line_number}
    - metadata
    - error (if any)
    """
    try:
        r = read_file(filepath)
        if not r.get("success"):
            return {"success": False, "error": r.get("error"), "metadata": r.get("metadata")}
        text = r.get("content", "")
        if not text:
            return {"success": True, "matches": [], "metadata": r.get("metadata")}

        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        matches = []
        # provide matches with character context and line number
        for m in pattern.finditer(text):
            start, end = m.span()
            snippet_start = max(0, start - context_chars)
            snippet_end = min(len(text), end + context_chars)
            snippet = text[snippet_start:snippet_end]
            # compute line number by counting newlines before start
            line_number = text.count("\n", 0, start) + 1
            matches.append({
                "start": start,
                "end": end,
                "snippet": snippet,
                "line_number": line_number,
            })
        return {"success": True, "matches": matches, "metadata": r.get("metadata")}
    except Exception as exc:
        return {"success": False, "error": str(exc), "metadata": {"path": filepath}}

