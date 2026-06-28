---
name: canvas-equation-discussion
description: Extract numbered equations from a PDF or Markdown file and create an unpublished Canvas discussion draft. Use when the user wants to turn an equation sheet / derivation PDF or Markdown (.md) into a Canvas "Discussion: Equations" draft, list their Canvas teacher courses, or preview which equations would upload.
---

# Canvas Equation Discussion

Pull numbered equations out of a PDF or Markdown file, pick a range, and post
them to Canvas as an **unpublished** discussion draft. This skill is
**self-contained**: it vendors its extraction/Canvas modules (`content`,
`pdf_equations`, `md_equations`, `canvas_latex`, `canvas_client`) alongside the
CLI, and declares its dependencies inline (PEP 723), so it runs from any
directory once copied into a skills folder — no repo checkout required.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) on the PATH. `uv run` installs the script's
  dependencies (`canvasapi`, `pymupdf`, `python-dotenv`) automatically on first
  use, into an isolated environment.
- A Canvas API token, resolved in this order: `--token` on any command →
  `CANVAS_API_KEY` environment variable → a `.env` file in the current working
  directory (auto-loaded). Course listing and uploading require it; `extract`
  and `preview` do not.
- If the user has no token, walk them through it: Canvas → **Account** →
  **Settings** → **Approved Integrations** → **+ New Access Token** →
  **Generate Token**, then copy it into a `.env` file (in the directory you run
  from) as `CANVAS_API_KEY=...`. Tokens are shown only once.

## Running

`uv run` the script directly — it resolves its own dependencies. Use the path to
wherever this skill folder lives (e.g. `~/.claude/skills/canvas-equation-discussion/`):

```bash
SKILL=~/.claude/skills/canvas-equation-discussion/canvas_discussion.py

# 1. Find the target course id
uv run "$SKILL" courses                 # add --show-all for older courses

# 2. See what equations the file contains
uv run "$SKILL" extract path/to/file.pdf

# 3. Preview the selected, renumbered set (no network calls)
uv run "$SKILL" preview path/to/file.pdf --range 1-10 --title "Choked Flow Equations"

# 4. Create the unpublished draft
uv run "$SKILL" upload path/to/file.pdf --course-id 12345 \
    --title "Choked Flow Equations" --range 1-10
```

Add `--json` to `courses`, `extract`, or `preview` for machine-readable output.

## Recommended sequence

1. `courses` — let the user confirm which course id to target.
2. `extract` — show the equations found; confirm the file parsed as expected.
3. `preview` — confirm the range and the renumbered labels before anything is
   posted. **Confirm the course id and title with the user here.**
4. `upload` — create the draft, then share the returned Canvas link so the
   teacher can review and publish it.

## Range syntax

`--range` is comma-separated. Blank means **all** equations. Tokens:
`1-10` (base numbers 1 through 10), `3b` (a single suffixed label), `5-1`
(a single dash-suffixed label). Selected equations are renumbered sequentially
in document order (suffixes preserved), e.g. picking sources `3,4,5b` yields
new labels `1,2,3b`.

## Notes

- Drafts are **always unpublished** — the teacher publishes in Canvas. The CLI
  cannot publish.
- Supported inputs: `.pdf` (labels like `(1)`, `(3b)`, `(5-1)`) and `.md`
  (display `$$...$$` blocks ending in `\tag{1}`). Prose is ignored.
- This standalone build does **not** bundle OCR (`pix2tex`/`torch`). Markdown and
  clean-text PDFs work; image-based or scanned PDFs are not supported (the OCR
  fallback is skipped and such equations keep their raw extracted text).
- If a command prints a friendly Canvas error (bad token, wrong role), surface
  it to the user verbatim — it already explains the fix.
