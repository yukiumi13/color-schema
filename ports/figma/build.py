"""Emit Tokens Studio JSON for Figma.

Format reference: https://docs.tokens.studio/manage-sets/json-schema
We emit a single set called "global"; each token has {value, type, description}.
This works with Tokens Studio on free Figma (imports as Styles) and on
Pro (imports as Variables).

`description` per token is sourced from the family-level `_meta.use` so
designers see the family's intent in the Figma inspector.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.loader import load_with_meta

OUT = Path(__file__).resolve().parent.parent.parent / "dist" / "tokens-figma.json"

# Groups whose leaf values are colors. Anything else (e.g. font) handled
# separately to avoid type-mismatch on import.
_COLOR_GROUPS = (
    "base", "ramp",
    "surface", "border", "text", "line",
    "status",
    "series",
)

# Groups whose values are lists of colors (sequential/diverging).
_COLOR_LIST_GROUPS = ("sequential", "diverging")


def _entry(value: str, description: str) -> dict:
    e = {"value": value, "type": "color"}
    if description:
        e["description"] = description
    return e


def _walk_colors(tokens: dict, meta: dict) -> dict:
    out: dict = {}
    for group in _COLOR_GROUPS:
        if group not in tokens:
            continue
        desc = (meta.get(group) or {}).get("use", "")
        out[group] = {
            name: _entry(value, desc)
            for name, value in tokens[group].items()
        }
    for group in _COLOR_LIST_GROUPS:
        if group not in tokens:
            continue
        desc = (meta.get(group) or {}).get("use", "")
        out[group] = {}
        for pname, stops in tokens[group].items():
            for i, hex_ in enumerate(stops):
                out[group][f"{pname}_{i}"] = _entry(hex_, desc)
    return out


def _walk_typography(tokens: dict) -> dict:
    f = tokens.get("font", {})
    return {
        "font": {
            "family":      {"value": f["family"],      "type": "fontFamilies"},
            "family_mono": {"value": f["family_mono"], "type": "fontFamilies"},
            "size_base":   {"value": f["size_base"],   "type": "fontSizes"},
            "size_small":  {"value": f["size_small"],  "type": "fontSizes"},
            "size_title":  {"value": f["size_title"],  "type": "fontSizes"},
        }
    }


def build() -> None:
    t, meta = load_with_meta()
    payload = {"global": {**_walk_colors(t, meta), **_walk_typography(t)}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    n_colors = sum(len(payload["global"][g]) for g in _COLOR_GROUPS if g in payload["global"])
    print(f"wrote {OUT}  ({n_colors} color tokens, with descriptions)")


if __name__ == "__main__":
    build()
