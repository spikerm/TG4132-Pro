from __future__ import annotations

from instrument_core import InstrumentCore
from tr1604_sim_v722 import App as V722App, MENUS, G, BR, D, SM

FW = "6.0.0"
BUILD = "instrument-core-desktop-001"


class App(V722App):
    """TR1604-Pro Instrument Core desktop reference build.

    V7.2.2 remains the proven CRT/display backend. Measurement state and each
    raw sweep are mirrored into InstrumentCore, so new functionality can move
    engine-by-engine to the common core without destabilising the display.
    """

    def __init__(self):
        super().__init__()
        self.core = InstrumentCore(points=700)
        self.root.title("TR1604-Pro Instrument Core")
        self._sync_core_from_ui()

    def _sync_core_from_ui(self) -> None:
        c = self.core.state
        c.screen = self.s.screen
        c.selected_marker = self.s.selected
        c.delta_enabled = self.s.delta
        c.auto_track = self.s.auto_track
        c.data_source = self.usb_mode
        c.measurement_text = self.measurement_readout.removeprefix("MEAS ").strip() or "READY"

        c.sweep.start_mhz = self.s.start
        c.sweep.stop_mhz = self.s.stop
        c.sweep.rbw_khz = self.s.rbw
        c.sweep.vbw_khz = self.s.vbw
        c.sweep.sweep_ms = self.s.sweep
        c.sweep.ref_level_dbm = self.ref_level
        c.sweep.attenuation_db = self.attenuation

        c.trace.mode = self.trace_mode if self.trace_mode in self.core.trace.MODES else "CLEAR/WRITE"
        c.trace.memory_enabled = self.mem_on

        c.generator.enabled = self.s.tg
        c.generator.level_dbm = self.s.tgl
        c.generator.mode = self.tg_mode
        c.generator.cw_frequency_mhz = self.tg_cw_freq

        c.display.crt_persistence = self.crt_persistence
        c.display.crt_intensity = self.crt_intensity
        c.display.menu_visible = self.menu_visible
        c.display.menu_rows = 12

        for i, marker in enumerate(self.s.markers):
            c.markers[i].enabled = marker.enabled
            c.markers[i].frequency_mhz = marker.f

    def _sync_ui_from_core_markers(self) -> None:
        for i, marker in enumerate(self.core.state.markers):
            self.s.markers[i].enabled = marker.enabled
            self.s.markers[i].f = marker.frequency_mhz

    def draw_measure(self, w, h):
        self._sync_core_from_ui()
        # The common core now sees and processes every desktop sweep.
        self.core.acquire(self.raw_level)
        super().draw_measure(w, h)
        self.txt(80, h - 30, f"CORE {self.core.VERSION}   FW {FW}   {BUILD}", D, SM)

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]

        # First functions migrated to the common core.
        if item == "MARKER TO PEAK":
            self._sync_core_from_ui()
            self.core.acquire(self.raw_level)
            f = self.core.marker_to_peak()
            self._sync_ui_from_core_markers()
            self.measurement_readout = f"CORE PEAK {f:.6f} MHz"
            return

        if item == "MARKER TO NOTCH":
            self._sync_core_from_ui()
            self.core.acquire(self.raw_level)
            f = self.core.marker_to_notch()
            self._sync_ui_from_core_markers()
            self.measurement_readout = f"CORE NOTCH {f:.6f} MHz"
            return

        if item == "BANDWIDTH":
            self._sync_core_from_ui()
            self.core.acquire(self.raw_level)
            result = self.core.bandwidth(notch=self.s.screen == "DUPLEX FILTER TUNE")
            if result:
                self.measurement_readout = (
                    f"CORE BW {self._format_df(result['bw_mhz'])}  Q {result['q']:.1f}"
                )
            else:
                self.measurement_readout = "CORE BW NO CROSSINGS"
            return

        if item == "SERVICE INFORMATION":
            self._sync_core_from_ui()
            self.msg(
                "INSTRUMENT CORE",
                f"FW {FW}\nBUILD {BUILD}\nCORE {self.core.VERSION}\n"
                f"SCREEN {self.core.state.screen}\nTRACE {self.core.state.trace.mode}\n"
                f"SWEEP {self.core.state.sweep.start_mhz:.6f}-{self.core.state.sweep.stop_mhz:.6f} MHz\n"
                f"USB {self.core.usb.status.mode} / {self.core.usb.status.message}\n"
                f"CAL {'VALID' if self.core.calibration.state.valid else 'NOT COMPLETE'}",
            )
            return

        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nInstrument Core {self.core.VERSION}\n"
                "Sweep / Trace / Marker / Measurement Engines\n"
                "Menu / Storage / USB / Calibration Engines\n"
                "V7.2 CRT display backend",
            )
            return

        super().activate()
        self._sync_core_from_ui()


if __name__ == "__main__":
    App().run()
