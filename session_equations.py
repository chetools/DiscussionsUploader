"""Extract display equations from a Claude Code conversation transcript.

Claude Code stores each conversation as a JSONL transcript under
``~/.claude/projects/<cwd-slug>/<session-id>.jsonl``. Every ``$$...$$`` (and
``\\[...\\]``) display-math block a human or Claude wrote in chat ends up in the
``message.content`` text of those lines. This module scans a transcript, pulls
out those display equations, dedupes them, numbers them sequentially, and
returns the same ``Equation`` dataclass the rest of the skill uses — so they can
be materialized to Markdown and flow through the existing preview/upload path.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from pdf_equations import Equation, strip_latex_boxes

# Display-math delimiters only (inline ``$...$`` is intentionally ignored).
DISPLAY_RES = (
    re.compile(r"\$\$(.+?)\$\$", re.DOTALL),
    re.compile(r"\\\[(.+?)\\\]", re.DOTALL),
)
TAG_RE = re.compile(r"\\tag\{[^}]*\}")
LABEL_RE = re.compile(r"\\label\{[^}]*\}")
NONUMBER_RE = re.compile(r"\\nonumber\b")


def transcript_slug(cwd: str | Path | None = None) -> str:
    """Map a working directory to its Claude Code project-folder slug."""
    abs_cwd = os.path.abspath(str(cwd) if cwd is not None else os.getcwd())
    return re.sub(r"[^A-Za-z0-9]", "-", abs_cwd)


def project_transcript_dir(project_dir: str | Path | None = None, cwd: str | Path | None = None) -> Path:
    if project_dir is not None:
        return Path(project_dir)
    return Path.home() / ".claude" / "projects" / transcript_slug(cwd)


def discover_transcript(
    project_dir: str | Path | None = None,
    cwd: str | Path | None = None,
) -> Path:
    """Return the most-recently-modified ``.jsonl`` (i.e. the active session)."""
    folder = project_transcript_dir(project_dir, cwd)
    if not folder.is_dir():
        raise FileNotFoundError(
            f"No Claude Code transcript folder at {folder}. Pass --transcript to "
            "point at a specific .jsonl conversation file."
        )
    candidates = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(
            f"No .jsonl transcripts found in {folder}. Pass --transcript to point "
            "at a specific conversation file."
        )
    return candidates[0]


def _iter_text_blocks(transcript_path: str | Path, roles: tuple[str, ...]):
    """Yield each message text block whose role is in ``roles``, in order."""
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = obj.get("message")
            if not isinstance(message, dict):
                continue
            if message.get("role") not in roles:
                continue
            content = message.get("content")
            if isinstance(content, str):
                yield content
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        yield block.get("text", "")


def _clean_latex(raw: str) -> str:
    latex = raw.strip()
    latex = TAG_RE.sub("", latex)
    latex = LABEL_RE.sub("", latex)
    latex = NONUMBER_RE.sub("", latex)
    return strip_latex_boxes(latex.strip())


def extract_session_equations(
    transcript_path: str | Path,
    roles: tuple[str, ...] = ("user", "assistant"),
) -> list[Equation]:
    """Pull deduped, sequentially-numbered display equations from a transcript."""
    equations: list[Equation] = []
    seen: set[str] = set()

    for text in _iter_text_blocks(transcript_path, roles):
        if not text:
            continue
        for pattern in DISPLAY_RES:
            for match in pattern.finditer(text):
                latex = _clean_latex(match.group(1))
                if not latex or not re.search(r"[A-Za-z0-9]", latex):
                    continue
                key = re.sub(r"\s+", " ", latex)
                if key in seen:
                    continue
                seen.add(key)
                seq = len(equations) + 1
                equations.append(
                    Equation(
                        label=str(seq),
                        suffix="",
                        base=seq,
                        latex=latex,
                        page=1,
                        order=seq - 1,
                    )
                )

    return equations


def write_session_markdown(equations: list[Equation], out_path: str | Path) -> Path:
    """Write equations as ``$$ <latex> \\tag{N} $$`` blocks for the .md pipeline."""
    out_path = Path(out_path)
    lines: list[str] = []
    for eq in equations:
        lines.append("$$")
        lines.append(f"{eq.latex} \\tag{{{eq.label}}}")
        lines.append("$$")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
