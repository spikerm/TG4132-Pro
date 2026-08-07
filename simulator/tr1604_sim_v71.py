from __future__ import annotations

import math
from collections import defaultdict

from tr1604_sim_v7 import App as V7App, MENUS, G, BR, D, Y, C, SM

FW = "5.1.0"
BUILD = "desktop-v7.1-001"


def _insert_after(screen: str, after: str, items: list[str]):
    menu = MENUS[screen]
    pos = menu.index(after) + 1 if after in menu else len(menu)
    for item in reversed(items):
        if item not in menu:
            menu.insert(pos, item)


_insert_after("SPECTRUM ANALYZER", "MARKER TO PEAK", ["NEXT PEAK", "PEAK LEFT", "PEAK RIGHT"])
_insert_after("SPECTRUM ANALYZER", "VBW", ["TRACE MODE", "CLEAR TRACE", "BANDWIDTH", "Q FACTOR"])
_insert_after("DUPLEX FILTER TUNE", "VBW", ["TRACE MODE", "CLEAR TRACE", "BANDWIDTH", "Q FACTOR", "RIPPLE", "NOTCH DEPTH"])
_insert_after("MEMORY / TRACE COMPARE", "VBW", ["TRACE MODE", "CLEAR TRACE"])
_insert_after("ANTENNA ANALYZER", "VBW", ["TRACE MODE", "CLEAR TRACE", "MIN SWR READOUT"])
_insert_after("INSERTION LOSS", "VBW", ["TRACE MODE", "CLEAR TRACE", "RIPPLE"])

for _screen in ("SPECTRUM ANALYZER", "DUPLEX FILTER TUNE", "INSERTION LOSS"):
    _insert_after(_screen, "TG LEVEL", ["TG MODE", "TG CW FREQUENCY"])

_insert_after("SYSTEM SETUP", "DISPLAY INTENSITY", ["CRT PERSISTENCE", "USB MODE", "USB STATUS"])


class App(V7App):
    """V7.1 reference measurement firmware.

    This build adds a real trace processor, peak-search family, persistent
    measurement readouts, TG track/CW state and USB-ready desktop state while
    keeping the V7 CRT renderer and controls.
    """

    TRACE_MODES = ("CLEAR/WRITE", "MAX HOLD", "MIN HOLD", "AVERAGE")

    def __init__(self):
        self.trace_mode = "CLEAR/WRITE"
        self.trace_hold: dict[tuple[str, int], float] = {}
        self.trace_avg_count: defaultdict[tuple[str, int], int] = defaultdict(int)
        self.measurement_readout = "MEAS READY"
        self.crt_persistence = 35.0
        self.crt_intensity = 80.0
        self.tg_mode = "TRACK"
        self.tg_cw_freq = 145.000000
        self.usb_mode = "SIMULATOR"
        self.usb_status = "LOCAL DATA"
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V7.1")

    # ------------------------------------------------------------------
    # Trace engine
    # ------------------------------------------------------------------
    def raw_level(self, f: float) -> float:
        return super().level(f)

    def level(self, f: float) -> float:
        value = self.raw_level(f)
        if self.trace_mode == "CLEAR/WRITE":
            return value

        # Quantise by current sweep so the hold bins follow the displayed trace.
        if self.s.span <= 0:
            return value
        idx = int(round((f - self.s.start) / self.s.span * 699.0))
        idx = max(0, min(699, idx))
        key = (self.s.screen, idx)

        if key not in self.trace_hold:
            self.trace_hold[key] = value
            self.trace_avg_count[key] = 1
            return value

        old = self.trace_hold[key]
        if self.trace_mode == "MAX HOLD":
            new = max(old, value)
        elif self.trace_mode == "MIN HOLD":
            new = min(old, value)
        else:  # AVERAGE
            n = min(64, self.trace_avg_count[key] + 1)
            new = old + (value - old) / n
            self.trace_avg_count[key] = n
        self.trace_hold[key] = new
        return new

    def clear_trace_engine(self):
        self.trace_hold.clear()
        self.trace_avg_count.clear()
        self.s.status = "TRACE ENGINE CLEARED"
        self.measurement_readout = "TRACE CLEARED"

    # ------------------------------------------------------------------
    # Peak / measurement helpers
    # ------------------------------------------------------------------
    def _samples(self, count: int = 1601):
        if self.s.span <= 0:
            return []
        return [
            (self.s.start + self.s.span * i / (count - 1), self.raw_level(self.s.start + self.s.span * i / (count - 1)))
            for i in range(count)
        ]

    def _peaks(self):
        data = self._samples()
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i][1] >= data[i - 1][1] and data[i][1] > data[i + 1][1]:
                peaks.append(data[i])
        peaks.sort(key=lambda p: p[1], reverse=True)
        return peaks

    def _select_peak(self, direction: str):
        peaks = self._peaks()
        if not peaks:
            self.measurement_readout = "PEAK SEARCH: NO PEAK"
            return
        current = self.s.markers[self.s.selected].f
        if direction == "NEXT":
            target = peaks[0]
            if abs(target[0] - current) < self.s.span / 200 and len(peaks) > 1:
                target = peaks[1]
        elif direction == "LEFT":
            left = [p for p in peaks if p[0] < current - self.s.span / 2000]
            target = max(left, key=lambda p: p[0]) if left else peaks[0]
        else:
            right = [p for p in peaks if p[0] > current + self.s.span / 2000]
            target = min(right, key=lambda p: p[0]) if right else peaks[0]
        m = self.s.markers[self.s.selected]
        m.enabled = True
        m.f = target[0]
        self.measurement_readout = f"PEAK {target[0]:.6f} MHz  {target[1]:.2f} dBm"

    @staticmethod
    def _crossing(data, start_idx, step, threshold):
        i = start_idx
        while 0 <= i + step < len(data):
            a = data[i]
            b = data[i + step]
            if (a[1] - threshold) * (b[1] - threshold) <= 0:
                if b[1] == a[1]:
                    return b[0]
                frac = (threshold - a[1]) / (b[1] - a[1])
                return a[0] + frac * (b[0] - a[0])
            i += step
        return None

    def _bandwidth_measurement(self):
        data = self._samples(2401)
        if not data:
            return None
        m = self.s.markers[self.s.selected]
        center_idx = min(range(len(data)), key=lambda i: abs(data[i][0] - m.f))

        if self.s.screen in ("DUPLEX FILTER TUNE", "NOTCH ZOOM"):
            # For a notch use +3 dB from the local minimum.
            lo = max(0, center_idx - len(data) // 5)
            hi = min(len(data), center_idx + len(data) // 5)
            center_idx = min(range(lo, hi), key=lambda i: data[i][1])
            threshold = data[center_idx][1] + 3.0
        else:
            lo = max(0, center_idx - len(data) // 5)
            hi = min(len(data), center_idx + len(data) // 5)
            center_idx = max(range(lo, hi), key=lambda i: data[i][1])
            threshold = data[center_idx][1] - 3.0

        left = self._crossing(data, center_idx, -1, threshold)
        right = self._crossing(data, center_idx, +1, threshold)
        if left is None or right is None or right <= left:
            return None
        return data[center_idx][0], right - left, data[center_idx][1], threshold

    def _show_bandwidth(self, q_only=False):
        result = self._bandwidth_measurement()
        if result is None:
            self.measurement_readout = "BW: NO VALID -3 dB CROSSINGS"
            return
        f0, bw, level, threshold = result
        q = f0 / bw if bw > 0 else math.inf
        if q_only:
            self.measurement_readout = f"Q {q:.1f}   F0 {f0:.6f} MHz   BW {self._format_df(bw)}"
        else:
            self.measurement_readout = f"BW {self._format_df(bw)}   F0 {f0:.6f} MHz   Q {q:.1f}"

    def _show_ripple(self):
        data = self._samples()
        vals = [v for _, v in data if v > -35.0]
        if len(vals) < 5:
            vals = [v for _, v in data]
        ripple = max(vals) - min(vals) if vals else 0.0
        self.measurement_readout = f"RIPPLE {ripple:.2f} dB"

    def _show_notch_depth(self):
        data = self._samples()
        if not data:
            return
        ordered = sorted(v for _, v in data)
        baseline = sum(ordered[int(len(ordered) * 0.75):]) / max(1, len(ordered) - int(len(ordered) * 0.75))
        notch = min(data, key=lambda p: p[1])
        depth = baseline - notch[1]
        self.measurement_readout = f"NOTCH {notch[0]:.6f} MHz   DEPTH {depth:.2f} dB"

    def _show_min_swr(self):
        pts = [(self.s.start + self.s.span * i / 2000.0, self.swr(self.s.start + self.s.span * i / 2000.0)) for i in range(2001)]
        f, swr = min(pts, key=lambda p: p[1])
        self.measurement_readout = f"MIN SWR {swr:.2f} @ {f:.6f} MHz   RL {self.return_loss(f):.2f} dB"

    # ------------------------------------------------------------------
    # Menu / value entry
    # ------------------------------------------------------------------
    def dialog_key(self, key, ch):
        if self.dialog and self.dialog.get("type") == "value" and key == "Return":
            target = self.dialog.get("target")
            if target in ("tg_cw", "persistence", "intensity"):
                try:
                    value = float(self.dialog.get("value", ""))
                except ValueError:
                    self.msg("INPUT ERROR", "INVALID NUMBER")
                    return
                if target == "tg_cw":
                    self.tg_cw_freq = max(0.001, min(1000.0, value))
                    self.measurement_readout = f"TG CW {self.tg_cw_freq:.6f} MHz"
                elif target == "persistence":
                    self.crt_persistence = max(0.0, min(100.0, value))
                    self.measurement_readout = f"CRT PERSISTENCE {self.crt_persistence:.0f}%"
                else:
                    self.crt_intensity = max(10.0, min(100.0, value))
                    self.measurement_readout = f"CRT INTENSITY {self.crt_intensity:.0f}%"
                self.dialog = None
                return
        super().dialog_key(key, ch)

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]

        if item == "TRACE MODE":
            i = (self.TRACE_MODES.index(self.trace_mode) + 1) % len(self.TRACE_MODES)
            self.trace_mode = self.TRACE_MODES[i]
            self.clear_trace_engine()
            self.measurement_readout = f"TRACE MODE {self.trace_mode}"
            return
        if item == "CLEAR TRACE":
            self.clear_trace_engine()
            return
        if item == "NEXT PEAK":
            self._select_peak("NEXT")
            return
        if item == "PEAK LEFT":
            self._select_peak("LEFT")
            return
        if item == "PEAK RIGHT":
            self._select_peak("RIGHT")
            return
        if item == "BANDWIDTH":
            self._show_bandwidth(False)
            return
        if item == "Q FACTOR":
            self._show_bandwidth(True)
            return
        if item == "RIPPLE":
            self._show_ripple()
            return
        if item == "NOTCH DEPTH":
            self._show_notch_depth()
            return
        if item == "MIN SWR READOUT":
            self._show_min_swr()
            return
        if item == "TG MODE":
            self.tg_mode = "CW" if self.tg_mode == "TRACK" else "TRACK"
            self.measurement_readout = f"TG MODE {self.tg_mode}"
            return
        if item == "TG CW FREQUENCY":
            self.valdlg("TG CW FREQUENCY MHz", "tg_cw")
            return
        if item == "CRT PERSISTENCE":
            self.valdlg("CRT PERSISTENCE %", "persistence")
            return
        if item == "DISPLAY INTENSITY":
            self.valdlg("CRT INTENSITY %", "intensity")
            return
        if item == "USB MODE":
            self.usb_mode = "USB REMOTE" if self.usb_mode == "SIMULATOR" else "SIMULATOR"
            self.usb_status = "WAITING FOR STM32" if self.usb_mode == "USB REMOTE" else "LOCAL DATA"
            self.measurement_readout = f"DATA SOURCE {self.usb_mode}"
            return
        if item == "USB STATUS":
            self.measurement_readout = f"USB {self.usb_status}"
            return
        if item == "SERVICE INFORMATION":
            self.msg(
                "SERVICE INFORMATION",
                f"FW {FW}\nBUILD {BUILD}\nTRACE {self.trace_mode}\nTG MODE {self.tg_mode}\n"
                f"TG CW {self.tg_cw_freq:.6f} MHz\nCRT PERSIST {self.crt_persistence:.0f}%\n"
                f"CRT INTENSITY {self.crt_intensity:.0f}%\nDATA {self.usb_mode}\nUSB {self.usb_status}",
            )
            return
        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nV7.1 Measurement / Trace Engine\nPeak Search + BW/Q\n"
                "Max/Min Hold + Average\nTG Track/CW\nUSB-ready Desktop Display",
            )
            return

        super().activate()

    # ------------------------------------------------------------------
    # V7 overlay additions
    # ------------------------------------------------------------------
    def draw_measure(self, w, h):
        super().draw_measure(w, h)

        # Persistent instrument status.  Keep it below the function-key row so
        # it never overwrites markers, Delta or the trace plot.
        self.txt(
            55,
            h - 72,
            f"MEAS {self.measurement_readout}   TRACE {self.trace_mode}   "
            f"TG {self.tg_mode}{(' ' + format(self.tg_cw_freq, '.6f') + ' MHz') if self.tg_mode == 'CW' else ''}   "
            f"CRT P{self.crt_persistence:.0f}% I{self.crt_intensity:.0f}%   {self.usb_mode}",
            BR,
            SM,
        )


if __name__ == "__main__":
    App().run()
