"""Register sequential/diverging colormaps with matplotlib.

Usage in user code:
    from ports.mpl.cmaps import register_all
    register_all()
    plt.imshow(data, cmap='paper.blue')           # sequential
    plt.imshow(delta, cmap='paper.redblue')       # diverging

Names are prefixed 'paper.' so they don't collide with matplotlib builtins.
"""

from __future__ import annotations

from matplotlib.colors import LinearSegmentedColormap

try:
    # matplotlib >= 3.9
    from matplotlib import colormaps as _cmap_registry

    def _register(cmap, name):
        _cmap_registry.register(cmap, name=name, force=True)
except ImportError:  # pragma: no cover
    from matplotlib.cm import register_cmap as _register_cmap

    def _register(cmap, name):
        _register_cmap(name=name, cmap=cmap)

from core.loader import load


def register_all() -> None:
    t = load()
    for name, stops in t.get("sequential", {}).items():
        cmap = LinearSegmentedColormap.from_list(f"paper.{name}", stops, N=256)
        _register(cmap, f"paper.{name}")
    for name, stops in t.get("diverging", {}).items():
        cmap = LinearSegmentedColormap.from_list(f"paper.{name}", stops, N=256)
        _register(cmap, f"paper.{name}")


if __name__ == "__main__":
    register_all()
    print("registered: paper.{blue, emerald, orange, slate, redblue, orangeblue, redgreen}")
