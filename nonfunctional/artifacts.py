from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import artifact_root


def write_json(name: str, payload: Any) -> Path:
    path = artifact_root() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
