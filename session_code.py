"""Discover Python files generated in a Claude Code session and select lines.

Generated Python in a Claude Code conversation is not pasted as fenced code in
the chat text — it is written to disk via ``Write``/``Edit`` tool calls. So the
transcript is only used to *discover which ``.py`` files were touched*; the
actual content is read from the file's current on-disk state. Line selection
preserves the file's original 1-based line numbers.
"""

from __future__ import annotations

import io
import json
import re
import tokenize
import ast
from dataclasses import dataclass
from pathlib import Path

# Reuse the same transcript discovery used by the equation session source.
from session_equations import discover_transcript  # noqa: F401  (re-exported)

EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


@dataclass
class PyFile:
    path: str
    exists: bool
    line_count: int


def _file_path_from_tool_use(block: dict) -> str | None:
    inp = block.get("input") or {}
    path = inp.get("file_path") or inp.get("notebook_path")
    if isinstance(path, str) and path.lower().endswith(".py"):
        return path
    return None


def discover_session_py_files(transcript_path: str | Path) -> list[PyFile]:
    """Distinct .py files written/edited in the transcript, first-seen order."""
    seen: dict[str, None] = {}
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
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                if block.get("name") not in EDIT_TOOLS:
                    continue
                path = _file_path_from_tool_use(block)
                if path is not None and path not in seen:
                    seen[path] = None

    files: list[PyFile] = []
    for path in seen:
        p = Path(path)
        exists = p.is_file()
        count = len(read_file_lines(p)) if exists else 0
        files.append(PyFile(path=path, exists=exists, line_count=count))
    return files


def read_file_lines(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    # splitlines() drops a trailing newline without inventing a final empty line.
    return text.splitlines()


def parse_line_spec(spec: str, total: int) -> list[int]:
    """Parse '9-17,20,25-30' into sorted unique 1-based lines within [1, total]."""
    spec = (spec or "").strip()
    if not spec:
        return list(range(1, total + 1))

    wanted: set[int] = set()
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", token)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
            if start > end:
                start, end = end, start
            for n in range(start, end + 1):
                if 1 <= n <= total:
                    wanted.add(n)
            continue
        if re.fullmatch(r"\d+", token):
            n = int(token)
            if 1 <= n <= total:
                wanted.add(n)
            continue
        raise ValueError(f"Invalid line token: {token!r}")

    return sorted(wanted)


def strip_comments_from_lines(lines: list[str]) -> tuple[list[str], set[int]]:
    """Remove Python ``#`` comments.

    Returns ``(new_lines, dropped)`` where ``new_lines`` has inline comments
    trimmed (code kept) and ``dropped`` is the set of 1-based line numbers that
    were comment-only (to be omitted entirely). Uses ``tokenize`` so a ``#``
    inside a string literal is never treated as a comment. Falls back to a
    simple full-line-comment scan if the source can't be tokenized.
    """
    new_lines = list(lines)
    dropped: set[int] = set()
    source = "\n".join(lines) + "\n"
    
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    for r in range(node.lineno, node.end_lineno + 1):
                        dropped.add(r)
    except SyntaxError:
        pass

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        for i, line in enumerate(lines, start=1):
            if line.lstrip().startswith("#"):
                dropped.add(i)
        return new_lines, dropped

    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        row, col = tok.start
        if not 1 <= row <= len(new_lines):
            continue
        before = new_lines[row - 1][:col]
        if before.strip() == "":
            dropped.add(row)          # comment-only line → drop entirely
        else:
            new_lines[row - 1] = before.rstrip()  # inline comment → keep code
    return new_lines, dropped


def select_numbered_lines(
    lines: list[str], spec: str, *, exclude_comments: bool = False
) -> list[tuple[int, str]]:
    """Return (original_line_no, text) pairs for the selected lines."""
    dropped: set[int] = set()
    if exclude_comments:
        lines, dropped = strip_comments_from_lines(lines)
    chosen = parse_line_spec(spec, len(lines))
    return [(n, lines[n - 1]) for n in chosen if n not in dropped]
