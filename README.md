---
title: "Canvas Discussion: Equations"
emoji: 📐
colorFrom: blue
colorTo: green
sdk: gradio
app_file: app.py
pinned: false
---

# Canvas Discussion: Equations

Upload numbered equations from a **PDF** or **Markdown** file into Canvas as an **unpublished discussion draft** — ready for teachers at [UC Canvas](https://uc.instructure.com/).

## How to use

1. **Connect** — Paste your Canvas API token and test the connection.
2. **Upload file** — Provide a PDF with numbered labels like `(1)`, `(3b)`, or `(5-1)`, or a Markdown file with display equations tagged `\tag{1}`, `\tag{3b}`, etc. Only numbered equations are uploaded; prose is stripped. `\boxed{...}` and `\fbox{...}` are removed automatically.
3. **Review & save** — Choose a course, preview the equations, and save an unpublished draft to Canvas.

## Getting a Canvas token

In Canvas: **Account → Settings → Approved Integrations → + New Access Token**

## Privacy

- Your Canvas URL is preconfigured for UC (`https://uc.instructure.com`).
- Your API token is **not** stored on this server.
- If you opt in, your token is saved only in **your browser's localStorage**.

Only use this tool if you trust the Space operator. API tokens grant access to your Canvas account.

## For developers

This Space is built from [DiscussionsUploader](https://github.com/chetools/DiscussionsUploader).

Local development:

```bash
uv run app.py
```

Optional `.env` for local dev:

```
CANVAS_API_KEY=your_token_here
```