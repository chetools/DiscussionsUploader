# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "canvasapi>=3.6.0",
#     "pymupdf>=1.27.0",
#     "python-dotenv>=1.0",
# ]
# ///
"""CLI wrapper for the Canvas equation-discussion workflow.

Thin command-line front end over the project's existing modules so Claude (or a
human) can drive the same flow as the Gradio app without the web UI:

    courses   list teacher courses (id + label)
    extract   list numbered equations found in a PDF or Markdown file
    preview   show the renumbered selection for a range (no network)
    upload    create an unpublished Canvas discussion draft

No business logic lives here; everything is delegated to content.py,
pdf_equations.py, canvas_latex.py, and canvas_client.py.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

# This skill is self-contained: the modules it imports are vendored alongside
# this file, so they resolve regardless of the current working directory.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from canvas_client import (  # noqa: E402
    create_equation_discussion,
    discussion_url,
    friendly_canvas_error,
    list_teacher_courses,
)
from canvas_latex import build_discussion_message  # noqa: E402
from content import extract_from_file  # noqa: E402
from pdf_equations import parse_equation_range, renumber_label  # noqa: E402
from session_equations import (  # noqa: E402
    discover_transcript,
    extract_session_equations,
    write_session_markdown,
)


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _selected(file: str, range_spec: str):
    """Extract equations and apply the range filter; returns (source_kind, list)."""
    result = extract_from_file(file)
    if not result.equations:
        return result.source_kind, []
    selected = parse_equation_range(range_spec or "", result.equations)
    return result.source_kind, selected


def _no_equations_hint(source_kind: str) -> str:
    if source_kind == "markdown":
        return (
            "No numbered equations found. Labels should use \\tag{1}, \\tag{3b}, "
            "or \\tag{5-1} on $$...$$ display blocks in the Markdown."
        )
    return (
        "No numbered equations found. Labels should look like (1), (3b), or (5-1) "
        "in the PDF."
    )


def cmd_courses(args: argparse.Namespace) -> int:
    try:
        courses = list_teacher_courses(api_key=args.token, show_all=args.show_all)
    except Exception as exc:
        return _fail(friendly_canvas_error(exc))

    if not courses:
        print("No teacher courses found. Try --show-all.")
        return 0

    if args.json:
        print(json.dumps([{"course_id": c.course_id, "label": c.label} for c in courses], indent=2))
        return 0

    print(f"{len(courses)} teacher course(s):")
    for c in courses:
        print(f"  {c.course_id}\t{c.label}")
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    try:
        result = extract_from_file(args.file)
    except Exception as exc:
        return _fail(f"Could not read that file: {exc}")

    if not result.equations:
        print(_no_equations_hint(result.source_kind))
        return 0

    location = "Section" if result.source_kind == "markdown" else "Page"

    if args.json:
        print(
            json.dumps(
                [
                    {"label": eq.label, location.lower(): eq.page, "latex": eq.latex}
                    for eq in result.equations
                ],
                indent=2,
            )
        )
        return 0

    kind = "Markdown" if result.source_kind == "markdown" else "PDF"
    print(f"Found {len(result.equations)} equation(s) from {kind}:")
    for eq in result.equations:
        print(f"  ({eq.label}) [{location} {eq.page}]  {eq.latex}")
    return 0


def cmd_session(args: argparse.Namespace) -> int:
    try:
        transcript = Path(args.transcript) if args.transcript else discover_transcript(
            project_dir=args.project_dir
        )
    except FileNotFoundError as exc:
        return _fail(str(exc))

    if not transcript.is_file():
        return _fail(f"Transcript not found: {transcript}")

    try:
        equations = extract_session_equations(transcript)
    except Exception as exc:
        return _fail(f"Could not read that transcript: {exc}")

    if not equations:
        print(
            "No $$...$$ display equations found in this conversation. "
            "Only display-math blocks (not inline $...$) are collected."
        )
        return 0

    out_path = Path(args.out) if args.out else Path(tempfile.gettempdir()) / "session_equations.md"
    write_session_markdown(equations, out_path)
    out_abs = out_path.resolve()

    if args.json:
        print(
            json.dumps(
                {
                    "transcript": str(transcript.resolve()),
                    "out": str(out_abs),
                    "equations": [{"label": eq.label, "latex": eq.latex} for eq in equations],
                },
                indent=2,
            )
        )
        return 0

    print(f"Found {len(equations)} display equation(s) in {transcript.name}:")
    for eq in equations:
        print(f"  ({eq.label})  {eq.latex}")
    print()
    print(f"Wrote Markdown for the preview/upload commands: {out_abs}")
    print(f"  Next: preview \"{out_abs}\" --range <nums> --title \"...\"")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    try:
        source_kind, selected = _selected(args.file, args.range)
    except ValueError as exc:
        return _fail(f"Could not understand that range: {exc}")
    except Exception as exc:
        return _fail(f"Could not read that file: {exc}")

    if not selected:
        print(_no_equations_hint(source_kind) if args.range in ("", None) else "No equations match that range.")
        return 0

    rows = [
        {"new": renumber_label(i + 1, eq.suffix), "source": eq.label, "latex": eq.latex}
        for i, eq in enumerate(selected)
    ]

    if args.json:
        print(json.dumps({"title": args.title or None, "equations": rows}, indent=2))
        return 0

    title = (args.title or "").strip() or "(no title)"
    print(f"Preview: unpublished discussion '{title}' with {len(rows)} equation(s).")
    print("  New #\tSource #\tLaTeX")
    for r in rows:
        print(f"  {r['new']}\t{r['source']}\t{r['latex']}")
    return 0


def cmd_upload(args: argparse.Namespace) -> int:
    title = (args.title or "").strip()
    if not title:
        return _fail("A --title is required to create the discussion.")

    try:
        source_kind, selected = _selected(args.file, args.range)
    except ValueError as exc:
        return _fail(f"Could not understand that range: {exc}")
    except Exception as exc:
        return _fail(f"Could not read that file: {exc}")

    if not selected:
        return _fail(
            _no_equations_hint(source_kind)
            if args.range in ("", None)
            else "No equations match that range; nothing to upload."
        )

    labeled = [(renumber_label(i + 1, eq.suffix), eq.latex) for i, eq in enumerate(selected)]
    message_html = build_discussion_message(labeled)

    try:
        result = create_equation_discussion(
            args.course_id,
            title,
            message_html,
            api_key=args.token,
        )
    except Exception as exc:
        return _fail(friendly_canvas_error(exc))

    if result.success and result.discussion_id and result.course_id:
        link = discussion_url(result.course_id, result.discussion_id)
        print(f"Draft created with {len(labeled)} equation(s): {title}")
        print(f"  Review and publish in Canvas: {link}")
        return 0

    if result.success:
        print(result.detail)
        return 0

    return _fail(result.detail)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="canvas_discussion",
        description="Extract equations from a PDF/Markdown file and manage Canvas discussion drafts.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Canvas API token (defaults to CANVAS_API_KEY env / .env).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_courses = sub.add_parser("courses", help="List Canvas teacher courses.")
    p_courses.add_argument("--show-all", action="store_true", help="Include older/unpublished courses.")
    p_courses.add_argument("--json", action="store_true", help="Emit JSON.")
    p_courses.set_defaults(func=cmd_courses)

    p_extract = sub.add_parser("extract", help="List numbered equations in a file.")
    p_extract.add_argument("file", help="Path to a .pdf or .md file.")
    p_extract.add_argument("--json", action="store_true", help="Emit JSON.")
    p_extract.set_defaults(func=cmd_extract)

    p_session = sub.add_parser(
        "session",
        help="Collect display equations from the current Claude Code conversation.",
    )
    p_session.add_argument(
        "--transcript",
        default=None,
        help="Path to a specific .jsonl transcript (defaults to the most recent for this project).",
    )
    p_session.add_argument(
        "--project-dir",
        default=None,
        help="Override the Claude Code projects folder to search for the transcript.",
    )
    p_session.add_argument(
        "--out",
        default=None,
        help="Where to write the materialized Markdown (defaults to a temp file).",
    )
    p_session.add_argument("--json", action="store_true", help="Emit JSON.")
    p_session.set_defaults(func=cmd_session)

    p_preview = sub.add_parser("preview", help="Show the renumbered selection for a range.")
    p_preview.add_argument("file", help="Path to a .pdf or .md file.")
    p_preview.add_argument("--range", default="", help="Range spec, e.g. '1-10,3b,5-1' (blank = all).")
    p_preview.add_argument("--title", default="", help="Discussion title (display only).")
    p_preview.add_argument("--json", action="store_true", help="Emit JSON.")
    p_preview.set_defaults(func=cmd_preview)

    p_upload = sub.add_parser("upload", help="Create an unpublished Canvas discussion draft.")
    p_upload.add_argument("file", help="Path to a .pdf or .md file.")
    p_upload.add_argument("--course-id", type=int, required=True, help="Target Canvas course id.")
    p_upload.add_argument("--title", required=True, help="Discussion title.")
    p_upload.add_argument("--range", default="", help="Range spec, e.g. '1-10,3b,5-1' (blank = all).")
    p_upload.set_defaults(func=cmd_upload)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
