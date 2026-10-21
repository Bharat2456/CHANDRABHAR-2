"""Durable workflow-state helpers (behaviour unchanged from the original dashboard)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def output_dir(root: Path) -> Path:
    return root.parent / "CHANDRABHAR-2_Platform_Outputs"


def workflow_state_path(root: Path) -> Path:
    return output_dir(root) / "workflow_state.json"


def load_workflow_state(root: Path) -> dict[str, Any]:
    p = workflow_state_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_workflow_state(root: Path, **updates) -> dict[str, Any]:
    p = workflow_state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = load_workflow_state(root)
    state.update(updates)
    p.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return state


def reset_workflow_state(root: Path, **state) -> dict[str, Any]:
    p = workflow_state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return state
