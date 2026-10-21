"""Design tokens for CHANDRABHAR-2 | LUNAR INTELLIGENCE INTERFACE.

Two complete palettes: ``dark`` (Orbital Night) and ``light`` (Lunar Daylight).
Keep .streamlit/config.toml native-theme colours in sync with ``bg``/``surface``/``text``/
``accent_info`` below. Semantic rules: green = gate passed only, red = error only.
"""
from __future__ import annotations

PALETTES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#07090D", "surface": "#0D1117", "surface2": "#131922", "border": "#26303F",
        "text": "#E8EDF4", "muted": "#98A3B5",
        "accent": "#F5A524", "accent_info": "#38B6E8",
        "ok": "#3FB950", "warn": "#E3B341", "bad": "#F85149", "mute": "#98A3B5",
        "ok_bg": "rgba(63,185,80,.14)", "warn_bg": "rgba(227,179,65,.14)",
        "bad_bg": "rgba(248,81,73,.14)", "info_bg": "rgba(56,182,232,.14)", "mute_bg": "rgba(152,163,181,.12)",
        "ohrc": "#F5A524", "tmc2": "#38B6E8", "iirs": "#6FD3B7",
        "shadow": "0 1px 0 rgba(255,255,255,.03) inset",
    },
    "light": {
        "bg": "#F4F1EA", "surface": "#FFFFFF", "surface2": "#EEEAE0", "border": "#D9D4C7",
        "text": "#14181F", "muted": "#5A6473",
        "accent": "#9A5000", "accent_info": "#1F4E8C",
        "ok": "#1A7F37", "warn": "#8A5A00", "bad": "#CF222E", "mute": "#5A6473",
        "ok_bg": "rgba(26,127,55,.10)", "warn_bg": "rgba(138,90,0,.10)",
        "bad_bg": "rgba(207,34,46,.09)", "info_bg": "rgba(31,78,140,.09)", "mute_bg": "rgba(90,100,115,.09)",
        "ohrc": "#9A5000", "tmc2": "#1F4E8C", "iirs": "#13795B",
        "shadow": "0 1px 2px rgba(20,24,31,.06)",
    },
}

SENSOR_KEYS = {"OHRC": "ohrc", "TMC2": "tmc2", "TMC": "tmc2", "IIRS": "iirs"}

FONT_SANS = '"Inter","Segoe UI",system-ui,-apple-system,sans-serif'
FONT_MONO = '"JetBrains Mono","Cascadia Mono","Consolas",monospace'


def palette(theme: str) -> dict[str, str]:
    return PALETTES["light" if str(theme).lower() == "light" else "dark"]
