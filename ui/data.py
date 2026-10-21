"""Mission-data discovery (same label discovery as the original dashboard) with honest error capture."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def find_labels(root: Path) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.rglob("*.xml"):
        n = p.name.lower()
        if any(k in n for k in ("ch2_ohr", "ch2_tmc", "ch2_iir")):
            out.append(p)
    return sorted(out)


def scan_products(root_str: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Return (rows, errors). Products that fail to parse are reported, not silently dropped."""
    from app.adapters import AdapterRegistry

    root = Path(root_str)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for p in find_labels(root):
        try:
            s = AdapterRegistry.inspect(p)
            rows.append({
                "sensor": s.sensor,
                "product_id": s.product_id,
                "path": str(p),
                "shape": str(tuple(s.array.shape)),
                "dtype": str(s.array.dtype),
                "gsd_m": float(s.gsd_m) if s.gsd_m is not None else None,
                "solar_elevation_deg": s.solar_elevation_deg,
                "solar_azimuth_deg": s.solar_azimuth_deg,
                "acquisition_start": s.acquisition_start,
                "crs": s.crs,
                "geometry_table": bool((s.metadata or {}).get("geometry_csv")),
            })
        except Exception as exc:
            errors.append({"path": str(p), "error": f"{type(exc).__name__}: {exc}"})
    return rows, errors


def browse_images(root: Path, sensor: str, limit: int = 4):
    if not root.exists():
        return []
    hits = []
    for p in root.rglob("*.png"):
        up = str(p).upper()
        if sensor.upper() in up or (sensor.upper() == "TMC2" and "TMC" in up):
            hits.append(p)
    return sorted(hits)[:limit]
