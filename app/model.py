from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import numpy as np

@dataclass
class ArraySpec:
    path: Path
    shape: tuple[int, ...]
    dtype: np.dtype
    offset: int = 0
    interleave: str = "native"
    axis_names: tuple[str, ...] = ()
    order: str = "C"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SceneSpec:
    sensor: str
    product_id: str
    source: Path
    array: ArraySpec
    gsd_m: Optional[float] = None
    crs: Optional[str] = None
    transform: Any = None
    footprint: Any = None
    acquisition_start: Optional[str] = None
    acquisition_end: Optional[str] = None
    solar_elevation_deg: Optional[float] = None
    solar_azimuth_deg: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Tile:
    row0: int
    row1: int
    col0: int
    col1: int
    physical_bounds: tuple[float,float,float,float] | None = None
    id: str = ""

@dataclass
class MatchResult:
    method: str
    keypoints_ref: int
    keypoints_src: int
    tentative_matches: int
    inliers: int
    inlier_ratio: float
    rmse_px: float | None
    median_error_px: float | None
    p95_error_px: float | None
    coverage: float
    homography: Optional[np.ndarray]
    points_ref: np.ndarray = field(default_factory=lambda: np.empty((0,2),np.float32))
    points_src: np.ndarray = field(default_factory=lambda: np.empty((0,2),np.float32))
    diagnostics: dict[str, Any] = field(default_factory=dict)
