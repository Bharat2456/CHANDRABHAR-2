"""Common-grid correspondence evidence renderer (moved verbatim from the original dashboard.py).

The drawing logic and thresholds are unchanged. The saved PNG keeps its dark mission-black
canvas so exported evidence is identical regardless of the UI theme.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def evidence_image(result, out_path: Path, title: str) -> Path:
    """Create a truthful common-grid correspondence view from the returned points.

    The points are the actual correspondence coordinates used by the matcher. This is
    deliberately labelled as a common-grid evidence view, not a raw-image overlay.
    """
    pts_r = np.asarray(getattr(result, "points_ref", np.empty((0, 2))), dtype=np.float32)
    pts_s = np.asarray(getattr(result, "points_src", np.empty((0, 2))), dtype=np.float32)
    W, H = 760, 430
    gap, margin = 34, 24
    panel_w, panel_h = 340, 330
    canvas = np.zeros((H, W, 3), np.uint8)
    canvas[:] = (10, 7, 5)  # BGR for Mission Black-ish
    cv2.rectangle(canvas, (margin, 62), (margin + panel_w, 62 + panel_h), (63, 48, 38), 2)
    x2 = margin + panel_w + gap
    cv2.rectangle(canvas, (x2, 62), (x2 + panel_w, 62 + panel_h), (63, 48, 38), 2)
    cv2.putText(canvas, title[:78], (margin, 28), cv2.FONT_HERSHEY_SIMPLEX, .62, (250, 247, 245), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Reference common-grid", (margin + 12, 52), cv2.FONT_HERSHEY_SIMPLEX, .48, (22, 111, 249), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Source common-grid", (x2 + 12, 52), cv2.FONT_HERSHEY_SIMPLEX, .48, (22, 111, 249), 1, cv2.LINE_AA)

    if len(pts_r) == 0 or len(pts_s) == 0:
        cv2.putText(canvas, "No independent correspondence points returned", (95, 220), cv2.FONT_HERSHEY_SIMPLEX, .65, (190, 205, 220), 1, cv2.LINE_AA)
    else:
        allx = np.concatenate([pts_r[:, 0], pts_s[:, 0]])
        ally = np.concatenate([pts_r[:, 1], pts_s[:, 1]])
        xmin, xmax = float(np.min(allx)), float(np.max(allx))
        ymin, ymax = float(np.min(ally)), float(np.max(ally))
        sx = max(xmax - xmin, 1.0)
        sy = max(ymax - ymin, 1.0)

        def map_pt(p, ox):
            px = int(ox + 12 + (float(p[0]) - xmin) / sx * (panel_w - 24))
            py = int(62 + 12 + (float(p[1]) - ymin) / sy * (panel_h - 24))
            return px, py

        # Determine inliers from the same homography returned by the engine.
        inlier_mask = np.zeros(len(pts_r), dtype=bool)
        Hm = getattr(result, "homography", None)
        if Hm is not None and len(pts_r) >= 3:
            try:
                pred = cv2.perspectiveTransform(pts_s.reshape(-1, 1, 2), np.asarray(Hm, np.float64)).reshape(-1, 2)
                err = np.linalg.norm(pred - pts_r, axis=1)
                inlier_mask = err <= 3.0
            except Exception:
                pass

        # Draw up to 90 pairs so the figure remains legible.
        idx = np.arange(len(pts_r))
        if len(idx) > 90:
            idx = idx[np.linspace(0, len(idx) - 1, 90).astype(int)]
        for i in idx:
            pr = map_pt(pts_r[i], margin)
            ps = map_pt(pts_s[i], x2)
            if inlier_mask[i]:
                c = (8, 136, 19)  # BGR India Green
                cv2.line(canvas, pr, ps, c, 1, cv2.LINE_AA)
            else:
                c = (120, 135, 150)
            cv2.circle(canvas, pr, 3, c, -1, cv2.LINE_AA)
            cv2.circle(canvas, ps, 3, c, -1, cv2.LINE_AA)

    cv2.putText(canvas, f"Matches: {getattr(result,'tentative_matches',0)}", (margin, 410), cv2.FONT_HERSHEY_SIMPLEX, .48, (166, 148, 138), 1, cv2.LINE_AA)
    cv2.putText(canvas, f"Inliers: {getattr(result,'inliers',0)}", (margin + 135, 410), cv2.FONT_HERSHEY_SIMPLEX, .48, (8, 136, 19), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Green = RANSAC inliers", (x2 + 12, 410), cv2.FONT_HERSHEY_SIMPLEX, .45, (8, 136, 19), 1, cv2.LINE_AA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas)
    return out_path
