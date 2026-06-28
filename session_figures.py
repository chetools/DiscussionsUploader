"""Discover image files (figures) mentioned in a Claude Code session.

Scans the active session's transcript for strings that look like file paths
ending in image extensions, and checks if they exist on disk.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# Reuse transcript discovery
from session_equations import discover_transcript

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
# Regex to find substrings that might be file paths ending in image extensions
PATH_RE = re.compile(r"([a-zA-Z0-9_\-\./\\]+\.(?:png|jpg|jpeg|svg|gif))", re.IGNORECASE)

@dataclass
class FigureFile:
    path: str
    absolute_path: Path
    size_bytes: int
    modified_time: datetime

def discover_session_figures(
    transcript_path: str | Path,
    cwd: str | Path | None = None
) -> list[FigureFile]:
    """Find unique, existing image files mentioned in the transcript."""
    cwd_path = Path(cwd) if cwd is not None else Path.cwd()
    seen: dict[Path, FigureFile] = {}
    
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            # Convert object to string to easily search for image paths
            content_str = json.dumps(obj)
            for match in PATH_RE.finditer(content_str):
                raw_path = match.group(1)
                
                # Filter out pure URLs if they happen to match
                if raw_path.startswith("http://") or raw_path.startswith("https://"):
                    continue
                    
                # Try to resolve path
                try:
                    # If it's absolute, Path(raw_path) keeps it absolute.
                    # If relative, we resolve relative to cwd_path.
                    p = Path(raw_path)
                    if not p.is_absolute():
                        p = cwd_path / p
                    p = p.resolve()
                    
                    if p not in seen and p.is_file():
                        stat = p.stat()
                        seen[p] = FigureFile(
                            path=raw_path,
                            absolute_path=p,
                            size_bytes=stat.st_size,
                            modified_time=datetime.fromtimestamp(stat.st_mtime)
                        )
                except Exception:
                    # Invalid path chars or permission errors
                    pass
                    
    # Return sorted by modified time, newest first
    return sorted(list(seen.values()), key=lambda f: f.modified_time, reverse=True)
