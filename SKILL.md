---
name: canvas-session-equations-code
description: Turn numbered equations (from a PDF, a Markdown file, or the current Claude Code conversation) OR Python code generated during a session into an unpublished Canvas discussion draft. Use when the user wants to post an equation sheet / derivation, the equations that came up in this chat, or a Python file (whole or selected lines) as a readable numbered-line listing to a Canvas "Discussion" draft, list their Canvas teacher courses, or preview what would upload.
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

# 4. Create the unpublished draft (optional --description adds intro text on top)
uv run "$SKILL" upload path/to/file.pdf --course-id 12345 \
    --title "Choked Flow Equations" --range 1-10 \
    --description "Equations from the choked-flow derivation we did in lecture."
```

Add `--json` to `courses`, `extract`, `preview`, or `session` for machine-readable output.

**`--description`** (on `preview`/`upload` and `code-preview`/`code-upload`) adds
a normal-text paragraph above the equations or code in the discussion body.

**Do not pause to ask the user for confirmation** before running these commands.
When the skill is invoked, proceed through the steps (and the upload) using the
details the user gave; surface results and any errors afterward. Drafts are
unpublished anyway, so the teacher reviews in Canvas before publishing.

## Session source (equations from this conversation)

To upload the equations that came up *during the current Claude Code
conversation* instead of from a file, use the `session` command. It scans the
active session's transcript, collects the display-math (`$$...$$` and `\[...\]`)
equations, dedupes and numbers them, and writes a Markdown file that the
existing `preview`/`upload` commands consume unchanged:

```bash
# 1. Collect the conversation's equations (auto-detects the current session)
uv run "$SKILL" session                 # writes a temp .md, prints a numbered list
#    --transcript PATH   target a specific .jsonl conversation instead
#    --project-dir DIR    override the Claude Code projects folder
#    --out PATH           choose where the .md is written

# 2. Show the numbered list to the user and let them pick which to keep.

# 3. Preview / upload the chosen numbers via the SAME commands as files:
uv run "$SKILL" preview <printed.md> --range 2,4,5 --title "Helmholtz Residual"
uv run "$SKILL" upload  <printed.md> --course-id 12345 \
    --title "Helmholtz Residual" --range 2,4,5
```

Notes for the session source:

- **Selection is the `--range` from the printed list** — present the numbered
  equations, ask the user which ones, then pass them as `--range`.
- Only **display** math is collected (deliberate `$$...$$` / `\[...\]` blocks);
  inline `$...$` is ignored. Blocks with no letters/digits (e.g. a bare `...`)
  are dropped, and verbatim-restated equations are deduped to first occurrence.
- The current session is the most-recently-modified transcript for this project.
  If that's the wrong one, pass `--transcript` with the exact `.jsonl` path.
- A `$$...$$` shown inside a fenced code example in chat can be captured too —
  the user curates that out via `--range`.

## Python code source (upload code from this session)

To post **Python code** generated during the conversation — a whole `.py` file
or selected lines — as a readable numbered-line listing, use the `code-*`
commands. Generated code is read from the file's **current on-disk state**; the
transcript is used only to discover which `.py` files the session produced.

```bash
# 1. List the .py files generated/edited in the current conversation
uv run "$SKILL" code-list                # autodetects the session transcript
#    --transcript PATH / --project-dir DIR to override

# 2. Preview the numbered listing (no network); blank --lines = whole file
uv run "$SKILL" code-preview secant_demo.py --lines 9-17

# 3. Create the unpublished draft (optional --description adds intro text on top)
uv run "$SKILL" code-upload secant_demo.py --course-id 12345 \
    --title "Secant method demo" --lines 9-17 \
    --description "Worked example from class: the secant root-finder."
```

Notes for the code source:

- **`--lines`** is comma-separated; blank means the **whole file**. Tokens:
  `9-17` (a range) and `20` (a single line), e.g. `9-17,20,25-30`. Selected
  lines keep their **original file line numbers** (lines 9–17 render as 9…17).
- **`--no-comments`** (on `code-preview`/`code-upload`) excludes all Python `#`
  comments: comment-only lines are dropped (their numbers are skipped, so the
  remaining lines keep their real numbers) and inline comments are trimmed off
  while the code stays. A `#` inside a string literal is **not** treated as a
  comment (uses `tokenize`).
- Rendered on Canvas as a monospace, numbered-line listing (no syntax colors):
  one `<pre>` element with the line number embedded at the start of each line.
  `<pre>` is used (not a `<div style="white-space:pre-wrap">`) because Canvas's
  sanitizer **strips the `white-space` style property** — a div collapses the
  whole listing onto one line. `<pre>` preserves whitespace structurally, and an
  inline `margin:0` (which Canvas keeps) removes its default block margins.
  Embedding the number per line means it can never desync from its code.
  Indentation and `<`/`>`/`&` are preserved; long lines extend horizontally
  rather than wrap.
- `code-list` flags files that no longer exist on disk; pass an explicit path to
  `code-preview`/`code-upload` (it need not be one from `code-list`).
- Add `--json` to `code-list` / `code-preview` for machine-readable output.

## Recommended sequence

1. `courses` — resolve the target course id (use the one the user named).
2. `extract` — show the equations found so the parse is visible.
3. `preview` — show the range and renumbered labels.
4. `upload` — create the draft, then share the returned Canvas link so the
   teacher can review and publish it.

Run these straight through without stopping to ask "shall I proceed?" — the
draft is unpublished, so the review happens in Canvas.

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
