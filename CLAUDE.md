# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app locally
uv run app.py
# or
uv run main.py

# Install dependencies
uv pip install -r requirements.txt
# or sync from pyproject.toml
uv sync
```

No test suite or linter is configured. The Canvas API requires a real token; for local dev, set `CANVAS_API_KEY` in a `.env` file (auto-loaded by `python-dotenv`). `CANVAS_API_URL` overrides the hardcoded UC URL.

## Architecture

Single-file-per-concern, no packages. All source lives in the project root.

| File | Role |
|---|---|
| `app.py` | Gradio UI — all event handlers and `build_app()`. Module-level `_equations_cache` and `_source_kind` act as in-process state between UI steps. |
| `canvas_client.py` | Canvas LMS API wrapper (via `canvasapi`). Handles auth, course listing, and discussion creation. `CANVAS_API_KEY` env var is the fallback when no token is passed from the UI. |
| `canvas_latex.py` | Converts LaTeX strings to Canvas RCE `<img class="equation_image">` HTML. URL-encodes LaTeX twice (once for the src path, once to escape the first encoding). |
| `content.py` | Dispatch layer — routes `.pdf` vs `.md` files to the appropriate extractor and returns a uniform `ExtractResult`. |
| `pdf_equations.py` | PDF extraction: uses PyMuPDF (`fitz`) for text extraction, falls back to `pix2tex` OCR for equations with low ASCII ratio. Contains `Equation` dataclass, label parsing (`EQ_LABEL_RE`), range parsing (`parse_equation_range`), and box-stripping (`strip_latex_boxes`). |
| `md_equations.py` | Markdown extraction: finds `$$...$$` blocks with a `\tag{N}` and returns the same `Equation` dataclass. |

**Data flow:**
1. User uploads PDF or Markdown → `content.extract_from_file` → list of `Equation` objects stored in `_equations_cache`
2. User picks range/title → `parse_equation_range` filters cache → `build_discussion_message` renders HTML
3. User clicks upload → `create_equation_discussion` posts to Canvas API as an unpublished draft

**Equation label format:** `(1)`, `(3b)`, `(5-1)` — base number plus optional alpha or dash-number suffix, matched by `EQ_LABEL_RE = r"^\((\d+)([a-zA-Z]+|-\d+)?\)$"`.

**OCR fallback:** `pix2tex.LatexOCR` is lazy-loaded on first use (can take ~1 min). It triggers when extracted text has < 55% ASCII characters.

## Deployment

The app is deployed to Hugging Face Spaces. `README.md` doubles as the HF Space card (YAML frontmatter). The Space entry point is `app_file: app.py` and the Gradio `demo` object must be module-level for HF to detect it.
