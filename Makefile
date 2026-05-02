PY := python3

.PHONY: all mpl figma thmx preview clean

all: mpl figma thmx

mpl:
	$(PY) -m ports.mpl.build

figma:
	$(PY) -m ports.figma.build

thmx:
	$(PY) -m ports.thmx.build

preview: mpl
	$(PY) preview.py

clean:
	rm -rf dist/
