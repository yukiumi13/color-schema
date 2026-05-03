"""Family-card preview — schema as a visual config card stack.

Layout (top → bottom):
  1. Title strip
  2. Primitive layer    : full ramp grid (9 hues × 11 shades)
  3. Semantic layer     : 8 family cards (surface/text/border/line +
                                          method/method_soft/sequential/diverging)
                          each card shows: name | use | pairs_with | swatches
  4. Live usage examples: 4 demo charts proving the schema works in real plots
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from core.loader import load_with_meta
from ports.mpl.cmaps import register_all as register_cmaps

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "preview.png"

RAMP_HUES = ("slate", "blue", "orange", "emerald", "violet",
             "red", "amber", "cyan", "rose")
RAMP_SHADES = ("50", "100", "200", "300", "400",
               "500", "600", "700", "800", "900", "950")


# ---------- card primitive --------------------------------------------------

def draw_family_card(ax, family_name: str, family_data: dict,
                     meta: dict, t: dict) -> None:
    """One configurable card showing: family name + use + pairs_with + swatches.

    Handles both scalar families (method.ours = "#hex") and list families
    (sequential.blue = ["#hex", ...]).
    """
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # ---- Header band (subtle bg) -----------------------------------------
    ax.add_patch(patches.Rectangle(
        (0, 0.86), 1, 0.14,
        facecolor=t["surface"]["subtle"], edgecolor="none",
        transform=ax.transAxes))
    ax.text(0.04, 0.93, family_name,
            fontsize=10, fontweight="bold",
            color=t["text"]["primary"], va="center",
            transform=ax.transAxes)

    # ---- Use one-liner ---------------------------------------------------
    use = meta.get("use", "—") if meta else "—"
    ax.text(0.04, 0.79, use, fontsize=7,
            color=t["text"]["secondary"], va="center",
            transform=ax.transAxes)

    # ---- pairs_with tags -------------------------------------------------
    pairs = (meta.get("pairs_with") or []) if meta else []
    if pairs:
        tag_str = "+ " + "  ".join(pairs)
        ax.text(0.04, 0.72, tag_str, fontsize=6,
                color=t["text"]["muted"], va="center", style="italic",
                transform=ax.transAxes)

    # ---- Swatches --------------------------------------------------------
    items = list(family_data.items())
    n = len(items)
    if n == 0:
        return

    body_top = 0.66
    body_bottom = 0.04
    row_h = (body_top - body_bottom) / n
    sw_pad = row_h * 0.15

    for i, (key, value) in enumerate(items):
        y_top = body_top - i * row_h
        y_bot = y_top - row_h + sw_pad

        if isinstance(value, str) and value.startswith("#"):
            # Scalar swatch row: [color block][name][hex]
            ax.add_patch(patches.Rectangle(
                (0.04, y_bot), 0.18, row_h - sw_pad,
                facecolor=value, edgecolor="none",
                transform=ax.transAxes))
            ax.text(0.26, y_bot + (row_h - sw_pad) / 2, key,
                    fontsize=7, color=t["text"]["primary"],
                    va="center", transform=ax.transAxes)
            ax.text(0.96, y_bot + (row_h - sw_pad) / 2, value.upper(),
                    fontsize=6, family="monospace",
                    color=t["text"]["muted"],
                    va="center", ha="right", transform=ax.transAxes)

        elif isinstance(value, list):
            # Gradient row: [name][gradient strip across N stops]
            ax.text(0.04, y_bot + (row_h - sw_pad) / 2, key,
                    fontsize=7, color=t["text"]["primary"],
                    va="center", transform=ax.transAxes)
            n_stops = len(value)
            grad_x0, grad_x1 = 0.30, 0.96
            grad_w = (grad_x1 - grad_x0) / n_stops
            for j, stop in enumerate(value):
                ax.add_patch(patches.Rectangle(
                    (grad_x0 + j * grad_w, y_bot),
                    grad_w, row_h - sw_pad,
                    facecolor=stop, edgecolor="none",
                    transform=ax.transAxes))


# ---------- ramp grid -------------------------------------------------------

def draw_ramps(ax, t):
    ax.set_title("primitive layer · 9 hues × 11 shades",
                 loc="left", fontsize=10, fontweight="bold",
                 color=t["text"]["primary"], pad=8)
    ax.set_xlim(0, len(RAMP_SHADES))
    ax.set_ylim(0, len(RAMP_HUES))
    ax.invert_yaxis()
    ax.set_xticks([i + 0.5 for i in range(len(RAMP_SHADES))])
    ax.set_xticklabels(RAMP_SHADES, fontsize=6, color=t["text"]["secondary"])
    ax.set_yticks([i + 0.5 for i in range(len(RAMP_HUES))])
    ax.set_yticklabels(RAMP_HUES, fontsize=7, color=t["text"]["secondary"])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)

    for y, hue in enumerate(RAMP_HUES):
        for x, shade in enumerate(RAMP_SHADES):
            key = f"{hue}_{shade}"
            if key not in t["ramp"]:
                continue
            ax.add_patch(patches.Rectangle(
                (x + 0.05, y + 0.05), 0.9, 0.9,
                facecolor=t["ramp"][key], edgecolor="none"))


# ---------- live usage demos ------------------------------------------------

def draw_pipeline(ax, t):
    """Demonstrates how to assign roles at the consumer site.

    Schema doesn't pre-bind colors to "ours/baseline/highlight" —
    instead the user picks: series.s1 for the primary condition, a
    neutral slate stop for baseline, series.s2 for the standout.
    Soft fills are pulled from the same hue's _50 / _100 ramp shade.
    """
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    ax.set_title("usage · pipeline (roles assigned at use site)",
                 loc="left", fontsize=9,
                 color=t["text"]["primary"], pad=6)

    # Project-local role mapping — illustrative, not in tokens.yaml.
    primary      = t["series"]["s1"];   primary_soft   = t["ramp"]["blue_50"]
    neutral      = t["ramp"]["slate_400"]; neutral_soft = t["ramp"]["slate_100"]
    standout     = t["series"]["s2"];   standout_soft  = t["ramp"]["orange_50"]

    def box(x, y, w, h, fill, edge, label):
        ax.add_patch(patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=fill, edgecolor=edge, linewidth=1.2))
        ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                fontsize=8, color=t["text"]["primary"])

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color=t["line"]["arrow"],
                                    lw=1.0, shrinkA=2, shrinkB=2))

    box(0.3, 1.5, 1.8, 1.0, t["surface"]["subtle"], t["border"]["subtle"], "Input")
    box(3.0, 2.3, 1.8, 1.0, primary_soft,  primary,  "Ours")
    box(3.0, 0.7, 1.8, 1.0, neutral_soft,  neutral,  "Baseline")
    box(5.7, 1.5, 1.8, 1.0, t["surface"]["subtle"], t["border"]["subtle"], "Merge")
    box(8.2, 1.5, 1.5, 1.0, standout_soft, standout, "Result")
    arrow(2.1, 2.0, 3.0, 2.8); arrow(2.1, 2.0, 3.0, 1.2)
    arrow(4.8, 2.8, 5.7, 2.0); arrow(4.8, 1.2, 5.7, 2.0)
    arrow(7.5, 2.0, 8.2, 2.0)


def draw_lines(ax, t):
    x = np.linspace(0, 6, 100)
    labels = ["Ours", "Base A", "Base B", "Base C",
              "Base D", "Base E", "Base F", "Base G"]
    for i, lbl in enumerate(labels):
        phase = i * 0.18
        ax.plot(x, np.sin(x - phase) * (1 - 0.07 * i), label=lbl,
                linewidth=(2.0 if i == 0 else 1.3))
    ax.set_xlabel("epoch"); ax.set_ylabel("metric")
    ax.set_title("usage · series (8-way categorical)", loc="left",
                 fontsize=9, color=t["text"]["primary"], pad=6)
    ax.legend(ncol=2, loc="lower left", fontsize=6)


def draw_sequential_heatmap(ax, t):
    rng = np.random.default_rng(1)
    data = rng.random((6, 10)) * 0.6 + np.linspace(0.1, 0.8, 10)[None, :]
    im = ax.imshow(data, cmap="paper.blue", aspect="auto")
    ax.set_title("usage · sequential heatmap", loc="left",
                 fontsize=9, color=t["text"]["primary"], pad=6)
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, shrink=0.8)


def draw_diverging_heatmap(ax, t):
    rng = np.random.default_rng(2)
    data = rng.standard_normal((6, 10))
    im = ax.imshow(data, cmap="paper.redblue", aspect="auto",
                   vmin=-2.5, vmax=2.5)
    ax.set_title("usage · diverging heatmap", loc="left",
                 fontsize=9, color=t["text"]["primary"], pad=6)
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, shrink=0.8)


# ---------- main -----------------------------------------------------------

# Cards to render and which family in `tokens` they pull from.
CARDS = [
    ("surface",         "surface"),
    ("text",            "text"),
    ("border",          "border"),
    ("line",            "line"),
    ("status",          "status"),
    ("series",          "series"),
    ("sequential",      "sequential"),
    ("diverging",       "diverging"),
]


def main():
    t, meta = load_with_meta()
    plt.style.use(str(ROOT / "dist" / "paper.mplstyle"))
    register_cmaps()

    # The mplstyle enables constrained_layout, which fights with our explicit
    # gridspec margins; disable for this figure only.
    with plt.rc_context({"figure.constrained_layout.use": False}):
        fig = plt.figure(figsize=(16, 14))
        fig.patch.set_facecolor(t["surface"]["bg"])

        gs = fig.add_gridspec(
            nrows=4, ncols=4,
            height_ratios=[1.2, 2.4, 2.4, 2.2],
            hspace=0.32, wspace=0.18,
            top=0.94, bottom=0.05, left=0.04, right=0.97,
        )

        # Row 0: full-width ramp grid
        ax_ramp = fig.add_subplot(gs[0, :])
        draw_ramps(ax_ramp, t)

        # Rows 1-2: 8 family cards
        for idx, (label, family_key) in enumerate(CARDS):
            row = 1 + idx // 4
            col = idx % 4
            ax = fig.add_subplot(gs[row, col])
            draw_family_card(ax, label, t.get(family_key, {}),
                             meta.get(family_key, {}), t)

        # Row 3: live usage demos
        draw_pipeline(fig.add_subplot(gs[3, 0]), t)
        draw_lines(fig.add_subplot(gs[3, 1]), t)
        draw_sequential_heatmap(fig.add_subplot(gs[3, 2]), t)
        draw_diverging_heatmap(fig.add_subplot(gs[3, 3]), t)

        fig.suptitle("color schema preview · primitive · semantic cards · live usage",
                     fontsize=14, fontweight="bold",
                     color=t["text"]["primary"], y=0.985)

        fig.savefig(OUT, dpi=180, facecolor=t["surface"]["bg"])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
