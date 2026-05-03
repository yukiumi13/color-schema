"""Import a Material 3 color scheme from a single seed hex.

Pipeline (matches the system diagram):
  seed hex
    -> HCT (Hue/Chroma/Tone) — perceptual color space
    -> 6 tonal palettes (primary / secondary / tertiary /
                         neutral / neutral-variant / error)
       (each with a fixed chroma; tone is sampled at 13 stops)
    -> 78 reference colors emitted as ramp.m3_<palette>_<tone>
    -> light + dark role pairings emitted as m3_light.* / m3_dark.*
       in lockstep (the pairing is what M3's "scheme" actually is)

The output is a self-contained YAML file. It can be:
  (a) merged into tokens.yaml by hand
  (b) loaded as an overlay via core.loader.load_layers([...])
  (c) used standalone (it has both ramp and semantic sections)

Usage:
    python -m importers.m3.build --seed "#6750A4" --out presets/m3-light.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from materialyoucolor.hct import Hct
    from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
except ImportError as e:
    raise SystemExit(
        "missing dependency: pip install materialyoucolor"
    ) from e


# Standard M3 tone stops (Material 3 spec — light/dark role mapping uses
# 10/20/30/40/80/90/95/99/100 with neutral also using 95).
M3_TONES = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100]

# Six tonal palettes per M3 scheme, in stable serialization order.
M3_PALETTES = (
    "primary",
    "secondary",
    "tertiary",
    "neutral",
    "neutral_variant",
    "error",
)

# Role -> (palette, tone) for the LIGHT scheme.
# Reference: https://m3.material.io/styles/color/the-color-system/color-roles
LIGHT_ROLES: list[tuple[str, str, int]] = [
    # (role,                      palette,           tone)
    ("primary",                   "primary",         40),
    ("on_primary",                "primary",         100),
    ("primary_container",         "primary",         90),
    ("on_primary_container",      "primary",         10),
    ("secondary",                 "secondary",       40),
    ("on_secondary",              "secondary",       100),
    ("secondary_container",       "secondary",       90),
    ("on_secondary_container",    "secondary",       10),
    ("tertiary",                  "tertiary",        40),
    ("on_tertiary",               "tertiary",        100),
    ("tertiary_container",        "tertiary",        90),
    ("on_tertiary_container",     "tertiary",        10),
    ("error",                     "error",           40),
    ("on_error",                  "error",           100),
    ("error_container",           "error",           90),
    ("on_error_container",        "error",           10),
    ("background",                "neutral",         99),
    ("on_background",             "neutral",         10),
    ("surface",                   "neutral",         99),
    ("on_surface",                "neutral",         10),
    ("surface_variant",           "neutral_variant", 90),
    ("on_surface_variant",        "neutral_variant", 30),
    ("outline",                   "neutral_variant", 50),
    ("outline_variant",           "neutral_variant", 80),
    ("inverse_surface",           "neutral",         20),
    ("inverse_on_surface",        "neutral",         95),
    ("inverse_primary",           "primary",         80),
]

# DARK scheme — every tone flipped relative to light (M3 spec).
DARK_ROLES: list[tuple[str, str, int]] = [
    ("primary",                   "primary",         80),
    ("on_primary",                "primary",         20),
    ("primary_container",         "primary",         30),
    ("on_primary_container",      "primary",         90),
    ("secondary",                 "secondary",       80),
    ("on_secondary",              "secondary",       20),
    ("secondary_container",       "secondary",       30),
    ("on_secondary_container",    "secondary",       90),
    ("tertiary",                  "tertiary",        80),
    ("on_tertiary",               "tertiary",        20),
    ("tertiary_container",        "tertiary",        30),
    ("on_tertiary_container",     "tertiary",        90),
    ("error",                     "error",           80),
    ("on_error",                  "error",           20),
    ("error_container",           "error",           30),
    ("on_error_container",        "error",           90),
    ("background",                "neutral",         10),
    ("on_background",             "neutral",         90),
    ("surface",                   "neutral",         10),
    ("on_surface",                "neutral",         90),
    ("surface_variant",           "neutral_variant", 30),
    ("on_surface_variant",        "neutral_variant", 80),
    ("outline",                   "neutral_variant", 60),
    ("outline_variant",           "neutral_variant", 30),
    ("inverse_surface",           "neutral",         90),
    ("inverse_on_surface",        "neutral",         20),
    ("inverse_primary",           "primary",         40),
]


def _hex_from_argb(argb: int) -> str:
    return f"#{argb & 0xFFFFFF:06X}"


def _seed_hex_to_argb(hex_str: str) -> int:
    h = hex_str.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"seed must be #RRGGBB, got {hex_str!r}")
    return 0xFF000000 | int(h, 16)


def build_palettes(seed_hex: str) -> dict[str, dict[int, str]]:
    """Returns {palette_name: {tone: hex}}, 6 palettes × 13 tones = 78 hex."""
    hct = Hct.from_int(_seed_hex_to_argb(seed_hex))
    scheme = SchemeTonalSpot(hct, False, 0.0)  # is_dark + contrast irrelevant for palettes

    palettes = {
        "primary":         scheme.primary_palette,
        "secondary":       scheme.secondary_palette,
        "tertiary":        scheme.tertiary_palette,
        "neutral":         scheme.neutral_palette,
        "neutral_variant": scheme.neutral_variant_palette,
        "error":           scheme.error_palette,
    }
    return {
        name: {tone: _hex_from_argb(p.tone(tone)) for tone in M3_TONES}
        for name, p in palettes.items()
    }


def render_yaml(seed_hex: str, palettes: dict[str, dict[int, str]]) -> str:
    """Format the full preset YAML — ramp section + light + dark schemes."""
    out: list[str] = []
    out.append(f"# Auto-generated by importers/m3/build.py")
    out.append(f"# Seed: {seed_hex.upper()}")
    out.append(f"# Scheme algorithm: SchemeTonalSpot (Material 3 default)")
    out.append(f"# Run again: python -m importers.m3.build --seed {seed_hex}")
    out.append("")

    # ---- Reference palette: ramp.m3_<palette>_<tone> --------------------
    out.append("# Reference palette: 6 tonal palettes × 13 tones = 78 colors.")
    out.append("# These are M3's 'reference' tier — primitives, not for direct use.")
    out.append("# Reference them via m3_light.* / m3_dark.* below.")
    out.append("ramp:")
    for pname in M3_PALETTES:
        for tone in M3_TONES:
            key = f"m3_{pname}_{tone}:"
            out.append(f"  {key:<26s} \"{palettes[pname][tone]}\"")
        out.append("")  # blank between palettes for readability

    # ---- Helper to emit a role block ------------------------------------
    def emit_scheme(name: str, label: str, roles, pair: str) -> None:
        out.append(f"# {label} — role pairs locked at generation time.")
        out.append(f"{name}:")
        out.append(f"  _meta:")
        out.append(f"    use: \"Material 3 {label.lower()} (seed {seed_hex.upper()})\"")
        out.append(f"    pairs_with: [{pair}]")
        out.append(f"    description: \"Each role auto-paired with its on-* counterpart by the importer; do not mix tones manually.\"")
        for role, pname, tone in roles:
            ref = f"${{ramp.m3_{pname}_{tone}}}"
            key = f"{role}:"
            out.append(f"  {key:<27s} \"{ref}\"")
        out.append("")

    emit_scheme("m3_light", "Light scheme", LIGHT_ROLES, "m3_dark")
    emit_scheme("m3_dark",  "Dark scheme",  DARK_ROLES,  "m3_light")

    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--seed", required=True, help="Seed hex, e.g. '#6750A4'")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output YAML path (e.g. presets/m3-light.yaml)")
    args = ap.parse_args()

    palettes = build_palettes(args.seed)
    yaml_text = render_yaml(args.seed, palettes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml_text)
    print(f"wrote {args.out}  (78 ramp tones, "
          f"{len(LIGHT_ROLES)} light roles, {len(DARK_ROLES)} dark roles)")


if __name__ == "__main__":
    main()
