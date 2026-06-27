"""Gradio app: upload numbered PDF equations to a Canvas discussion."""

from __future__ import annotations

import gradio as gr
import pandas as pd

from canvas_client import create_equation_discussion, list_teacher_courses
from canvas_latex import build_discussion_message
from pdf_equations import Equation, extract_equations, parse_equation_range, renumber_label

_equations_cache: list[Equation] = []


def _course_choices(show_all: bool = False) -> list[tuple[str, int]]:
    try:
        courses = list_teacher_courses(show_all=show_all)
        return [(c.label, c.course_id) for c in courses]
    except Exception as exc:
        return [(f"Error loading courses: {exc}", -1)]


def refresh_courses(show_all: bool) -> gr.Dropdown:
    choices = _course_choices(show_all)
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
        return pd.DataFrame(), f"Extraction failed: {exc}"

    if not _equations_cache:
        return (
            pd.DataFrame(),
            "No numbered equations found. Expected labels like (1), (3b), (5-1), …",
        )

    df = pd.DataFrame(
        {
            "label": [eq.label for eq in _equations_cache],
            "page": [eq.page for eq in _equations_cache],
            "latex": [eq.latex for eq in _equations_cache],
        }
    )
    return df, f"Found {len(_equations_cache)} equations."


def build_preview(
    range_spec: str,
    discussion_title: str,
) -> tuple[pd.DataFrame, str]:
    if not _equations_cache:
        return pd.DataFrame(), "No equations loaded."

    try:
        selected = parse_equation_range(range_spec, _equations_cache)
    except ValueError as exc:
        return pd.DataFrame(), f"Invalid range: {exc}"

    if not selected:
        return pd.DataFrame(), "No equations match that range."

    rows: list[dict] = []
    for i, eq in enumerate(selected):
        display = renumber_label(i + 1, eq.suffix)
        rows.append(
            {
                "display_label": display,
                "pdf_label": eq.label,
                "latex": eq.latex,
            }
        )

    title = discussion_title.strip() or "(no title)"
    return (
        pd.DataFrame(rows),
        f"Preview: 1 discussion titled '{title}' with {len(rows)} equation(s).",
    )


def upload_discussion(
    course_id: int | None,
    range_spec: str,
    discussion_title: str,
) -> tuple[pd.DataFrame, str]:
    title = discussion_title.strip()
    if not title:
        return pd.DataFrame(), "Enter a discussion title before uploading."

    preview_df, preview_msg = build_preview(range_spec, title)
    if preview_df.empty:
        return preview_df, preview_msg

    if not course_id or course_id == -1:
        return preview_df, "Select a valid course first."

    labeled = list(zip(preview_df["display_label"], preview_df["latex"]))
    message_html = build_discussion_message(labeled)

    try:
        result = create_equation_discussion(int(course_id), title, message_html)
    except Exception as exc:
        return preview_df, f"Upload failed: {exc}"

    result_df = pd.DataFrame(
        [{"title": result.title, "success": result.success, "detail": result.detail}]
    )
    status = f"Uploaded: {result.detail}"
    if result.discussion_id:
        status += f" (id={result.discussion_id})"
    return result_df, status


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Canvas Equation Uploader") as app:
        gr.Markdown(
            "# Canvas Equation Discussion Uploader\n"
            "Extract numbered equations from a PDF and upload them as a single Canvas discussion."
        )

        with gr.Row():
            show_all_cb = gr.Checkbox(
                label="Show all courses",
                value=False,
            )
            refresh_btn = gr.Button("Refresh courses")

        course_dd = gr.Dropdown(
            label="Course",
            choices=_course_choices(show_all=False),
            value=_course_choices(False)[0][1] if _course_choices(False) else None,
            interactive=True,
        )

        pdf_in = gr.File(label="PDF file", file_types=[".pdf"])
        extract_status = gr.Markdown("Upload a PDF to extract equations.")
        extracted_df = gr.Dataframe(
            label="All extracted equations",
            interactive=False,
            wrap=True,
        )

        with gr.Row():
            range_in = gr.Textbox(
                label="Equation range",
                placeholder="e.g. 1-10, 3b,5-1, or leave blank for all",
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

        upload_btn = gr.Button("Upload to Canvas", variant="primary")
        upload_status = gr.Markdown("")
        upload_results = gr.Dataframe(label="Upload results", interactive=False)

        refresh_btn.click(refresh_courses, inputs=show_all_cb, outputs=course_dd)
        show_all_cb.change(refresh_courses, inputs=show_all_cb, outputs=course_dd)
        pdf_in.change(on_pdf_upload, inputs=pdf_in, outputs=[extracted_df, extract_status])
        preview_btn.click(
            build_preview,
            inputs=[range_in, title_in],
            outputs=[preview_df, preview_status],
        )
        upload_btn.click(
            upload_discussion,
            inputs=[course_dd, range_in, title_in],
            outputs=[upload_results, upload_status],
        )

    return app


if __name__ == "__main__":
    build_app().launch()