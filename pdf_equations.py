"""Extract numbered equations from PDF files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz

EQ_LABEL_RE = re.compile(r"^\((\d+)([a-zA-Z]+|-\d+)?\)$")

UNICODE_TO_LATEX: dict[str, str] = {
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "θ": r"\theta",
    "λ": r"\lambda",
    "μ": r"\mu",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "φ": r"\phi",
    "ω": r"\omega",
    "Δ": r"\Delta",
    "Σ": r"\Sigma",
    "Ω": r"\Omega",
    "∞": r"\infty",
    "≤": r"\leq",
    "≥": r"\geq",
    "≠": r"\neq",
    "≈": r"\approx",
    "±": r"\pm",
    "×": r"\times",
    "÷": r"\div",
    "∂": r"\partial",
    "∇": r"\nabla",
    "√": r"\sqrt",
    "·": r"\cdot",
    "…": r"\ldots",
    "→": r"\rightarrow",
    "←": r"\leftarrow",
    "⇒": r"\Rightarrow",
    "⇐": r"\Leftarrow",
    "⇔": r"\Leftrightarrow",
    "−": "-",
    "–": "-",
    "—": "-",
    "˙": r"\dot",
    "∗": r"^{*}",
}

SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾", "0123456789+-=()")
SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", "0123456789+-=()")


@dataclass
class TextLine:
    text: str
    y: float
    page: int


@dataclass
class Equation:
    label: str
    suffix: str
    base: int
    latex: str
    page: int
    order: int


_ocr_model = None


def renumber_label(sequence: int, suffix: str) -> str:
    return f"{sequence}{suffix}"


def _get_ocr_model():
    global _ocr_model
    if _ocr_model is None:
        from pix2tex.cli import LatexOCR

        _ocr_model = LatexOCR()
    return _ocr_model


def _collect_lines(doc: fitz.Document) -> list[TextLine]:
    lines: list[TextLine] = []
    for page_idx, page in enumerate(doc):
        block_data = page.get_text("dict")
        for block in block_data.get("blocks", []):
            for line in block.get("lines", []):
                text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if not text:
                    continue
                y_vals = [span["bbox"][1] for span in line.get("spans", [])]
                y = sum(y_vals) / len(y_vals) if y_vals else 0.0
                lines.append(TextLine(text=text, y=y, page=page_idx))
    return lines


def _normalize_to_latex(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        matched = False
        for uchar, latex in UNICODE_TO_LATEX.items():
            if text.startswith(uchar, i):
                out.append(latex)
                i += len(uchar)
                matched = True
                break
        if matched:
            continue
        ch = text[i]
        if ch in "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾":
            sup = ch.translate(SUPERSCRIPT_MAP)
            out.append(f"^{{{sup}}}" if len(sup) > 1 else f"^{sup}")
            i += 1
            continue
        if ch in "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎":
            sub = ch.translate(SUBSCRIPT_MAP)
            out.append(f"_{{{sub}}}" if len(sub) > 1 else f"_{sub}")
            i += 1
            continue
        out.append(ch)
        i += 1

    cleaned = "".join(out)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\b([A-Za-z])2\b", r"\1^2", cleaned)
    cleaned = re.sub(r"\b([A-Za-z])3\b", r"\1^3", cleaned)
    cleaned = re.sub(r"\\rho([a-z])", r"\\rho \1", cleaned)
    cleaned = re.sub(r"\\Leftarrow\\Rightarrow", r"\\Leftrightarrow ", cleaned)
    cleaned = re.sub(r"\\dot([a-z])", r"\\dot{\1}", cleaned)
    cleaned = re.sub(r"\bv\^2 2\b", r"\\frac{v^2}{2}", cleaned)
    return cleaned


def _parse_label_line(text: str) -> tuple[str, int, str] | None:
    m = EQ_LABEL_RE.match(text.strip())
    if not m:
        return None
    base = int(m.group(1))
    suffix = m.group(2) or ""
    label = f"{base}{suffix}"
    return label, base, suffix


def _is_body_line(text: str) -> bool:
    t = text.strip()
    if not t or EQ_LABEL_RE.match(t):
        return False
    if t.startswith("(γ") or t.startswith("(γ "):
        return False
    if re.match(r"^Section\s+\d+\s*$", t, re.I):
        return False
    if re.search(r"derivation|numbered equations", t, re.I) and "=" not in t:
        return False
    if len(t) > 80 and "=" not in t:
        return False
    if re.match(r"^[\w\\^_{}\s.+-]+$", t) and t.endswith("="):
        return True
    if len(t) <= 12 and re.match(r"^[\w\\^_{}\s.+-]+$", t):
        return True
    return bool(re.search(r"[=+\-*/^≤≥≈]", t) or re.search(r"\\|[A-Za-z]\s*=", t))


def _body_before_label(page_lines: list[TextLine], label_idx: int) -> str:
    parts: list[str] = []
    for j in range(label_idx - 1, -1, -1):
        t = page_lines[j].text.strip()
        if EQ_LABEL_RE.match(t):
            break
        if re.match(r"^Section\s+\d+\s*$", t, re.I):
            break
        if _is_body_line(t):
            parts.insert(0, t)
        elif parts:
            break
    joined = " ".join(parts)
    joined = re.sub(r"\s+=\s+", " = ", joined)
    return joined


def _needs_ocr(text: str) -> bool:
    if not text or len(text) < 2:
        return True
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
    return ascii_ratio < 0.55


def _ocr_equation(doc: fitz.Document, page: int, bbox: fitz.Rect) -> str:
    from PIL import Image
    import io

    pg = doc[page]
    pix = pg.get_pixmap(clip=bbox, matrix=fitz.Matrix(3, 3))
    image = Image.open(io.BytesIO(pix.tobytes("png")))
    return _get_ocr_model()(image)


def extract_equations(pdf_path: str | Path) -> list[Equation]:
    path = Path(pdf_path)
    doc = fitz.open(path)
    try:
        all_lines = _collect_lines(doc)
        by_page: dict[int, list[TextLine]] = {}
        for line in all_lines:
            by_page.setdefault(line.page, []).append(line)

        equations: list[Equation] = []
        order = 0
        for page_idx in sorted(by_page):
            page_lines = by_page[page_idx]
            for idx, line in enumerate(page_lines):
                parsed = _parse_label_line(line.text)
                if parsed is None:
                    continue
                label, base, suffix = parsed
                raw = _body_before_label(page_lines, idx)
                latex = _normalize_to_latex(raw)
                if _needs_ocr(latex):
                    page = doc[page_idx]
                    y0 = page_lines[max(0, idx - 3)].y if idx > 0 else line.y - 20
                    bbox = fitz.Rect(page.rect.width * 0.05, y0 - 4, page.rect.width * 0.9, line.y + 12)
                    try:
                        latex = _ocr_equation(doc, page_idx, bbox)
                    except Exception:
                        pass
                if latex:
                    equations.append(
                        Equation(
                            label=label,
                            suffix=suffix,
                            base=base,
                            latex=latex.strip(),
                            page=page_idx + 1,
                            order=order,
                        )
                    )
                    order += 1

        return equations
    finally:
        doc.close()


def _parse_range_token(token: str, by_label: dict[str, Equation]) -> set[str]:
    token = token.strip()
    if not token:
        return set()

    if token in by_label:
        return {token}

    if re.fullmatch(r"\d+-\d+", token):
        start_s, end_s = token.split("-", 1)
        start, end = int(start_s), int(end_s)
        if start > end:
            start, end = end, start
        return {eq.label for eq in by_label.values() if start <= eq.base <= end}

    if re.fullmatch(r"\d+", token):
        base = int(token)
        return {eq.label for eq in by_label.values() if eq.base == base}

    return set()


def parse_equation_range(spec: str, equations: list[Equation]) -> list[Equation]:
    """Parse range spec against available equations; returns in document order."""
    if not equations:
        return []

    by_label = {eq.label: eq for eq in equations}

    spec = spec.strip()
    if not spec:
        return list(equations)

    wanted: set[str] = set()
    for part in spec.split(","):
        wanted.update(_parse_range_token(part, by_label))

    return [eq for eq in equations if eq.label in wanted]