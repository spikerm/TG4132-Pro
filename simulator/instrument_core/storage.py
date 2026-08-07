from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class StorageEngine:
    """Profile/trace persistence abstraction.

    Desktop uses JSON files; STM32 can later replace this backend with FatFS/SD
    while keeping the same engine-facing API.
    """

    def save_json(self, path: str | Path, payload: Dict[str, Any]) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return p

    def load_json(self, path: str | Path) -> Dict[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))
