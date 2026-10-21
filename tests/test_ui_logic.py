"""UI-layer tests (pure Python; no Streamlit needed). They verify presentation logic only —
they say nothing about scientific validity of any result."""
import re
import tomllib
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from app.core.evidence import gate
from ui import components as C
from ui.logic import (GATE_REASON_TEXT, evidence_claims, fmt_int, fmt_num, fmt_pct, gate_status_tone,
                      readiness, validate_selection, explain_error)
from ui.theme import build_css
from ui.tokens import PALETTES

ROOT = Path(__file__).resolve().parent.parent


def _res(matches=100, inliers=50, ratio=0.5, cov=0.5, rmse=1.0, h=True, status=None, reasons=None):
    r = SimpleNamespace(tentative_matches=matches, inliers=inliers, inlier_ratio=ratio, coverage=cov, rmse_px=rmse,
                        homography=np.eye(3) if h else None, diagnostics={})
    g = gate(r)
    r.diagnostics = {"status": status or g["status"], "gate_reasons": g["reasons"] if reasons is None else reasons, "elapsed_s": 3.2}
    return r


def test_gate_reason_text_covers_every_engine_reason():
    # Drive each engine condition individually and make sure the UI has wording for it.
    cases = [_res(matches=7), _res(inliers=11), _res(ratio=0.34), _res(cov=0.34), _res(rmse=2.6), _res(rmse=None)]
    seen = set()
    for r in cases:
        seen.update(gate(r)["reasons"])
    assert seen == set(GATE_REASON_TEXT), seen ^ set(GATE_REASON_TEXT)


def test_gate_text_thresholds_match_engine_boundaries():
    assert gate(_res(matches=8, inliers=12, ratio=0.35, cov=0.35, rmse=2.5))["status"] == "VALIDATED"
    assert "too_few_inliers" in gate(_res(inliers=11))["reasons"]
    assert "8" in GATE_REASON_TEXT["too_few_tentative_matches"]
    assert "12" in GATE_REASON_TEXT["too_few_inliers"]
    assert "0.35" in GATE_REASON_TEXT["low_inlier_ratio"] and "35%" in GATE_REASON_TEXT["low_spatial_coverage"]
    assert "2.5" in GATE_REASON_TEXT["high_or_missing_rmse"]


def test_green_only_for_validated():
    assert gate_status_tone("VALIDATED")[0] == "ok"
    for s in ("INSUFFICIENT_EVIDENCE", "UNKNOWN", None, "COMPLETED", ""):
        assert gate_status_tone(s)[0] != "ok"
    assert gate_status_tone("INSUFFICIENT_EVIDENCE")[0] == "warn"


def test_claims_never_conflated():
    good = {c["q"]: c for c in evidence_claims(_res())}
    bad = {c["q"]: c for c in evidence_claims(_res(inliers=3, cov=0.1))}
    assert good["Evidence gate (configured thresholds)"]["tone"] == "ok"
    assert bad["Evidence gate (configured thresholds)"]["tone"] == "warn"
    # Completion and homography are never green; ground truth is never claimed.
    for claims in (good, bad):
        assert claims["Processing completed"]["tone"] != "ok"
        assert claims["Transformation estimated"]["tone"] != "ok"
        gt = claims["Independent ground-truth validation"]
        assert gt["tone"] == "mute" and gt["label"] == "Not established"
    nohom = {c["q"]: c for c in evidence_claims(_res(h=False, inliers=0, ratio=0, cov=0, rmse=None))}
    assert nohom["Transformation estimated"]["label"] == "Not estimated"


def test_formatters_handle_missing():
    assert fmt_num(None) == "—" and fmt_num(float("nan")) == "—" and fmt_int(None) == "—" and fmt_pct(None) == "—"
    assert fmt_num(1.23456, 2, "px") == "1.23 px" and fmt_int(12345) == "12,345" and fmt_pct(0.5) == "50.0%"


def test_validate_selection():
    ids = {"a": {"sensor": "OHRC", "gsd_m": 0.3}, "b": {"sensor": "TMC2", "gsd_m": 5.0},
           "c": {"sensor": "OHRC", "gsd_m": None}}
    assert validate_selection(ids, "a", "a")[0][0] == "bad"
    assert validate_selection(ids, "a", "b") == []
    tones = [t for t, _ in validate_selection(ids, "a", "c")]
    assert tones == ["warn", "warn"] and "bad" not in tones


def test_readiness_never_claims_validation():
    tone, label, note = readiness({"gsd_m": 5.0})
    assert tone == "info" and "validated" in note.lower() and "nothing" in note.lower()
    assert readiness({"gsd_m": None})[0] == "warn"


def test_explain_error():
    assert "file" in explain_error(FileNotFoundError("x"))[0].lower()
    assert "memory" in explain_error(MemoryError())[0].lower()
    assert explain_error(RuntimeError("boom"))[1]


def test_components_escape_dynamic_text():
    html = C.tile_html("<b>x</b>", "<script>1</script>", "n&n")
    assert "<script>" not in html and "&lt;script&gt;" in html
    row = {"product_id": "<img src=x onerror=1>", "shape": "(1, 2)", "dtype": "uint8", "gsd_m": 5.0}
    assert "<img" not in C.source_panel_html(row, "TMC2")
    assert "Not found" in C.source_panel_html(None, "IIRS")


def test_chips_carry_text_and_symbol_not_colour_only():
    for tone in ("ok", "warn", "bad", "info", "mute"):
        h = C.chip_html("Label", tone)
        assert "Label" in h and "aria-hidden" in h


def _lum(hexc):
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_palettes_have_same_keys_and_readable_contrast():
    assert PALETTES["dark"].keys() == PALETTES["light"].keys()
    for name, p in PALETTES.items():
        for fg in ("text", "muted", "accent", "accent_info", "ok", "warn", "bad", "ohrc", "tmc2", "iirs"):
            for bg in ("bg", "surface"):
                assert _contrast(p[fg], p[bg]) >= 4.5, (name, fg, bg, _contrast(p[fg], p[bg]))


def test_streamlit_config_matches_tokens():
    cfg = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    for mode in ("dark", "light"):
        t, p = cfg["theme"][mode], PALETTES[mode]
        assert t["backgroundColor"].lower() == p["bg"].lower()
        assert t["secondaryBackgroundColor"].lower() == p["surface"].lower()
        assert t["textColor"].lower() == p["text"].lower()
        assert t["primaryColor"].lower() == p["accent_info"].lower()


def test_css_has_both_themes_reduced_motion_and_no_stray_hex_in_components():
    for th in ("dark", "light"):
        css = build_css(th)
        assert "--cb-bg" in css and "prefers-reduced-motion" in css
    # Components must use tokens, not hard-coded colours.
    src = (ROOT / "ui" / "components.py").read_text()
    assert not re.search(r"#[0-9A-Fa-f]{6}\b", src)
