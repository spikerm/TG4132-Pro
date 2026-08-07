from __future__ import annotations

from typing import List, Optional

from .state import InstrumentState


class TraceEngine:
    MODES = ("CLEAR/WRITE", "MAX HOLD", "MIN HOLD", "AVERAGE", "VIEW")

    def __init__(self, state: InstrumentState):
        self.state = state
        self._hold: Optional[List[float]] = None
        self._avg_count = 0
        self.memory_b: Optional[List[float]] = None

    def clear(self) -> None:
        self._hold = None
        self._avg_count = 0

    def set_mode(self, mode: str) -> None:
        mode = mode.upper()
        if mode not in self.MODES:
            raise ValueError(f"unsupported trace mode: {mode}")
        self.state.trace.mode = mode
        if mode != "VIEW":
            self.clear()

    def process(self, values: List[float]) -> List[float]:
        mode = self.state.trace.mode
        if mode == "CLEAR/WRITE":
            return list(values)
        if mode == "VIEW":
            return list(self._hold if self._hold is not None else values)
        if self._hold is None or len(self._hold) != len(values):
            self._hold = list(values)
            self._avg_count = 1
            return list(self._hold)
        if mode == "MAX HOLD":
            self._hold = [max(a, b) for a, b in zip(self._hold, values)]
        elif mode == "MIN HOLD":
            self._hold = [min(a, b) for a, b in zip(self._hold, values)]
        elif mode == "AVERAGE":
            self._avg_count = min(256, self._avg_count + 1)
            n = self._avg_count
            self._hold = [a + (b - a) / n for a, b in zip(self._hold, values)]
        return list(self._hold)

    def store_memory(self, values: List[float]) -> None:
        self.memory_b = list(values)
        self.state.trace.memory_enabled = True

    def clear_memory(self) -> None:
        self.memory_b = None
        self.state.trace.memory_enabled = False
