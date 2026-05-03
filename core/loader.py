"""Load tokens.yaml, resolve all ${...} references, and split _meta out.

`_meta` blocks document each family's purpose (use / pairs_with / description)
but are NOT real tokens — they must be removed before passing to ports, or
exporters (figma, mpl) will try to emit them as colors and crash.

Two entry points:
  load()           -> cleaned tokens dict (no _meta), drop-in for all ports
  load_with_meta() -> (cleaned, meta_map) where meta_map is keyed by family path
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from core import resolvers

resolvers.register_all()

ROOT = Path(__file__).resolve().parent.parent
TOKENS_PATH = ROOT / "tokens.yaml"


def _strip_meta(node: Any, prefix: str = "") -> tuple[Any, dict[str, dict]]:
    """Recursively pull `_meta` blocks out of dicts.

    Returns (cleaned_node, meta_map). meta_map has keys like 'method',
    'method_soft', '' (top-level), with values being the _meta dict
    that lived at that location.
    """
    if not isinstance(node, dict):
        return node, {}
    cleaned: dict = {}
    meta_map: dict[str, dict] = {}
    for k, v in node.items():
        if k == "_meta":
            meta_map[prefix.rstrip(".")] = v
            continue
        sub_prefix = f"{prefix}{k}." if prefix else f"{k}."
        sub_cleaned, sub_meta = _strip_meta(v, sub_prefix)
        cleaned[k] = sub_cleaned
        meta_map.update(sub_meta)
    return cleaned, meta_map


def load(path: Path | str = TOKENS_PATH) -> dict[str, Any]:
    cfg = OmegaConf.load(str(path))
    raw = OmegaConf.to_container(cfg, resolve=True)
    cleaned, _ = _strip_meta(raw)  # type: ignore[arg-type]
    return cleaned  # type: ignore[return-value]


def load_with_meta(path: Path | str = TOKENS_PATH) -> tuple[dict[str, Any], dict[str, dict]]:
    cfg = OmegaConf.load(str(path))
    raw = OmegaConf.to_container(cfg, resolve=True)
    return _strip_meta(raw)  # type: ignore[arg-type,return-value]


def load_layers(
    paths: list[Path | str],
    *,
    with_meta: bool = False,
) -> dict[str, Any] | tuple[dict[str, Any], dict[str, dict]]:
    """Load and deep-merge multiple token files. Later overrides earlier.

    Use case: layer a preset (e.g. presets/m3-default.yaml from the M3
    importer) on top of the core tokens.yaml so that ports see a unified
    tree containing both.

    All ${...} references resolve against the merged tree, so a preset
    file that declares its own `ramp.m3_*` block can reference those
    primitives from its own semantic section.
    """
    cfgs = [OmegaConf.load(str(p)) for p in paths]
    merged = OmegaConf.merge(*cfgs)
    raw = OmegaConf.to_container(merged, resolve=True)
    cleaned, meta = _strip_meta(raw)  # type: ignore[arg-type]
    return (cleaned, meta) if with_meta else cleaned  # type: ignore[return-value]


if __name__ == "__main__":
    import json
    tokens, meta = load_with_meta()
    print("=== TOKENS ===")
    print(json.dumps(tokens, indent=2, ensure_ascii=False))
    print("\n=== META ===")
    print(json.dumps(meta, indent=2, ensure_ascii=False))
