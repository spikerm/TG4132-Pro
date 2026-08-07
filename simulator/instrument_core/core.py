from __future__ import annotations

from dataclasses import asdict
from typing import Callable, Dict, List, Optional

from .calibration import CalibrationEngine
from .marker import MarkerEngine
from .measurement import MeasurementEngine
from .menu import MenuEngine
from .state import InstrumentState
from .storage import StorageEngine
from .sweep import SweepEngine, SweepFrame
from .trace import TraceEngine
from .usb import UsbEngine


class InstrumentCore:
    VERSION = "0.1.0"

    def __init__(self, state: InstrumentState | None = None, points: int = 700):
        self.state = state or InstrumentState()
        self.sweep = SweepEngine(self.state, points=points)
        self.trace = TraceEngine(self.state)
        self.markers = MarkerEngine(self.state)
        self.measurements = MeasurementEngine()
        self.menu = MenuEngine(rows=self.state.display.menu_rows)
        self.storage = StorageEngine()
        self.usb = UsbEngine()
        self.calibration = CalibrationEngine()
        self.last_raw: Optional[SweepFrame] = None
        self.last_trace: Optional[SweepFrame] = None

    def acquire(self, source: Callable[[float], float]) -> SweepFrame:
        raw = self.sweep.frame(source)
        shown = self.trace.process(raw.values)
        self.last_raw = raw
        self.last_trace = SweepFrame(list(raw.frequencies_mhz), shown)
        return self.last_trace

    def store_trace_b(self) -> None:
        if self.last_trace is None:
            raise RuntimeError("no trace available")
        self.trace.store_memory(self.last_trace.values)

    def marker_to_peak(self, marker: int | None = None) -> float:
        if self.last_trace is None:
            raise RuntimeError("no trace available")
        return self.markers.to_peak(self.last_trace.frequencies_mhz, self.last_trace.values, marker)

    def marker_to_notch(self, marker: int | None = None) -> float:
        if self.last_trace is None:
            raise RuntimeError("no trace available")
        return self.markers.to_notch(self.last_trace.frequencies_mhz, self.last_trace.values, marker)

    def bandwidth(self, marker: int | None = None, depth_db: float = 3.0, notch: bool = False):
        if self.last_trace is None:
            raise RuntimeError("no trace available")
        marker = self.state.selected_marker if marker is None else marker
        mf = self.state.markers[marker].frequency_mhz
        idx = min(range(len(self.last_trace.frequencies_mhz)), key=lambda i: abs(self.last_trace.frequencies_mhz[i] - mf))
        return self.measurements.bandwidth(self.last_trace.frequencies_mhz, self.last_trace.values, idx, depth_db=depth_db, notch=notch)

    def snapshot(self) -> Dict:
        return {
            "core_version": self.VERSION,
            "state": asdict(self.state),
            "usb": asdict(self.usb.status),
            "calibration": asdict(self.calibration.state),
        }
