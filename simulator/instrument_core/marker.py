from __future__ import annotations

from typing import List, Tuple

from .state import InstrumentState


class MarkerEngine:
    def __init__(self, state: InstrumentState):
        self.state = state

    def select(self, index: int) -> None:
        self.state.selected_marker = max(0, min(3, int(index)))

    def enable(self, index: int, enabled: bool = True) -> None:
        self.state.markers[index].enabled = bool(enabled)

    def set_frequency(self, index: int, frequency_mhz: float) -> None:
        self.state.markers[index].frequency_mhz = float(frequency_mhz)
        self.state.markers[index].enabled = True

    def to_peak(self, frequencies: List[float], values: List[float], index: int | None = None) -> float:
        if not values:
            raise ValueError("empty trace")
        idx = max(range(len(values)), key=values.__getitem__)
        marker = self.state.selected_marker if index is None else index
        self.set_frequency(marker, frequencies[idx])
        return frequencies[idx]

    def to_notch(self, frequencies: List[float], values: List[float], index: int | None = None) -> float:
        if not values:
            raise ValueError("empty trace")
        idx = min(range(len(values)), key=values.__getitem__)
        marker = self.state.selected_marker if index is None else index
        self.set_frequency(marker, frequencies[idx])
        return frequencies[idx]

    def delta(self) -> Tuple[float, int, int] | None:
        active = [i for i, m in enumerate(self.state.markers) if m.enabled]
        if not self.state.delta_enabled or len(active) < 2:
            return None
        a, b = active[0], active[1]
        return self.state.markers[b].frequency_mhz - self.state.markers[a].frequency_mhz, a, b
