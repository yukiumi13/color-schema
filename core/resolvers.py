"""Color-math resolvers registered with OmegaConf.

All functions take and return #RRGGBB hex strings. Derivation happens
in HLS space (stdlib colorsys) which is simple and good enough for the
small adjustments we do here (soft fills, border shades).
"""

from __future__ import annotations

import colorsys
import re
from typing import Tuple

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


def _to_rgb(hex_str: str) -> Tuple[float, float, float]:
    m = _HEX_RE.match(hex_str.strip())
    if not m:
        raise ValueError(f"not a #RRGGBB color: {hex_str!r}")
    h = m.group(1)
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def _to_hex(rgb: Tuple[float, float, float]) -> str:
    r, g, b = (max(0.0, min(1.0, c)) for c in rgb)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def mix(a: str, b: str, t: str | float) -> str:
    """Linear RGB mix; t=0 returns a, t=1 returns b."""
    t = float(t)
    ra, ga, ba = _to_rgb(a)
    rb, gb, bb = _to_rgb(b)
    return _to_hex((ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t))


def darken(hex_str: str, amount: str | float) -> str:
    """Reduce lightness in HLS space. amount in [0,1]."""
    amt = float(amount)
    r, g, b = _to_rgb(hex_str)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, l - amt)
    return _to_hex(colorsys.hls_to_rgb(h, l, s))


def lighten(hex_str: str, amount: str | float) -> str:
    amt = float(amount)
    r, g, b = _to_rgb(hex_str)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(1.0, l + amt)
    return _to_hex(colorsys.hls_to_rgb(h, l, s))


def desaturate(hex_str: str, amount: str | float) -> str:
    amt = float(amount)
    r, g, b = _to_rgb(hex_str)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    s = max(0.0, s - amt)
    return _to_hex(colorsys.hls_to_rgb(h, l, s))


def alpha_over(fg: str, bg: str, a: str | float) -> str:
    """Flatten fg @ alpha onto bg — useful for exporting to tools that
    don't support alpha (PPT theme colors, some matplotlib contexts)."""
    return mix(bg, fg, float(a))


def register_all() -> None:
    """Call once at import time of loader.py."""
    from omegaconf import OmegaConf

    for name, fn in {
        "mix": _mix_resolver,
        "darken": _single_amount_resolver(darken),
        "lighten": _single_amount_resolver(lighten),
        "desaturate": _single_amount_resolver(desaturate),
        "alpha": _alpha_resolver,
    }.items():
        # replace=True so re-import in interactive sessions doesn't error
        OmegaConf.register_new_resolver(name, fn, replace=True)


def _mix_resolver(a: str, b: str, t: str) -> str:
    return mix(a, b, t)


def _single_amount_resolver(fn):
    def inner(color: str, amount: str) -> str:
        return fn(color, amount)
    return inner


def _alpha_resolver(fg: str, bg: str, a: str) -> str:
    return alpha_over(fg, bg, a)
