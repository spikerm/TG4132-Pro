from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class MarkerState:
    enabled: bool = False
    frequency_mhz: float = 0.0


@dataclass
class SweepState:
    start_mhz: float = 140.0
    stop_mhz: float = 150.0
    rbw_khz: float = 30.0
    vbw_khz: float = 30.0
    sweep_ms: float = 250.0
    ref_level_dbm: float = 0.0
    attenuation_db: float = 0.0

    @property
    def span_mhz(self) -> float:
        return self.stop_mhz - self.start_mhz

    @property
    def center_mhz(self) -> float:
        return (self.start_mhz + self.stop_mhz) / 2.0


@dataclass
class TraceState:
    mode: str = "CLEAR/WRITE"
    memory_enabled: bool = False
    average_depth: int = 16


@dataclass
class GeneratorState:
    enabled: bool = True
    level_dbm: float = -10.0
    mode: str = "TRACK"
    cw_frequency_mhz: float = 145.0


@dataclass
class DisplayState:
    crt_persistence: float = 35.0
    crt_intensity: float = 80.0
    menu_visible: bool = True
    menu_rows: int = 12


@dataclass
class InstrumentState:
    screen: str = "SPECTRUM ANALYZER"
    selected_marker: int = 0
    delta_enabled: bool = True
    auto_track: bool = False
    data_source: str = "SIMULATOR"
    measurement_text: str = "READY"
    sweep: SweepState = field(default_factory=SweepState)
    trace: TraceState = field(default_factory=TraceState)
    generator: GeneratorState = field(default_factory=GeneratorState)
    display: DisplayState = field(default_factory=DisplayState)
    markers: List[MarkerState] = field(default_factory=lambda: [MarkerState() for _ in range(4)])
