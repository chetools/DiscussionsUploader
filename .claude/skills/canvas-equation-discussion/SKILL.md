---
name: canvas-equation-discussion
description: Extract numbered equations from a PDF or Markdown file and create an unpublished Canvas discussion draft. Use when the user wants to turn an equation sheet / derivation PDF or Markdown (.md) into a Canvas "Discussion: Equations" draft, list their Canvas teacher courses, or preview which equations would upload.
---

# Canvas Equation Discussion

Drive the same workflow as this repo's Gradio app from the terminal: pull
numbered equations out of a PDF or Markdown file, pick a range, and post them
to Canvas as an **unpublished** discussion draft. The CLI reuses the project's
own modules (`content`, `pdf_equations`, `canvas_latex`, `canvas_client`), so
behavior matches the app exactly.

## Prerequisites

- A Canvas API token. The CLI reads it from `CANVAS_API_KEY` (environment
  variable or a `.env` file in the project root, auto-loaded), or you can pass
  `--token` to any command. Course listing and uploading require it; `extract`
  and `preview` do not.
- If the user has no token, walk them through it: Canvas → **Account** →
  **Settings** → **Approved Integrations** → **+ New Access Token** →
  **Generate Token**, then copy it into a `.env` file as
  `CANVAS_API_KEY=...`. Tokens are shown only once.

## Running

Always run from the project root with `uv run` so dependencies resolve:

```bash
SKILL=.claude/skills/canvas-equation-discussion/canvas_discussion.py

# 1. Find the target course id
uv run python "$SKILL" courses                 # add --show-all for older courses

# 2. See what equations the file contains
uv run python "$SKILL" extract path/to/file.pdf

# 3. Preview the selected, renumbered set (no network calls)
uv run python "$SKILL" preview path/to/file.pdf --range 1-10 --title "Choked Flow Equations"

# 4. Create the unpublished draft
uv run python "$SKILL" upload path/to/file.pdf --course-id 12345 \
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
- The first PDF run can take ~1 minute while the `pix2tex` OCR model lazy-loads
  (used only when extracted text isn't clean enough). Markdown needs no OCR.
- If a command prints a friendly Canvas error (bad token, wrong role), surface
  it to the user verbatim — it already explains the fix.
