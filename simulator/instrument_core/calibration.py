from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CalibrationState:
    valid: bool = False
    open_done: bool = False
    short_done: bool = False
    load_done: bool = False
    rf_reference_db: float = 0.0
    notes: Dict[str, float] = field(default_factory=dict)


class CalibrationEngine:
    def __init__(self):
        self.state = CalibrationState()

    def reset(self) -> None:
        self.state = CalibrationState()

    def capture_open(self) -> None:
        self.state.open_done = True
        self._update_valid()

    def capture_short(self) -> None:
        self.state.short_done = True
        self._update_valid()

    def capture_load(self) -> None:
        self.state.load_done = True
        self._update_valid()

    def set_rf_reference(self, level_db: float) -> None:
        self.state.rf_reference_db = float(level_db)

    def _update_valid(self) -> None:
        self.state.valid = self.state.open_done and self.state.short_done and self.state.load_done
