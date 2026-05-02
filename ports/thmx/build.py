"""Emit paper.thmx — PowerPoint theme file.

.thmx is an Open Packaging Conventions (OPC) zip with:
  /[Content_Types].xml
  /_rels/.rels           -> points at the theme part
  /theme/theme1.xml      -> the theme definition (colors + fonts + fmtScheme)

Theme color slot mapping (PowerPoint gives users these 12 slots):
  dk1/lt1      text-on-background pair (dark text over light bg)
  dk2/lt2      secondary text-on-background pair
  accent1..6   the 6 user-facing "theme colors" shown in the color picker
  hlink        hyperlink color
  folHlink     followed hyperlink color

We map method.ours -> accent1 so "Ours" in PPT matches "Ours" in figures.
Accent order is tuned so the color picker's first 3 are already maximally
distinct (blue / vermilion / green).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from jinja2 import Template

from core.loader import load
from core.resolvers import darken

THIS = Path(__file__).resolve().parent
OUT = THIS.parent.parent / "dist" / "paper.thmx"


def _hex6(color: str) -> str:
    """#RRGGBB -> RRGGBB (uppercase, no hash) — OOXML srgbClr format."""
    return color.lstrip("#").upper()


def _render_theme_xml(t: dict) -> str:
    template = Template((THIS / "theme.xml.j2").read_text())
    return template.render(
        theme_name="Paper",
        # Text/background pairs
        dk1=_hex6(t["text"]["primary"]),
        lt1=_hex6(t["surface"]["bg"]),
        dk2=_hex6(t["text"]["secondary"]),
        lt2=_hex6(t["surface"]["subtle"]),
        # Accents — order chosen for maximal distinctness in the picker
        accent1=_hex6(t["method"]["ours"]),      # blue
        accent2=_hex6(t["method"]["highlight"]), # vermilion
        accent3=_hex6(t["method"]["success"]),   # green
        accent4=_hex6(t["method"]["warning"]),   # orange
        accent5=_hex6(t["series"]["s5"]),        # purple
        accent6=_hex6(t["series"]["s6"]),        # sky blue
        # Links
        hlink=_hex6(t["method"]["ours"]),
        folHlink=_hex6(darken(t["method"]["ours"], 0.12)),
        # Fonts — PowerPoint wants a single typeface name, not a fallback list.
        # If the user's Windows lacks Inter, PPT falls back to Calibri/Aptos.
        font_major=t["font"]["family_ppt"],
        font_minor=t["font"]["family_ppt"],
    )


CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Override PartName="/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>
"""

ROOT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>
"""


def build() -> None:
    t = load()
    theme_xml = _render_theme_xml(t)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        z.writestr("_rels/.rels", ROOT_RELS_XML)
        z.writestr("theme/theme1.xml", theme_xml)

    # Quick summary of what the picker will show:
    accents = [t["method"]["ours"], t["method"]["highlight"],
               t["method"]["success"], t["method"]["warning"],
               t["series"]["s5"], t["series"]["s6"]]
    print(f"wrote {OUT}")
    print(f"  accents 1-6: {' '.join(accents)}")


if __name__ == "__main__":
    build()
