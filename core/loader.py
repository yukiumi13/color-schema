"""Load tokens.yaml and fully resolve all ${...} references."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from core import resolvers

resolvers.register_all()

ROOT = Path(__file__).resolve().parent.parent
TOKENS_PATH = ROOT / "tokens.yaml"


def load(path: Path | str = TOKENS_PATH) -> dict[str, Any]:
    cfg = OmegaConf.load(str(path))
    # resolve=True evaluates ${...} interpolations eagerly.
    return OmegaConf.to_container(cfg, resolve=True)  # type: ignore[return-value]


if __name__ == "__main__":
    # Quick sanity print: dump the fully-resolved tokens.
    import json
    print(json.dumps(load(), indent=2, ensure_ascii=False))
