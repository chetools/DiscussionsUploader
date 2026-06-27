"""Convert LaTeX strings to Canvas Rich Content Editor equation HTML."""

from __future__ import annotations

import urllib.parse


def _attr_latex(latex: str) -> str:
    return latex.replace("&", "&amp;")


def _encoded_src(latex: str) -> str:
    clean = latex.replace("&", "&")
    once = urllib.parse.quote(clean, safe="()")
    return urllib.parse.quote(once, safe="()&")


def _equation_line(label: str, latex: str) -> str:
    img = to_canvas_html(latex, inline=True, vertical_align_top=True)
    return (
        f'<p style="text-align:left;">'
        f"<strong>({label})</strong>&nbsp;&nbsp;{img}</p>"
    )


def build_discussion_message(equations: list[tuple[str, str]]) -> str:
    """Build one discussion body from (display_label, latex) pairs."""
    return "".join(_equation_line(label, latex) for label, latex in equations)


def to_canvas_html(
    latex: str,
    *,
    inline: bool = False,
    vertical_align_top: bool = False,
) -> str:
    """Wrap LaTeX in Canvas's equation_image img tag."""
    attr = _attr_latex(latex)
    src = _encoded_src(latex)
    style = ' style="vertical-align:top;"' if vertical_align_top else ""
    img = (
        f'<img class="equation_image"{style} title="{attr}" '
        f'src="/equation_images/{src}" alt="Latex: {attr}" '
        f'data-equation-content="{attr}" />'
    )
    if inline:
        return img
    return f"<p>{img}</p>"


if __name__ == "__main__":
    sample = r"\dot{m}=\rho A V"
    html = to_canvas_html(sample)
    assert "data-equation-content" in html
    assert "/equation_images/" in html
    print(html)