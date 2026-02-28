LLM-Powered File System Assistant
=================================

A small Python utility that provides core file-system tools for reading, listing, writing,
and searching resume files, plus a lightweight assistant that can map user queries to
those tools (optionally using OpenAI to parse intent).

Files of interest
- `fs_tools.py` - read/list/write/search helpers (supports .txt, .pdf, .docx)
- `llm_file_assistant.py` - simple assistant that maps plain queries to tool actions
- `resumes/` - sample resume files (e.g. `resume_john_doe.txt`)
- `requirements.txt` - Python dependencies used for optional PDF/DOCX reading and tests

Quick setup
-----------
Install dependencies (recommended in a virtual environment):

```bat
python -m pip install -r requirements.txt
```

Run the test suite (uses `pytest`):

```bat
python -m pytest -q
```

Usage examples (cmd.exe)
------------------------
The assistant is a small CLI you can call with a plain-English query. Example commands (run from the project root):

1) Read all resumes in the `resumes` folder

```bat
python llm_file_assistant.py "Read all resumes in the resumes folder"
```

This lists files found under `resumes/`, reads each supported file, and returns a JSON object containing file metadata and extracted content.

2) Find resumes mentioning "Python"

```bat
python llm_file_assistant.py "Find resumes mentioning Python experience"
```

This will search all resume files for the keyword `Python` (case-insensitive) and return matches with context snippets and line numbers.

3) Create a summary file for a resume (example with the included sample `resume_john_doe.txt`)

```bat
python llm_file_assistant.py "Create a summary file for resume_john_doe.txt"
```

This reads the target resume, generates a short summary (first few non-empty lines or first 500 characters), and writes a summary file alongside the resume named `resume_john_doe.txt.summary.txt`.

Optional: Enable OpenAI intent parsing
-------------------------------------
If you want the assistant to use an LLM to parse intent (more flexible recognition), set the `OPENAI_API_KEY` environment variable in your shell before running the assistant. The assistant falls back to a heuristic parser if the key or package is missing.

For cmd.exe:

```bat
set OPENAI_API_KEY=sk-...your-key...
python llm_file_assistant.py "Find resumes mentioning machine learning"
```

Included sample resumes
-----------------------
The repository contains several dummy/sample resumes under the `resumes/` directory for testing and demonstration. Current files include:

- `resumes/resume_john_doe.txt`
- `resumes/resume_john_doe_python_dev.txt`
- `resumes/resume_john_doe_python_dev.pdf` (generated)
- `resumes/resume_jane_smith.txt`
- `resumes/resume_alex_lee.txt`
- `resumes/resume_emily_chen.txt`
- `resumes/Kodanda_Profile_AEM.pdf` (sample PDF)
- `resumes/resume_varun.pdf` (sample PDF)

These provide a mix of .txt and .pdf files so you can exercise reading, searching, and conversion utilities.

Notes and limitations
---------------------
- PDF extraction uses `PyPDF2` (installation included in `requirements.txt`) — text extraction quality depends on the PDF. Scanned images require OCR and are not supported by default.
- DOCX extraction uses `python-docx` and extracts paragraph text (tables and complex layouts may need extra parsing).
- `search_in_file` returns match snippets plus a line number computed by counting newlines in the extracted text.
- If you add large files or many files, consider streaming or batching reads to avoid large memory use.

Developer notes
---------------
- Tests are under `tests/` and cover core `fs_tools` functionality.
- To extend: add OCR support (Tesseract/pytesseract), improve DOCX/table parsing, or add more advanced LLM-driven behaviors.

Contact
-------
If you'd like me to expand the CLI, add subcommands, or improve summaries using the LLM, tell me which feature to prioritize and I'll implement it.
