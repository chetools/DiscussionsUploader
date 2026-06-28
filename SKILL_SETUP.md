# Installing the `canvas-equation-discussion` skill

This repo ships a **self-contained** [Claude Code](https://claude.com/claude-code)
skill that turns a numbered-equation PDF or Markdown file into an **unpublished
Canvas discussion draft** — driven by Claude from the terminal.

The skill folder
[`.claude/skills/canvas-equation-discussion/`](.claude/skills/canvas-equation-discussion/)
is portable: it vendors its own extraction/Canvas modules and declares its Python
dependencies inline (PEP 723). You can **copy just that one folder** into any
skills directory and use it without cloning this repo.

## Prerequisites

1. **Claude Code** — https://claude.com/claude-code
2. **[uv](https://docs.astral.sh/uv/)** on your PATH. `uv run` installs the
   skill's dependencies (`canvasapi`, `pymupdf`, `python-dotenv`) automatically
   on first use, into an isolated environment — no manual `pip install`.
3. A **Canvas API token** (only for `courses` and `upload`; `extract`/`preview`
   work without one).
   - In Canvas: **Account → Settings → Approved Integrations → + New Access
     Token → Generate Token**, then copy it (shown only once).

## Install

Copy the skill folder into a skills directory:

```bash
# User scope (available in every project)
mkdir -p ~/.claude/skills
cp -r .claude/skills/canvas-equation-discussion ~/.claude/skills/

# …or project scope (available only in one project)
cp -r .claude/skills/canvas-equation-discussion /path/to/project/.claude/skills/
```

On Windows the user-scope target is `%USERPROFILE%\.claude\skills\`.

Provide your Canvas token by either:

- a `.env` file in the directory you run Claude / the CLI from, containing
  `CANVAS_API_KEY=your_token_here` (optionally `CANVAS_API_URL=https://yourschool.instructure.com`), or
- exporting `CANVAS_API_KEY` in your environment, or
- passing `--token ...` to a command.

Then launch Claude Code; the skill is auto-discovered:

```bash
claude
```

## Using it

Ask Claude in plain English, e.g.:

- *"List my Canvas teacher courses."*
- *"Extract the equations from notes.pdf."*
- *"Preview equations 1-10 from derivation.md titled 'Choked Flow'."*
- *"Upload equations 2-5 from notes.pdf to course 1843860 as an unpublished draft."*

Drafts are **always unpublished** — you review and publish them in Canvas.

### Running the CLI directly (optional)

```bash
SKILL=~/.claude/skills/canvas-equation-discussion/canvas_discussion.py

uv run "$SKILL" courses                                  # list teacher courses
uv run "$SKILL" extract path/to/file.pdf                 # show equations found
uv run "$SKILL" preview path/to/file.md --range 1-10 --title "My Topic"
uv run "$SKILL" upload path/to/file.pdf \
    --course-id 12345 --title "My Topic" --range 1-10
```

Add `--json` to `courses`, `extract`, or `preview` for machine-readable output.

## Supported inputs

| Type | Equation label format |
|---|---|
| `.pdf` | `(1)`, `(3b)`, `(5-1)` next to each equation |
| `.md` / `.markdown` | display `$$...$$` blocks ending in `\tag{1}` |

Prose is ignored — only labeled equations are picked up. This standalone build
does **not** bundle OCR (`pix2tex`/`torch`), so Markdown and clean-text PDFs are
supported but image/scanned PDFs are not.

## Range syntax

`--range` is comma-separated; blank means **all**. Tokens: `1-10` (base numbers
1–10), `3b` (single suffixed label), `5-1` (single dash-suffixed label). Selected
equations are renumbered sequentially in document order, so picking sources
`3,4,5b` yields new labels `1,2,3b`.

## Maintainer note

The five modules inside the skill folder (`canvas_client.py`, `canvas_latex.py`,
`content.py`, `pdf_equations.py`, `md_equations.py`) are **vendored copies** of
the same-named files in the repo root. If you change the root modules, re-copy
them into the skill folder to keep the standalone build in sync.
