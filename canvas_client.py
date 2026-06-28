"""Canvas LMS API helpers for course listing and discussion creation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from canvasapi import Canvas
from canvasapi.exceptions import CanvasException, Unauthorized
from dotenv import load_dotenv

load_dotenv()

CANVAS_BASE_URL = "https://uc.instructure.com"
TWO_YEARS_DAYS = 730


@dataclass
class CourseOption:
    course_id: int
    label: str


@dataclass
class UploadResult:
    title: str
    success: bool
    detail: str
    discussion_id: int | None = None
    course_id: int | None = None


def friendly_canvas_error(exc: Exception) -> str:
    if isinstance(exc, Unauthorized):
        return (
            "Canvas didn't accept that token. Open Canvas → Account → Settings → "
            "Approved Integrations, generate a new access token, and try again."
        )
    if isinstance(exc, CanvasException):
        msg = str(exc).strip()
        if "401" in msg or "unauthorized" in msg.lower():
            return (
                "Canvas didn't accept that token. Generate a new access token "
                "in your Canvas account settings and try again."
            )
        if "403" in msg or "forbidden" in msg.lower():
            return "Canvas denied access. Make sure your token is still active and you are enrolled as a teacher."
        return f"Canvas returned an error: {msg}"
    if isinstance(exc, RuntimeError):
        return str(exc)
    return f"Something went wrong while contacting Canvas: {exc}"


def _resolve_api_key(api_key: str | None) -> str:
    key = (api_key or "").strip() or os.environ.get("CANVAS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Enter your Canvas API token in Step 1 before continuing.")
    return key


def _client(api_key: str | None = None) -> Canvas:
    key = _resolve_api_key(api_key)
    url = os.environ.get("CANVAS_API_URL", CANVAS_BASE_URL).rstrip("/")
    return Canvas(url, key)


def discussion_url(course_id: int, discussion_id: int) -> str:
    base = os.environ.get("CANVAS_API_URL", CANVAS_BASE_URL).rstrip("/")
    return f"{base}/courses/{course_id}/discussion_topics/{discussion_id}"


def _parse_canvas_date(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


def _reference_date(course) -> datetime | None:
    for attr in ("start_at", "end_at", "created_at"):
        parsed = _parse_canvas_date(getattr(course, attr, None))
        if parsed is not None:
            return parsed
    return None


def list_teacher_courses(*, api_key: str | None = None, show_all: bool = False) -> list[CourseOption]:
    canvas = _client(api_key)
    cutoff = datetime.now(timezone.utc) - timedelta(days=TWO_YEARS_DAYS)
    options: list[CourseOption] = []
    dated: list[tuple[datetime, CourseOption]] = []

    for course in canvas.get_courses(enrollment_type="teacher"):
        state = getattr(course, "workflow_state", None)
        if state == "deleted":
            continue

        if not show_all:
            if state != "available":
                continue
            ref = _reference_date(course)
            if ref is None or ref < cutoff:
                continue

        code = getattr(course, "course_code", None) or "?"
        name = getattr(course, "name", None) or "Unnamed"
        state_tag = f" [{state}]" if state and state != "available" else ""
        option = CourseOption(
            course_id=int(course.id),
            label=f"{code} — {name}{state_tag}",
        )

        if show_all:
            options.append(option)
        else:
            dated.append((_reference_date(course) or datetime.min.replace(tzinfo=timezone.utc), option))

    if show_all:
        options.sort(key=lambda c: c.label.lower())
        return options

    dated.sort(key=lambda item: item[0], reverse=True)
    return [option for _, option in dated]


def create_equation_discussion(
    course_id: int,
    title: str,
    message_html: str,
    *,
    api_key: str | None = None,
) -> UploadResult:
    """Create a single unpublished discussion with all equations in the message body."""
    canvas = _client(api_key)
    course = canvas.get_course(course_id)
    try:
        topic = course.create_discussion_topic(
            title=title,
            message=message_html,
            published=False,
        )
        return UploadResult(
            title=title,
            success=True,
            detail="Saved as an unpublished draft in Canvas.",
            discussion_id=int(topic.id),
            course_id=course_id,
        )
    except Exception as exc:
        return UploadResult(
            title=title,
            success=False,
            detail=friendly_canvas_error(exc),
            course_id=course_id,
        )


def upload_course_file(
    course_id: int,
    filepath: str,
    *,
    api_key: str | None = None,
) -> str:
    """Upload a local file to the course's Files area and return its URL."""
    canvas = _client(api_key)
    course = canvas.get_course(course_id)
    try:
        success, response = course.upload(filepath)
        if success and "url" in response:
            return response["url"]
        else:
            raise RuntimeError("Canvas did not return a valid URL after upload.")
    except Exception as exc:
        raise RuntimeError(friendly_canvas_error(exc)) from exc