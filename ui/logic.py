"""Pure, framework-free UI logic: formatting, status classification, validation, error text.

Everything here only *reads* engine results. No scientific value is computed or altered.
The gate threshold wording mirrors ``app/core/evidence.py``; ``tests/test_ui_logic.py``
checks that the two stay consistent.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Optional

# Mirrors app/core/evidence.py::gate (display text only; the engine remains the authority).
GATE_REASON_TEXT = {
    "too_few_tentative_matches": "Fewer than 8 tentative matches were found.",
    "too_few_inliers": "Fewer than 12 independent geometric inliers survived RANSAC.",
    "low_inlier_ratio": "Inlier ratio is below 0.35.",
    "low_spatial_coverage": "Inliers cover less than 35% of the 4×4 spatial grid.",
    "high_or_missing_rmse": "RMSE is above 2.5 px, or no RMSE could be computed.",
}

# tone -> (symbol, label used for assistive text)
TONE_SYMBOL = {"ok": "✓", "warn": "▲", "bad": "✕", "info": "●", "mute": "○"}


def is_missing(v: Any) -> bool:
    if v is None:
        return True
    try:
        return isinstance(v, float) and math.isnan(v)
    except Exception:
        return False


def fmt_num(v: Any, digits: int = 3, unit: str = "") -> str:
    if is_missing(v):
        return "—"
    try:
        return f"{float(v):.{digits}f}{(' ' + unit) if unit else ''}"
    except Exception:
        return str(v)


def fmt_int(v: Any) -> str:
    return "—" if is_missing(v) else f"{int(v):,}"


def fmt_pct(v: Any, digits: int = 1) -> str:
    return "—" if is_missing(v) else f"{float(v) * 100:.{digits}f}%"


def sensor_label(sensor: str) -> str:
    return "TMC-2" if str(sensor).upper() in {"TMC2", "TMC"} else str(sensor).upper()


def gate_status_tone(status: Any) -> tuple[str, str]:
    """(tone, label). Green is used for VALIDATED only; anything else is never 'ok'."""
    s = str(status or "UNKNOWN").upper()
    if s == "VALIDATED":
        return "ok", "Passed"
    if "INSUFFICIENT" in s:
        return "warn", "Insufficient evidence"
    if s in {"ERROR", "REJECTED", "FAILED"}:
        return "bad", "Failed"
    return "mute", "Unknown"


def gate_reasons(result_or_diag: Any) -> list[str]:
    d = result_or_diag if isinstance(result_or_diag, dict) else (getattr(result_or_diag, "diagnostics", None) or {})
    return [str(r) for r in (d.get("gate_reasons") or [])]


def humanize_reason(code: str) -> str:
    return GATE_REASON_TEXT.get(code, code)


def evidence_claims(result: Any) -> list[dict[str, str]]:
    """Four distinct claims; never collapsed into one green badge."""
    diag = getattr(result, "diagnostics", None) or {}
    has_h = getattr(result, "homography", None) is not None
    tone, label = gate_status_tone(diag.get("status"))
    reasons = gate_reasons(result)
    return [
        {"q": "Processing completed", "tone": "info", "label": "Completed",
         "detail": f"Engine returned a result in {fmt_num(diag.get('elapsed_s'), 1, 's')}. This says nothing about quality."},
        {"q": "Transformation estimated", "tone": "info" if has_h else "warn",
         "label": "Estimated" if has_h else "Not estimated",
         "detail": "A homography was returned by RANSAC." if has_h else "No homography could be estimated from the correspondences."},
        {"q": "Evidence gate (configured thresholds)", "tone": tone, "label": label,
         "detail": "All gate conditions were met." if tone == "ok" else
                   (f"{len(reasons)} condition(s) not met — see gate interpretation." if reasons else "No gate reasons were returned.")},
        {"q": "Independent ground-truth validation", "tone": "mute", "label": "Not established",
         "detail": "This software does not compare against independent ground truth; the gate is an internal consistency test."},
    ]


def validate_selection(ids: dict[str, dict], ref_id: str, src_id: str) -> list[tuple[str, str]]:
    """Pre-run checks. Returns [(tone, message)]; any 'bad' blocks execution."""
    out: list[tuple[str, str]] = []
    if ref_id == src_id:
        out.append(("bad", "Choose two different products for a correspondence experiment."))
        return out
    r, s = ids.get(ref_id, {}), ids.get(src_id, {})
    if r.get("sensor") == s.get("sensor"):
        out.append(("warn", f"Both products are {sensor_label(r.get('sensor', ''))}. The platform targets cross-sensor pairs; same-sensor runs are not a validated use case."))
    for tag, x in (("Reference", r), ("Source", s)):
        if is_missing(x.get("gsd_m")):
            out.append(("warn", f"{tag} product reports no GSD in its metadata; the physical-scale plan may fail or fall back."))
    return out


def explain_error(exc: BaseException) -> tuple[str, str]:
    """(summary, suggested action) in plain language. The raw message is always shown separately."""
    name = type(exc).__name__
    if isinstance(exc, FileNotFoundError):
        return "A file referenced by the product label could not be found.", "Check that the .img/.xml/geometry files sit together in the mission folder and were not moved."
    if isinstance(exc, MemoryError):
        return "The run ran out of memory.", "Close other applications and retry; use a smaller sensor pair first."
    if isinstance(exc, ValueError) and "adapter" in str(exc).lower():
        return "No reader could interpret this product.", "Confirm the product is a supported PDS4 / ENVI / raw+sidecar product."
    if isinstance(exc, ImportError):
        return "A required Python package is missing.", "Run RUN_CHANDRABHAR-2.bat again to install requirements."
    return f"The engine raised {name}.", "Open the technical details below; the exact message is preserved for debugging."


def result_row(name: str, res: Any) -> dict[str, Any]:
    d = getattr(res, "diagnostics", None) or {}
    return {"Pair": name.replace("_", " ↔ "), "Gate": gate_status_tone(d.get("status"))[1], "Matches": res.tentative_matches,
            "Inliers": res.inliers, "Inlier ratio": round(res.inlier_ratio, 4), "Coverage": round(res.coverage, 4),
            "RMSE (m)": d.get("rmse_m")}


def readiness(row: dict[str, Any]) -> tuple[str, str, str]:
    """Metadata readiness for a scanned product -> (tone, label, note).

    Deliberately says 'metadata parsed' — pixel data is only read during processing.
    """
    if is_missing(row.get("gsd_m")):
        return "warn", "GSD missing", "Metadata parsed but no ground-sample distance was found."
    return "info", "Metadata parsed", "Pixel data is read only when a run starts; nothing is validated yet."


def chunk(seq: Iterable, n: int):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]
