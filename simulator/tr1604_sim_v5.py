"""TR1604-Pro Desktop Display V5.

V5 reference UI features:
- Trace A: live measurement (green)
- Trace B: stored memory/reference (yellow dashed)
- Four independently switchable markers, all visible in the bottom readout
- Spectrum, Duplex and Antenna modes can store/toggle the reference directly
- USB remote support and slideshow startup inherited from V4/V3
"""
from __future__ import annotations

from dataclasses import dataclass, field

from tr1604_sim_v2 import MENUS, GREEN, YELLOW, CYAN, BRIGHT, DIM, BG, SMALL, TITLE
from tr1604_sim_v4 import Simulator as V4Simulator

FW_VERSION = "3.2.2"
BUILD_ID = "desktop-v5-003"

# Direct memory and marker controls in the principal measurement screens.
for _screen in (
    "SPECTRUM ANALYZER",
    "DUPLEX FILTER TUNE",
    "ANTENNA ANALYZER",
    "MEMORY / TRACE COMPARE",
):
    _menu = MENUS[_screen]
    if "MARKER SELECT" in _menu and "MARKER ON/OFF" not in _menu:
        _menu.insert(_menu.index("MARKER SELECT") + 1, "MARKER ON/OFF")

for _screen in ("SPECTRUM ANALYZER", "DUPLEX FILTER TUNE", "ANTENNA ANALYZER"):
    _menu = MENUS[_screen]
    insert_at = max(0, len(_menu) - 1)
    for _item in ("STORE MEMORY TRACE", "MEMORY OVERLAY ON/OFF"):
        if _item not in _menu:
            _menu.insert(insert_at, _item)
            insert_at += 1


@dataclass
class MemoryTrace:
    values: list[float] = field(default_factory=list)
    start_mhz: float = 0.0
    stop_mhz: float = 0.0
    kind: str = "DB"
    source_screen: str = ""
    enabled: bool = False


class Simulator(V4Simulator):
    def __init__(self) -> None:
        self.memory = MemoryTrace()
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V5")

    # ------------------------------------------------------------------
    # Keyboard / markers
    # ------------------------------------------------------------------
    def key(self, event) -> None:
        """V5 marker behaviour: 1..4 select only; X toggles selected marker."""
        if self.startup_active or self.s.dialog:
            super().key(event)
            return

        ch = event.char.lower() if isinstance(event.char, str) and event.char else ""
        # Important for Python/Tk 3.14: '' in '1234' is True, so explicitly
        # require a non-empty character before converting to int.
        if ch and ch in "1234":
            self.s.selected_marker = int(ch) - 1
            self.s.status = f"MARKER {ch} SELECTED - {'ON' if self.s.markers[self.s.selected_marker].enabled else 'OFF'}"
            self.draw()
            return
        if ch == "x":
            self.toggle_selected_marker()
            self.draw()
            return
        super().key(event)

    def toggle_selected_marker(self) -> None:
        marker = self.s.markers[self.s.selected_marker]
        marker.enabled = not marker.enabled
        self.s.status = f"MARKER {self.s.selected_marker + 1} {'ON' if marker.enabled else 'OFF'}"

    # ------------------------------------------------------------------
    # Memory trace
    # ------------------------------------------------------------------
    def _capture_memory_values(self, n: int = 700) -> tuple[list[float], str]:
        if self.s.screen == "ANTENNA ANALYZER":
            vals = [self.swr(self.s.start_mhz + self.s.span * i / (n - 1)) for i in range(n)]
            return vals, "SWR"
        return self.trace(n), "DB"

    def store_memory_trace(self) -> None:
        values, kind = self._capture_memory_values()
        self.memory = MemoryTrace(
            values=values,
            start_mhz=self.s.start_mhz,
            stop_mhz=self.s.stop_mhz,
            kind=kind,
            source_screen=self.s.screen,
            enabled=True,
        )
        self.s.trace_b = list(values)
        self.s.trace_b_on = True
        self.s.status = f"MEMORY B STORED - {self.s.screen}"

    def toggle_memory_overlay(self) -> None:
        if not self.memory.values and self.s.trace_b:
            self.memory = MemoryTrace(
                values=list(self.s.trace_b),
                start_mhz=self.s.start_mhz,
                stop_mhz=self.s.stop_mhz,
                kind="SWR" if self.s.screen == "ANTENNA ANALYZER" else "DB",
                source_screen=self.s.screen,
                enabled=True,
            )
        elif self.memory.values:
            self.memory.enabled = not self.memory.enabled
        self.s.trace_b_on = self.memory.enabled
        self.s.status = "MEMORY B ON" if self.memory.enabled else "MEMORY B OFF"

    def activate(self) -> None:
        item = MENUS[self.s.screen][self.s.menu_index]
        if item == "MARKER ON/OFF":
            self.toggle_selected_marker()
            return
        if item in ("STORE MEMORY TRACE", "STORE TRACE B"):
            self.store_memory_trace()
            return
        if item in ("MEMORY OVERLAY ON/OFF", "TRACE B ON/OFF"):
            self.toggle_memory_overlay()
            return
        if item == "ABOUT":
            self.message(
                "TR1604-PRO",
                "\n".join((
                    f"Firmware {FW_VERSION}",
                    "Digital Memory / Trace Overlay",
                    "4 Marker Measurement",
                    "Tracking Generator",
                    "CRT Overlay / USB Desktop",
                    "",
                    "R. Markesteijn",
                    f"Build {BUILD_ID}",
                )),
            )
            return
        if item == "SERVICE INFORMATION":
            state = "CONNECTED" if self.usb.snapshot.connected else "DISCONNECTED"
            mem = "ON" if self.memory.enabled else "OFF"
            active_markers = sum(1 for m in self.s.markers if m.enabled)
            self.message(
                "SERVICE INFORMATION",
                "\n".join((
                    f"FIRMWARE       {FW_VERSION}",
                    f"BUILD          {BUILD_ID}",
                    "CPU            STM32H743   OK",
                    "ADC            AD7616      OK",
                    "VECTOR DAC     DUAL 16-BIT OK",
                    "TG PLL         LOCKED      OK",
                    "SD CARD        READY       OK",
                    "BYPASS         SAFE        OK",
                    f"MARKERS        {active_markers}/4 ON",
                    f"MEMORY B       {mem}",
                    f"DATA SOURCE    {self.data_source}",
                    f"USB {self.usb_port:<7} {state}",
                )),
            )
            return
        super().activate()

    @staticmethod
    def _resample(values: list[float], n: int) -> list[float]:
        if not values:
            return []
        if len(values) == n:
            return values
        if len(values) == 1:
            return values * n
        out: list[float] = []
        for i in range(n):
            pos = i * (len(values) - 1) / (n - 1)
            lo = int(pos)
            hi = min(lo + 1, len(values) - 1)
            frac = pos - lo
            out.append(values[lo] * (1.0 - frac) + values[hi] * frac)
        return out

    def _draw_memory_overlay(self, x0, y0, x1, y1) -> None:
        if not self.memory.enabled or not self.memory.values:
            return

        mw = 290 if self.s.menu_open else 0
        pr = x1 - mw - (18 if mw else 0)
        px0 = x0 + 45
        py0 = y0 + 120
        px1 = pr
        py1 = y1 - 175
        n = 700
        values = self._resample(self.memory.values, n)
        current_kind = "SWR" if self.s.screen == "ANTENNA ANALYZER" else "DB"
        if self.memory.kind != current_kind:
            self.text(px0 + 12, py0 + 10, "MEM B: INCOMPATIBLE SCALE", color=YELLOW, font=SMALL)
            return

        points: list[float] = []
        for i, value in enumerate(values):
            x = px0 + (px1 - px0) * i / (n - 1)
            if current_kind == "SWR":
                value = max(1.0, min(self.s.swr_max, value))
                y = py0 + (py1 - py0) * ((self.s.swr_max - value) / (self.s.swr_max - 1.0))
            else:
                value = max(-110.0, min(0.0, value))
                y = py0 + (py1 - py0) * ((-value) / 110.0)
            points.extend((x, y))

        for i in range(0, n - 1, 4):
            j = min(i + 2, n - 1)
            a = i * 2
            b = j * 2
            self.c.create_line(points[a], points[a + 1], points[b], points[b + 1], fill=YELLOW, width=2)

        self.text(px1 - 12, py0 + 10, "MEM B", color=YELLOW, font=TITLE, anchor="ne")
        self.text(px1 - 12, py0 + 34, f"{self.memory.start_mhz:.4f}-{self.memory.stop_mhz:.4f} MHz", color=YELLOW, font=SMALL, anchor="ne")

    # ------------------------------------------------------------------
    # Four-marker bottom readout
    # ------------------------------------------------------------------
    def _draw_four_marker_readout(self, x0, y0, x1, y1) -> None:
        mw = 290 if self.s.menu_open else 0
        pr = x1 - mw - (18 if mw else 0)
        px0 = x0 + 45
        px1 = pr
        py1 = y1 - 175

        # Keep the four marker blocks clearly above both bottom text rows.
        # Plot labels live just below py1; status is at y1-61 and F-keys at y1-22.
        by = py1 + 50
        bottom = y1 - 88

        self.c.create_rectangle(px0 - 2, by - 2, px1 + 2, bottom + 2, fill=BG, outline=BG)
        bw = (px1 - px0) / 4.0
        colors = (YELLOW, CYAN, GREEN, BRIGHT)

        for i, marker in enumerate(self.s.markers[:4]):
            xa = px0 + i * bw
            xb = px0 + (i + 1) * bw
            selected = i == self.s.selected_marker
            outline = BRIGHT if selected else DIM
            width = 2 if selected else 1
            self.c.create_rectangle(xa, by, xb, bottom, outline=outline, width=width)

            if marker.enabled:
                if self.s.screen == "ANTENNA ANALYZER":
                    value_text = f"SWR {self.swr(marker.frequency_mhz):.2f}"
                else:
                    value_text = f"{self.level(marker.frequency_mhz):.2f} dB"
                body = f"MKR {i + 1}  ON\n{marker.frequency_mhz:.4f} MHz\n{value_text}"
                color = colors[i]
            else:
                body = f"MKR {i + 1}  OFF\n---.---- MHz\n---"
                color = DIM

            if selected:
                body = "> " + body
            self.text(xa + 10, by + 8, body, color=color, font=SMALL)

    def draw_measurement(self, x0, y0, x1, y1) -> None:
        super().draw_measurement(x0, y0, x1, y1)
        self._draw_memory_overlay(x0, y0, x1, y1)
        self._draw_four_marker_readout(x0, y0, x1, y1)

        mem_state = "MEM B ON" if self.memory.enabled else "MEM B OFF"
        mem_color = YELLOW if self.memory.enabled else DIM
        active = sum(1 for m in self.s.markers if m.enabled)
        status_y = y1 - 61
        self.text(x0 + 8, status_y, "TRACE A LIVE", color=GREEN, font=SMALL)
        self.text(x0 + 125, status_y, mem_state, color=mem_color, font=SMALL)
        self.text(x0 + 235, status_y, f"MARKERS {active}/4", color=GREEN, font=SMALL)
        self.text(x0 + 335, status_y, "1-4 SELECT  X ON/OFF", color=DIM, font=SMALL)


if __name__ == "__main__":
    Simulator().run()
