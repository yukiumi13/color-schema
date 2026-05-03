"""Emit paper.mplstyle — matplotlib rc file tuned for academic figures.

Design choices (so the chart visually belongs with the rest of the schema):
  * Series colors are the categorical palette from tokens.yaml (8 hues
    chosen for max hue-distance on small-N plots). series.s1 is the
    "primary" slot — assign it to your method / first condition.
  * Axes/grid/text pull from the neutral ramp via surface/text/line —
    no black, no new grays introduced here.
  * Grid drawn *under* data, barely visible (line.grid is the lightest
    slate stop, basically a hairline).
  * No top/right spines — cleaner, more common in recent ML papers.
  * Legend has no frame (matches the flat aesthetic of pipeline figs).

The header of the generated file lists every token family used, with
the family's `_meta.use` description, so anyone reading the .mplstyle
knows where each color came from.
"""

from __future__ import annotations

from pathlib import Path

from core.loader import load_with_meta

OUT = Path(__file__).resolve().parent.parent.parent / "dist" / "paper.mplstyle"

# Families read by this rc. Keep in sync with the f-string body below.
_FAMILIES_USED = ("surface", "text", "border", "line", "series", "font")


def _bare(h: str) -> str:
    """Matplotlib mplstyle treats '#' as a comment delimiter, so hex
    colors must be written without the leading '#'."""
    return h.lstrip("#")


def _doc_header(meta: dict) -> str:
    lines = [
        "# paper.mplstyle — generated from tokens.yaml",
        "# Load via:  plt.style.use('<path>/paper.mplstyle')",
        "#",
        "# Token families used by this rc:",
    ]
    for fam in _FAMILIES_USED:
        m = meta.get(fam) or {}
        use = m.get("use", "—")
        lines.append(f"#   {fam:<10s} — {use}")
    return "\n".join(lines)


def build() -> None:
    t_raw, meta = load_with_meta()
    # Strip '#' from every color string in the tree for mplstyle output.
    # Simpler than threading _bare() through every f-string below.
    def strip(d):
        return {k: (_bare(v) if isinstance(v, str) and v.startswith("#") else v)
                for k, v in d.items()}
    t = {k: (strip(v) if isinstance(v, dict) else v) for k, v in t_raw.items()}

    series_keys = [k for k in sorted(t["series"]) if k.startswith("s")]
    cycle = ", ".join(t["series"][k] for k in series_keys)

    rc = f"""{_doc_header(meta)}

# ---- Figure / background ------------------------------------------------
figure.facecolor      : {t['surface']['bg']}
figure.edgecolor      : {t['surface']['bg']}
figure.dpi            : 150
savefig.facecolor     : {t['surface']['bg']}
savefig.edgecolor     : {t['surface']['bg']}
savefig.dpi           : 300
savefig.bbox          : tight
savefig.pad_inches    : 0.02

# ---- Axes ---------------------------------------------------------------
axes.facecolor        : {t['surface']['bg']}
axes.edgecolor        : {t['line']['axis']}
axes.linewidth        : 0.8
axes.labelcolor       : {t['text']['primary']}
axes.labelsize        : {t['font']['size_base']}
axes.titlesize        : {t['font']['size_title']}
axes.titlecolor       : {t['text']['primary']}
axes.titlepad         : 6
axes.labelpad         : 4
axes.spines.top       : False
axes.spines.right     : False
axes.spines.left      : True
axes.spines.bottom    : True
axes.axisbelow        : True
axes.prop_cycle       : cycler('color', [{', '.join(repr(t['series'][k]) for k in series_keys)}])

# ---- Grid ---------------------------------------------------------------
axes.grid             : True
axes.grid.axis        : y
grid.color            : {t['line']['grid']}
grid.linestyle        : -
grid.linewidth        : 0.6
grid.alpha            : 1.0

# ---- Ticks --------------------------------------------------------------
xtick.color           : {t['text']['secondary']}
xtick.labelcolor      : {t['text']['secondary']}
xtick.labelsize       : {t['font']['size_small']}
xtick.direction       : out
xtick.major.size      : 3
xtick.major.width     : 0.8
xtick.minor.size      : 1.5
xtick.minor.width     : 0.6
ytick.color           : {t['text']['secondary']}
ytick.labelcolor      : {t['text']['secondary']}
ytick.labelsize       : {t['font']['size_small']}
ytick.direction       : out
ytick.major.size      : 3
ytick.major.width     : 0.8
ytick.minor.size      : 1.5
ytick.minor.width     : 0.6

# ---- Lines / markers ----------------------------------------------------
lines.linewidth       : 1.6
lines.markersize      : 4.5
lines.markeredgewidth : 0
patch.linewidth       : 0.6
patch.edgecolor       : {t['line']['axis']}

# ---- Legend -------------------------------------------------------------
legend.frameon        : False
legend.fontsize       : {t['font']['size_small']}
legend.labelcolor     : {t['text']['primary']}
legend.handlelength   : 1.6
legend.handletextpad  : 0.5
legend.columnspacing  : 1.2
legend.borderaxespad  : 0.4

# ---- Text / fonts -------------------------------------------------------
font.family           : sans-serif
font.sans-serif       : {t['font']['family']}
font.weight           : {t['font']['weight_body']}
font.size             : {t['font']['size_base']}
text.color            : {t['text']['primary']}
axes.titleweight      : {t['font']['weight_bold']}
axes.labelweight      : {t['font']['weight_body']}
mathtext.default      : regular

# ---- Error bars / bar plots --------------------------------------------
errorbar.capsize      : 2.5

# ---- Image / color maps -------------------------------------------------
image.cmap            : viridis

# ---- Figure layout ------------------------------------------------------
figure.figsize        : 3.5, 2.4
figure.autolayout     : False
figure.constrained_layout.use : True
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rc)
    print(f"wrote {OUT}  ({len(rc)} bytes, prop_cycle: {cycle})")


if __name__ == "__main__":
    build()
