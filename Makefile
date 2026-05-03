PY := python3

# Default M3 seed (Material 3 reference purple). Override on the CLI:
#   make m3 SEED=0061A4
# (No leading '#' — Make treats it as a comment delimiter.)
SEED ?= 6750A4

.PHONY: all mpl figma thmx preview m3 clean

all: mpl figma thmx

mpl:
	$(PY) -m ports.mpl.build

figma:
	$(PY) -m ports.figma.build

thmx:
	$(PY) -m ports.thmx.build

preview: mpl
	$(PY) preview.py

# Importer: turn a single seed hex into a full M3 reference palette +
# light/dark role mappings. Output is a self-contained YAML preset that
# can be layered on top of tokens.yaml via core.loader.load_layers().
m3:
	$(PY) -m importers.m3.build --seed "#$(SEED)" --out presets/m3-default.yaml

clean:
	rm -rf dist/
