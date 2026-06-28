"""Unified extraction from PDF and Markdown sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from md_equations import extract_equations_from_markdown
from pdf_equations import Equation, extract_equations


@dataclass
class ExtractResult:
    equations: list[Equation]
    source_kind: str


def extract_from_file(path: str | Path) -> ExtractResult:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return ExtractResult(equations=extract_equations(path), source_kind="pdf")

    if suffix in {".md", ".markdown"}:
        return ExtractResult(
            equations=extract_equations_from_markdown(path),
            source_kind="markdown",
        )

    raise ValueError(f"Unsupported file type: {suffix}. Upload a PDF or Markdown (.md) file.")