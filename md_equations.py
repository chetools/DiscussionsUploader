"""Extract numbered equations from Markdown files (prose ignored)."""

from __future__ import annotations

import re
from pathlib import Path

from pdf_equations import Equation, strip_latex_boxes

DISPLAY_MATH_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
TAG_RE = re.compile(r"\\tag\{([^}]+)\}\s*$")
LABEL_PART_RE = re.compile(r"^(\d+)([a-zA-Z]+|-\d+)?$")


def _parse_label_string(label_str: str) -> tuple[str, int, str]:
    m = LABEL_PART_RE.match(label_str.strip())
    if not m:
        raise ValueError(f"Invalid equation label: {label_str!r}")
    base = int(m.group(1))
    suffix = m.group(2) or ""
    return f"{base}{suffix}", base, suffix


def extract_equations_from_markdown(path: str | Path) -> list[Equation]:
    text = Path(path).read_text(encoding="utf-8")
    equations: list[Equation] = []
    order = 0

    for match in DISPLAY_MATH_RE.finditer(text):
        math_content = match.group(1).strip()
        tag_match = TAG_RE.search(math_content)
        if not tag_match:
            continue
        latex = strip_latex_boxes(TAG_RE.sub("", math_content).strip())
        label, base, suffix = _parse_label_string(tag_match.group(1))
        equations.append(
            Equation(
                label=label,
                suffix=suffix,
                base=base,
                latex=latex,
                page=1,
                order=order,
            )
        )
        order += 1

    return equations