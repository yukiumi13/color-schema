"""Expanded preview — shows the full palette so you can eyeball:
  (a) is the ramp coverage enough?
  (b) do the semantic roles feel right?
  (c) do categorical/sequential/diverging palettes harmonize?

Layout (2 rows × 4 cols = 8 panels):
  row 1: ramp swatch grid    | semantic swatches  | pipeline diagram  | bar plot
  row 2: series demo (lines) | multi-series bars  | sequential heatmap| diverging heatmap
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from core.loader import load
from ports.mpl.cmaps import register_all as register_cmaps

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "preview.png"

RAMP_HUES = ("slate", "blue", "orange", "emerald", "violet",
             "red", "amber", "cyan", "rose")
RAMP_SHADES = ("50", "100", "200", "300", "400",
               "500", "600", "700", "800", "900", "950")


# ---------- panel drawers ---------------------------------------------------

def draw_ramps(ax, t):
    ax.set_title("color ramp", loc="left", color=t["text"]["primary"])
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


def draw_semantics(ax, t):
    ax.set_title("semantic tokens", loc="left", color=t["text"]["primary"])
    ax.axis("off")
    roles = ["ours", "baseline", "highlight", "success",
             "warning", "danger", "info"]
    for i, role in enumerate(roles):
        y = len(roles) - 1 - i
        # solid swatch (method.*)
        ax.add_patch(patches.FancyBboxPatch(
            (0.05, y + 0.15), 0.22, 0.7,
            boxstyle="round,pad=0,rounding_size=0.06",
            facecolor=t["method"][role], edgecolor="none"))
        # soft swatch (method_soft.*)
        ax.add_patch(patches.FancyBboxPatch(
            (0.30, y + 0.15), 0.22, 0.7,
            boxstyle="round,pad=0,rounding_size=0.06",
            facecolor=t["method_soft"][role],
            edgecolor=t["method"][role], linewidth=1.0))
        # soft-200 swatch (method_soft_200.*)
        ax.add_patch(patches.FancyBboxPatch(
            (0.55, y + 0.15), 0.22, 0.7,
            boxstyle="round,pad=0,rounding_size=0.06",
            facecolor=t["method_soft_200"][role], edgecolor="none"))
        ax.text(0.82, y + 0.5, role, va="center",
                fontsize=8, color=t["text"]["primary"])
    ax.set_xlim(0, 1.3); ax.set_ylim(0, len(roles))


def draw_pipeline(ax, t):
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    ax.set_title("pipeline (PPT style)", loc="left", color=t["text"]["primary"])

    def box(x, y, w, h, fill, edge, label):
        ax.add_patch(patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=fill, edgecolor=edge, linewidth=1.2))
        ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                fontsize=9, color=t["text"]["primary"])

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color=t["line"]["arrow"],
                                    lw=1.0, shrinkA=2, shrinkB=2))

    box(0.3, 1.5, 1.8, 1.0, t["surface"]["subtle"],       t["border"]["subtle"], "Input")
    box(3.0, 2.3, 1.8, 1.0, t["method_soft"]["ours"],      t["method"]["ours"],      "Ours")
    box(3.0, 0.7, 1.8, 1.0, t["method_soft"]["baseline"],  t["method"]["baseline"],  "Baseline")
    box(5.7, 1.5, 1.8, 1.0, t["surface"]["subtle"],       t["border"]["subtle"], "Merge")
    box(8.2, 1.5, 1.5, 1.0, t["method_soft"]["highlight"], t["method"]["highlight"], "Result")
    arrow(2.1, 2.0, 3.0, 2.8); arrow(2.1, 2.0, 3.0, 1.2)
    arrow(4.8, 2.8, 5.7, 2.0); arrow(4.8, 1.2, 5.7, 2.0)
    arrow(7.5, 2.0, 8.2, 2.0)


def draw_bars(ax, t):
    methods = ["A", "B", "C", "D", "Ours"]
    vals = [0.58, 0.66, 0.71, 0.74, 0.83]
    colors = [t["method"]["baseline"]] * 4 + [t["method"]["ours"]]
    ax.bar(methods, vals, color=colors, edgecolor="none")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("accuracy")
    ax.set_title("bar plot", loc="left", color=t["text"]["primary"])
    ax.text(4, 0.83 + 0.02, "0.83", ha="center",
            color=t["method"]["ours"], fontsize=9, weight="bold")


def draw_lines(ax, t):
    x = np.linspace(0, 6, 100)
    labels = ["Ours", "Base A", "Base B", "Base C",
              "Base D", "Base E", "Base F", "Base G"]
    for i, lbl in enumerate(labels):
        phase = i * 0.18
        ax.plot(x, np.sin(x - phase) * (1 - 0.07 * i), label=lbl,
                linewidth=(2.0 if i == 0 else 1.3))
    ax.set_xlabel("epoch"); ax.set_ylabel("metric")
    ax.set_title("categorical series (8)", loc="left", color=t["text"]["primary"])
    ax.legend(ncol=2, loc="lower left", fontsize=7)


def draw_grouped_bars(ax, t):
    groups = ["Task 1", "Task 2", "Task 3", "Task 4"]
    x = np.arange(len(groups))
    width = 0.18
    series = ["Ours", "Base A", "Base B", "Base C"]
    data = [[0.82, 0.88, 0.76, 0.91],
            [0.70, 0.74, 0.68, 0.80],
            [0.66, 0.71, 0.64, 0.77],
            [0.62, 0.68, 0.60, 0.73]]
    colors = [t["series"][f"s{i+1}"] for i in range(4)]
    for i, (lbl, vals, c) in enumerate(zip(series, data, colors)):
        ax.bar(x + (i - 1.5) * width, vals, width, label=lbl, color=c)
    ax.set_xticks(x); ax.set_xticklabels(groups)
    ax.set_ylim(0, 1.0); ax.set_ylabel("accuracy")
    ax.set_title("grouped bars", loc="left", color=t["text"]["primary"])
    ax.legend(ncol=4, loc="upper center", fontsize=7,
              bbox_to_anchor=(0.5, -0.15))


def draw_sequential_heatmap(ax, t):
    rng = np.random.default_rng(1)
    data = rng.random((6, 10)) * 0.6 + np.linspace(0.1, 0.8, 10)[None, :]
    im = ax.imshow(data, cmap="paper.blue", aspect="auto")
    ax.set_title("sequential heatmap (paper.blue)", loc="left",
                 color=t["text"]["primary"])
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, shrink=0.8)


def draw_diverging_heatmap(ax, t):
    rng = np.random.default_rng(2)
    data = rng.standard_normal((6, 10))
    im = ax.imshow(data, cmap="paper.redblue", aspect="auto",
                   vmin=-2.5, vmax=2.5)
    ax.set_title("diverging heatmap (paper.redblue)", loc="left",
                 color=t["text"]["primary"])
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, shrink=0.8)


# ---------- main -----------------------------------------------------------

def main():
    t = load()
    plt.style.use(str(ROOT / "dist" / "paper.mplstyle"))
    register_cmaps()

    # Override the style's constrained_layout so our explicit spacing wins.
    with plt.rc_context({"figure.constrained_layout.use": False}):
        fig, axes = plt.subplots(2, 4, figsize=(18, 8.5),
                                 gridspec_kw={"hspace": 0.5, "wspace": 0.3,
                                              "top": 0.92, "bottom": 0.08,
                                              "left": 0.04, "right": 0.98})

    draw_ramps(axes[0, 0], t)
    draw_semantics(axes[0, 1], t)
    draw_pipeline(axes[0, 2], t)
    draw_bars(axes[0, 3], t)

    draw_lines(axes[1, 0], t)
    draw_grouped_bars(axes[1, 1], t)
    draw_sequential_heatmap(axes[1, 2], t)
    draw_diverging_heatmap(axes[1, 3], t)

    fig.suptitle("theme preview — Fluent-style ramps + semantic tokens",
                 fontsize=13, color=t["text"]["primary"], y=0.98)
    fig.savefig(OUT, dpi=180)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
