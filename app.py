"""Teacher-facing Gradio app for Canvas Discussion: Equations."""

from __future__ import annotations

import gradio as gr
import pandas as pd

from canvas_client import (
    CANVAS_BASE_URL,
    create_equation_discussion,
    discussion_url,
    friendly_canvas_error,
    list_teacher_courses,
)
from canvas_latex import build_discussion_message
from pdf_equations import Equation, extract_equations, parse_equation_range, renumber_label

TOKEN_STORAGE_KEY = "canvas_discussion_equations_token"
REMEMBER_STORAGE_KEY = "canvas_discussion_equations_remember"

_equations_cache: list[Equation] = []

APP_CSS = """
.section-card {
    border: 1px solid var(--border-color-primary);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    background: var(--background-fill-secondary);
}
.privacy-note {
    border-left: 4px solid #0ea5e9;
    padding: 0.75rem 1rem;
    margin: 0.75rem 0;
    background: rgba(14, 165, 233, 0.08);
    border-radius: 0 8px 8px 0;
    font-size: 0.95rem;
}
.step-heading {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
}
"""

TOKEN_GUIDE = """
### How to get your Canvas API token

1. Log in to [Canvas](https://uc.instructure.com/).
2. Open **Account** (left sidebar) → **Settings**.
3. Scroll to **Approved Integrations** and click **+ New Access Token**.
4. For **Purpose**, enter something like `Equation Discussion Uploader`.
5. Click **Generate Token**, copy the token, and paste it above.

Tokens are shown only once. If you lose it, generate a new one.
"""


def _course_choices(api_key: str, show_all: bool = False) -> list[tuple[str, int]]:
    if not (api_key or "").strip():
        return [("Enter your Canvas token in Step 1", -1)]
    try:
        courses = list_teacher_courses(api_key=api_key, show_all=show_all)
        if not courses:
            return [("No teacher courses found for this account", -1)]
        return [(c.label, c.course_id) for c in courses]
    except Exception as exc:
        return [(friendly_canvas_error(exc), -1)]


def test_connection(api_key: str) -> tuple[str, gr.Dropdown]:
    if not (api_key or "").strip():
        return "Enter your Canvas API token first.", gr.Dropdown(choices=[("Enter your Canvas token in Step 1", -1)])

    try:
        courses = list_teacher_courses(api_key=api_key)
        count = len(courses)
        if count == 0:
            return (
                "Connected to Canvas, but no recent teacher courses were found. "
                "Try enabling **Show all courses** in Step 3.",
                gr.Dropdown(choices=_course_choices(api_key)),
            )
        sample = courses[0].label
        status = (
            f"Connected successfully. Found **{count}** recent teacher course"
            f"{'s' if count != 1 else ''} (e.g. {sample})."
        )
        return status, gr.Dropdown(choices=_course_choices(api_key), value=courses[0].course_id)
    except Exception as exc:
        return friendly_canvas_error(exc), gr.Dropdown(choices=[(friendly_canvas_error(exc), -1)])


def refresh_courses(api_key: str, show_all: bool) -> gr.Dropdown:
    choices = _course_choices(api_key, show_all)
    value = choices[0][1] if choices and choices[0][1] != -1 else None
    return gr.Dropdown(choices=choices, value=value)


def on_pdf_upload(pdf_file) -> tuple[pd.DataFrame, str]:
    global _equations_cache
    if pdf_file is None:
        _equations_cache = []
        return pd.DataFrame(), "Upload a PDF to extract equations."

    try:
        _equations_cache = extract_equations(pdf_file)
    except Exception as exc:
        _equations_cache = []
        return pd.DataFrame(), f"Could not read that PDF: {exc}"

    if not _equations_cache:
        return (
            pd.DataFrame(),
            "No numbered equations found. Labels should look like **(1)**, **(3b)**, or **(5-1)**.",
        )

    df = pd.DataFrame(
        {
            "Equation #": [eq.label for eq in _equations_cache],
            "Page": [eq.page for eq in _equations_cache],
            "Equation": [eq.latex for eq in _equations_cache],
        }
    )
    return df, f"Found **{len(_equations_cache)}** equations. Review them below, then continue to Step 3."


def build_preview(
    range_spec: str,
    discussion_title: str,
) -> tuple[pd.DataFrame, str]:
    if not _equations_cache:
        return pd.DataFrame(), "Upload a PDF in Step 2 first."

    try:
        selected = parse_equation_range(range_spec, _equations_cache)
    except ValueError as exc:
        return pd.DataFrame(), f"Could not understand that range: {exc}"

    if not selected:
        return pd.DataFrame(), "No equations match that range. Check the examples and try again."

    rows: list[dict] = []
    for i, eq in enumerate(selected):
        display = renumber_label(i + 1, eq.suffix)
        rows.append(
            {
                "New #": display,
                "PDF #": eq.label,
                "Equation": eq.latex,
            }
        )

    title = discussion_title.strip() or "(no title)"
    return (
        pd.DataFrame(rows),
        f"Preview: one unpublished discussion titled **{title}** with **{len(rows)}** equation(s).",
    )


def upload_discussion(
    api_key: str,
    course_id: int | None,
    range_spec: str,
    discussion_title: str,
) -> tuple[pd.DataFrame, str]:
    if not (api_key or "").strip():
        return pd.DataFrame(), "Enter your Canvas API token in Step 1 before uploading."

    title = discussion_title.strip()
    if not title:
        return pd.DataFrame(), "Enter a discussion title before uploading."

    preview_df, preview_msg = build_preview(range_spec, title)
    if preview_df.empty:
        return preview_df, preview_msg

    if not course_id or course_id == -1:
        return preview_df, "Select a valid course first."

    labeled = list(zip(preview_df["New #"], preview_df["Equation"]))
    message_html = build_discussion_message(labeled)

    try:
        result = create_equation_discussion(
            int(course_id),
            title,
            message_html,
            api_key=api_key,
        )
    except Exception as exc:
        return preview_df, friendly_canvas_error(exc)

    result_df = pd.DataFrame(
        [{"Title": result.title, "Status": "Draft created" if result.success else "Failed", "Details": result.detail}]
    )
    if result.success and result.discussion_id and result.course_id:
        link = discussion_url(result.course_id, result.discussion_id)
        status = (
            f"Draft discussion created. Open it in Canvas to review and publish when ready: "
            f"[{title}]({link})"
        )
    elif result.success:
        status = result.detail
    else:
        status = result.detail
    return result_df, status


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Canvas Discussion: Equations") as app:
        gr.Markdown(
            "# Canvas Discussion: Equations\n"
            f"Extract numbered equations from a PDF and save them as an **unpublished** Canvas discussion "
            f"draft on [{CANVAS_BASE_URL}]({CANVAS_BASE_URL})."
        )

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("## Step 1 — Connect to Canvas", elem_classes=["step-heading"])
            token_in = gr.Textbox(
                label="Canvas API token",
                placeholder="Paste your token here",
                type="password",
            )
            remember_cb = gr.Checkbox(
                label="Remember token in this browser",
                value=False,
            )
            gr.Markdown(
                '<div class="privacy-note">'
                "<strong>Privacy:</strong> If you check the box above, your token is stored only in "
                "<strong>this browser's localStorage</strong> on your device. It is never saved on our server."
                "</div>"
            )
            with gr.Accordion("How to get your Canvas token", open=False):
                gr.Markdown(TOKEN_GUIDE)
            test_btn = gr.Button("Test connection")
            connection_status = gr.Markdown("Enter your token and click **Test connection**.")

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("## Step 2 — Upload PDF", elem_classes=["step-heading"])
            gr.Markdown(
                "Upload a PDF with numbered equation labels like **(1)**, **(3b)**, or **(5-1)**. "
                "The first scan may take up to a minute while the equation reader loads."
            )
            pdf_in = gr.File(label="PDF file", file_types=[".pdf"])
            extract_status = gr.Markdown("Upload a PDF to extract equations.")
            extracted_df = gr.Dataframe(
                label="Extracted equations",
                interactive=False,
                wrap=True,
            )

        with gr.Group(elem_classes=["section-card"]):
            gr.Markdown("## Step 3 — Review and upload", elem_classes=["step-heading"])
            with gr.Row():
                show_all_cb = gr.Checkbox(label="Show all courses", value=False)
                refresh_btn = gr.Button("Refresh courses")
            course_dd = gr.Dropdown(
                label="Course",
                choices=[("Complete Step 1 first", -1)],
                value=None,
                interactive=True,
            )
            with gr.Row():
                range_in = gr.Textbox(
                    label="Equation range (optional)",
                    placeholder="Leave blank for all, or e.g. 1-10, 3b, 5-1",
                    value="",
                )
                title_in = gr.Textbox(
                    label="Discussion title",
                    placeholder="e.g. Choked Flow Equations",
                    value="",
                )
            preview_btn = gr.Button("Update preview")
            preview_status = gr.Markdown("")
            preview_df = gr.Dataframe(label="Upload preview", interactive=False, wrap=True)
            upload_btn = gr.Button("Save draft to Canvas", variant="primary")
            upload_status = gr.Markdown("")
            upload_results = gr.Dataframe(label="Upload result", interactive=False)

        restore_js = f"""
        () => {{
            const token = localStorage.getItem("{TOKEN_STORAGE_KEY}") || "";
            const remember = localStorage.getItem("{REMEMBER_STORAGE_KEY}") === "true";
            return [token, remember];
        }}
        """
        persist_js = f"""
        (token, remember) => {{
            if (remember && token) {{
                localStorage.setItem("{TOKEN_STORAGE_KEY}", token);
                localStorage.setItem("{REMEMBER_STORAGE_KEY}", "true");
            }} else {{
                localStorage.removeItem("{TOKEN_STORAGE_KEY}");
                localStorage.setItem("{REMEMBER_STORAGE_KEY}", remember ? "true" : "false");
            }}
        }}
        """

        app.load(None, None, js=restore_js, outputs=[token_in, remember_cb])

        token_in.change(None, [token_in, remember_cb], None, js=persist_js)
        remember_cb.change(None, [token_in, remember_cb], None, js=persist_js)

        test_btn.click(
            test_connection,
            inputs=token_in,
            outputs=[connection_status, course_dd],
        )
        refresh_btn.click(refresh_courses, inputs=[token_in, show_all_cb], outputs=course_dd)
        show_all_cb.change(refresh_courses, inputs=[token_in, show_all_cb], outputs=course_dd)
        pdf_in.change(on_pdf_upload, inputs=pdf_in, outputs=[extracted_df, extract_status])
        preview_btn.click(
            build_preview,
            inputs=[range_in, title_in],
            outputs=[preview_df, preview_status],
        )
        upload_btn.click(
            upload_discussion,
            inputs=[token_in, course_dd, range_in, title_in],
            outputs=[upload_results, upload_status],
        )

    return app


demo = build_app()


def launch() -> None:
    demo.launch(
        css=APP_CSS,
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"),
    )


if __name__ == "__main__":
    launch()