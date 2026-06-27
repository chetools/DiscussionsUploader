"""Canvas LMS API helpers for course listing and discussion creation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from canvasapi import Canvas
from dotenv import load_dotenv

load_dotenv()

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


def _client() -> Canvas:
    url = os.environ.get("CANVAS_API_URL", "").rstrip("/")
    key = os.environ.get("CANVAS_API_KEY", "")
    if not url or not key:
        raise RuntimeError("Set CANVAS_API_URL and CANVAS_API_KEY in .env")
    return Canvas(url, key)


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


def list_teacher_courses(*, show_all: bool = False) -> list[CourseOption]:
    canvas = _client()
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
            label=f"{code} — {name}{state_tag} (id={course.id})",
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
) -> UploadResult:
    """Create a single discussion with all equations in the message body."""
    canvas = _client()
    course = canvas.get_course(course_id)
    try:
        topic = course.create_discussion_topic(
            title=title,
            message=message_html,
            published=True,
        )
        return UploadResult(
            title=title,
            success=True,
            detail="Created",
            discussion_id=int(topic.id),
        )
    except Exception as exc:
        return UploadResult(title=title, success=False, detail=str(exc))