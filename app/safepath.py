"""Defensive helpers for untrusted mission files.

Mission labels (PDS4 XML, ENVI headers, JSON sidecars) are untrusted input.  Every
filename a label refers to is resolved through :func:`resolve_companion`, which can
only return a path that lies inside the declared workspace root.  Labels can never
cause the engine to open files elsewhere.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

MAX_LABEL_BYTES = 20 * 1024 * 1024        # PDS4 / ENVI / JSON label ceiling
MAX_SNIFF_BYTES = 200_000                  # bytes inspected by can_open() probes
MAX_DIM = 2_000_000_000                    # absolute per-axis ceiling for declared dims
_UNSAFE_NAME = re.compile(r"[\x00-\x1f\\/:*?\"<>|]")


class UnsafePathError(ValueError):
    """Raised when a label-supplied name would escape the workspace."""


def clean_name(name: str) -> str:
    """Return *name* if it is a plain single path component, else raise."""
    if name is None:
        raise UnsafePathError("empty file name")
    n = str(name).strip()
    if not n or n in {".", ".."}:
        raise UnsafePathError(f"invalid file name {name!r}")
    if _UNSAFE_NAME.search(n):
        raise UnsafePathError(f"file name {name!r} contains path separators or control characters")
    if len(n) > 255:
        raise UnsafePathError("file name too long")
    return n


def is_within(root: Path, candidate: Path) -> bool:
    try:
        root_r = Path(os.path.abspath(root))
        cand_r = Path(os.path.abspath(candidate))
        cand_r.relative_to(root_r)
        return True
    except ValueError:
        return False


def confine(root: Optional[Path], candidate: Path) -> Path:
    """Return *candidate* only if it lies inside *root* (when a root is given)."""
    if root is not None and not is_within(Path(root), Path(candidate)):
        raise UnsafePathError(f"{candidate} is outside the workspace")
    return Path(candidate)


def resolve_companion(base_dir: Path, name: str, root: Optional[Path] = None) -> Optional[Path]:
    """Resolve a label-supplied companion *name* beside *base_dir* (plain names only)."""
    n = clean_name(name)
    p = Path(base_dir) / n
    confine(root, p)
    return p if p.exists() else None


def read_text_limited(path: Path, limit: int = MAX_LABEL_BYTES, head: Optional[int] = None) -> str:
    path = Path(path)
    size = path.stat().st_size
    if head is None and size > limit:
        raise ValueError(f"{path.name}: {size} bytes exceeds the {limit}-byte label limit")
    with path.open("rb") as f:
        raw = f.read(head if head is not None else limit)
    return raw.decode("utf-8", errors="ignore")


def parse_xml_safe(path: Path) -> ET.Element:
    """Parse XML while rejecting DTD/entity declarations (entity-expansion attacks)."""
    txt = read_text_limited(path)
    low = txt[:200_000].lower()
    if "<!entity" in low or "<!doctype" in low and "[" in low.split("<!doctype", 1)[1][:2000]:
        raise ValueError("XML label declares a DTD/entities; refused for safety")
    return ET.fromstring(txt)


def checked_shape(shape) -> tuple:
    out = []
    for s in shape:
        s = int(s)
        if s <= 0 or s > MAX_DIM:
            raise ValueError(f"invalid dimension {s}")
        out.append(s)
    if not out:
        raise ValueError("empty shape")
    return tuple(out)
