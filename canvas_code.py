"""Render Python source into Canvas Rich Content Editor HTML.

Produces a readable, numbered-line code listing as a single ``<div>`` block.

Design points that matter for Canvas (confirmed by inspecting stored discussion
HTML):

- **One block, line numbers embedded per line.** Earlier two-column layouts put
  numbers and code in separate elements; Canvas wraps long lines, which slid the
  code down while the number column did not, so the numbering visibly desynced.
  Prefixing each line with its own number means a wrapped line can never lose its
  number.
- **A ``<pre>`` element, not a ``<div>`` with ``white-space``.** Canvas's
  sanitizer **strips the ``white-space`` property** from inline ``style`` (a
  ``<div style="white-space:pre-wrap">`` came back with that property removed, so
  every line collapsed onto one line). ``<pre>`` preserves whitespace and line
  breaks via the browser's user-agent stylesheet, which is *not* an inline-style
  attribute and so cannot be stripped. Its only downside — Canvas's default block
  margin (the "excessive blank lines above/below") — is removed with an inline
  ``margin:0``, which Canvas *does* keep.

Long lines do not wrap (``<pre>`` defaults to no-wrap); they extend with a
horizontal scrollbar. That is fine here — line numbers are embedded per line, so
nothing can desync regardless of wrapping.

No syntax highlighting and no extra dependencies.
"""

from __future__ import annotations

MONO = "Menlo, Consolas, 'Courier New', monospace"

CODE_PRE_STYLE = (
    "margin:0; padding:8px; "
    f"font-family:{MONO}; font-size:13px; line-height:1.4; "
    "background:#f6f8fa; border:1px solid #e1e4e8; border-radius:4px;"
)


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def description_html(text: str | None) -> str:
    """Render optional normal-text description as a paragraph (blank -> '')."""
    text = (text or "").strip()
    if not text:
        return ""
    safe = escape_html(text).replace("\n", "<br>")
    return f"<p>{safe}</p>"


def build_code_message(
    filename: str,
    numbered_lines: list[tuple[int, str]],
    description: str | None = None,
) -> str:
    """Build a discussion body for ``(line_no, text)`` pairs (original numbers)."""
    width = max((len(str(n)) for n, _ in numbered_lines), default=1)
    body = "\n".join(
        f"{str(n).rjust(width)} | {escape_html(text.rstrip(chr(10)))}"
        for n, text in numbered_lines
    )
    return (
        f"{description_html(description)}"
        f'<pre style="{CODE_PRE_STYLE}">{body}</pre>'
    )


if __name__ == "__main__":
    sample = [
        (9, "def secant(f, x0, x1, iterations=7):"),
        (10, "    points = [x0, x1]"),
        (11, ""),
        (12, "        x2 = x1 - fx1  # update"),
    ]
    html = build_code_message("secant_demo.py", sample, description="Root finding demo.")
    assert html.count("<pre") == 1 and html.count("<div") == 0  # single <pre> block
    assert "white-space" not in html  # do not rely on a strippable style property
    assert "margin:0" in html  # kills <pre>'s default block margin (Canvas keeps it)
    assert "<p>Root finding demo.</p>" in html  # description rendered above
    # numbers embedded, right-justified to width 2, in the same block as the code
    assert " 9 | def secant" in html
    assert "10 |     points = [x0, x1]" in html
    assert "12 |         x2 = x1 - fx1" in html  # indentation preserved as real spaces
    print(html)
