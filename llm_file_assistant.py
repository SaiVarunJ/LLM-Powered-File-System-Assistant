"""llm_file_assistant.py

A lightweight adapter that connects simple heuristics and optional OpenAI LLM
calls to the file-system tools in fs_tools.py.

Functionality:
- handle_query(query: str) -> dict: decide which tool to call and return structured output
- If OpenAI API key and package are available, it can use the LLM to parse intent; otherwise falls back to simple intent rules.

Example queries supported:
- "Read all resumes in the resumes folder"
- "Find resumes mentioning Python experience"
- "Create a summary file for resume_john_doe.pdf"

This module intentionally keeps LLM usage optional and provides clear fallbacks.
"""
from __future__ import annotations
import os
import re
import json
from typing import Any, Dict, List, Optional

from fs_tools import read_file, list_files, search_in_file, write_file

# Optional OpenAI integration
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

OPENAI_MODEL = "gpt-3.5-turbo"


def _call_openai(prompt: str, system: Optional[str] = None) -> str:
    """Call OpenAI chat completions if available and configured.

    Returns text response or raises an exception on failure.
    """
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI package not installed")
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_APIKEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    openai.api_key = api_key
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = openai.ChatCompletion.create(model=OPENAI_MODEL, messages=messages, temperature=0)
    return resp.choices[0].message.content


def _heuristic_intent(query: str) -> Dict[str, Any]:
    q = query.lower()
    if "read all resumes" in q or ("read" in q and "resumes" in q):
        return {"action": "read_all_resumes"}
    if "find" in q or "search" in q or "mention" in q or "mentioning" in q:
        return {"action": "search_resumes"}
    if "summary" in q or "create a summary" in q or "summarize" in q:
        return {"action": "create_summary"}
    # fallback
    return {"action": "unknown"}


def handle_query(query: str, resumes_dir: str = "resumes") -> Dict[str, Any]:
    """Main entrypoint to handle user queries about files/resumes.

    Uses the LLM if available to parse the intent, otherwise falls back to heuristics.
    Returns a structured dict with fields: success, action, result, error(optional)
    """
    # Try LLM to interpret intent if possible
    intent = None
    if OPENAI_AVAILABLE and (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_APIKEY")):
        try:
            prompt = (
                "You are a tiny assistant that maps a user instruction about files to a simple JSON with keys: action and params. "
                "Possible actions: read_all_resumes, search_resumes, create_summary, list_files, read_file. "
                "Return only JSON. Instruction: " + query
            )
            out = _call_openai(prompt)
            # try to parse JSON from response
            parsed = json.loads(out)
            intent = parsed
        except Exception:
            intent = _heuristic_intent(query)
    else:
        intent = _heuristic_intent(query)

    action = intent.get("action")

    if action == "read_all_resumes":
        # list files and read each
        files = list_files(resumes_dir)
        results = []
        for f in files:
            r = read_file(f["path"]) if f.get("path") else read_file(os.path.join(resumes_dir, f["name"]))
            results.append({"file": f, "read": r})
        return {"success": True, "action": action, "result": results}

    if action == "search_resumes":
        # extract keyword from intent params or fallback to extracting from query
        keyword = None
        if isinstance(intent.get("params"), dict):
            keyword = intent["params"].get("keyword")
        if not keyword:
            # heuristic: look for words after 'mention' or 'mentioning' or 'find' or 'for'
            m = re.search(r"mention(?:ing)?\s+([\w#+\-]+)", query, re.IGNORECASE)
            if not m:
                m = re.search(r"find\s+.*\s([\w#+\-]+)", query, re.IGNORECASE)
            if not m:
                m = re.search(r"for\s+([\w#+\-]+)", query, re.IGNORECASE)
            if m:
                keyword = m.group(1)
        if not keyword:
            return {"success": False, "action": action, "error": "Could not determine search keyword"}
        files = list_files(resumes_dir)
        matches = []
        for f in files:
            search = search_in_file(f["path"], keyword)
            if search.get("success") and search.get("matches"):
                matches.append({"file": f, "matches": search["matches"]})
        return {"success": True, "action": action, "keyword": keyword, "result": matches}

    if action == "create_summary":
        # expect a filename in the query
        m = re.search(r"resume[_ ]?([\w\-]+)\.(pdf|txt|docx)", query, re.IGNORECASE)
        filename = None
        if m:
            filename = f"resume_{m.group(1)}.{m.group(2)}"
        else:
            # try to find any .pdf/.txt/.docx token
            m2 = re.search(r"([\w\-]+\.(pdf|txt|docx))", query, re.IGNORECASE)
            if m2:
                filename = m2.group(1)
        if not filename:
            return {"success": False, "action": action, "error": "Could not determine filename to summarize"}
        filepath = os.path.join(resumes_dir, filename)
        rf = read_file(filepath)
        if not rf.get("success"):
            return {"success": False, "action": action, "error": rf.get("error"), "file": filepath}
        content = rf.get("content", "")
        # lightweight summary: take first 500 chars or first 5 lines
        lines = [ln for ln in content.splitlines() if ln.strip()]
        summary = ""
        if lines:
            summary = "\n".join(lines[:5])
        if not summary:
            summary = content[:500]
        summary_path = os.path.join(resumes_dir, filename + ".summary.txt")
        w = write_file(summary_path, summary)
        if not w.get("success"):
            return {"success": False, "action": action, "error": w.get("error")}
        return {"success": True, "action": action, "summary_path": w.get("path"), "summary": summary}

    if action == "list_files":
        files = list_files(resumes_dir)
        return {"success": True, "action": action, "result": files}

    if action == "read_file":
        # try to extract filename
        m = re.search(r"([\w\-]+\.(pdf|txt|docx))", query, re.IGNORECASE)
        if not m:
            return {"success": False, "action": action, "error": "No filename found"}
        filename = m.group(1)
        filepath = os.path.join(resumes_dir, filename)
        rf = read_file(filepath)
        return {"success": rf.get("success"), "action": action, "result": rf}

    return {"success": False, "action": action, "error": "Unknown or unsupported action"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple LLM-backed file assistant (optional LLM).")
    parser.add_argument("query", help="User query to execute")
    parser.add_argument("--resumes-dir", default="resumes", help="Directory where resumes live")
    args = parser.parse_args()
    out = handle_query(args.query, resumes_dir=args.resumes_dir)
    print(json.dumps(out, indent=2))

