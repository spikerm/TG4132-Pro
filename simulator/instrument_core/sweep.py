from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .state import InstrumentState


@dataclass
class SweepFrame:
    frequencies_mhz: List[float]
    values: List[float]


class SweepEngine:
    def __init__(self, state: InstrumentState, points: int = 700):
        self.state = state
        self.points = max(32, int(points))

    def frequencies(self) -> List[float]:
        s = self.state.sweep
        if self.points <= 1:
            return [s.start_mhz]
        return [s.start_mhz + s.span_mhz * i / (self.points - 1) for i in range(self.points)]

    def frame(self, source) -> SweepFrame:
        freqs = self.frequencies()
        return SweepFrame(freqs, [float(source(f)) for f in freqs])

    def set_center_span(self, center_mhz: float, span_mhz: float) -> None:
        span_mhz = max(0.000001, float(span_mhz))
        self.state.sweep.start_mhz = float(center_mhz) - span_mhz / 2.0
        self.state.sweep.stop_mhz = float(center_mhz) + span_mhz / 2.0

    def set_start_stop(self, start_mhz: float, stop_mhz: float) -> None:
        if stop_mhz <= start_mhz:
            raise ValueError("stop must be greater than start")
        self.state.sweep.start_mhz = float(start_mhz)
        self.state.sweep.stop_mhz = float(stop_mhz)
