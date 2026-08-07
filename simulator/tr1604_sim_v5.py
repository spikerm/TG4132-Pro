"""TR1604-Pro Desktop Display V5.

V5 promotes trace memory to a real reference overlay:
- Trace A: live measurement (green)
- Trace B: stored memory/reference (yellow dashed)
- The reference is retained while the live trace continues changing.
- Spectrum, Duplex and Antenna modes can store/toggle the reference directly.
- USB remote support and the V3 startup scene remain available through V4.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from tr1604_sim_v2 import MENUS, GREEN, YELLOW, DIM, SMALL, TITLE
from tr1604_sim_v4 import Simulator as V4Simulator

FW_VERSION = "3.2.0"
BUILD_ID = "desktop-v5-001"

# Add direct memory controls to the principal measurement screens.
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

    def _capture_memory_values(self, n: int = 700) -> tuple[list[float], str]:
        if self.s.screen == "ANTENNA ANALYZER":
            vals = [
                self.swr(self.s.start_mhz + self.s.span * i / (n - 1))
                for i in range(n)
            ]
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
        # Keep legacy Trace B state synchronized for Memory / Trace Compare mode.
        self.s.trace_b = list(values)
        self.s.trace_b_on = True
        self.s.status = f"MEMORY B STORED - {self.s.screen}"

    def toggle_memory_overlay(self) -> None:
        if not self.memory.values and self.s.trace_b:
            # Promote an older Trace B into the V5 overlay format.
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
                    "Tracking Generator",
                    "CRT Overlay",
                    "USB Desktop Display",
                    "",
                    "R. Markesteijn",
                    f"Build {BUILD_ID}",
                )),
            )
            return
        if item == "SERVICE INFORMATION":
            state = "CONNECTED" if self.usb.snapshot.connected else "DISCONNECTED"
            mem = "ON" if self.memory.enabled else "OFF"
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

        # Recreate the V2/V4 measurement plot geometry exactly.
        mw = 290 if self.s.menu_open else 0
        pr = x1 - mw - (18 if mw else 0)
        px0 = x0 + 45
        py0 = y0 + 120
        px1 = pr
        py1 = y1 - 175
        n = 700
        values = self._resample(self.memory.values, n)

        # Only compare like-for-like data. A dB trace is not meaningful on an SWR axis.
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

        # Dashed yellow reference makes the live green trace easy to compare.
        if len(points) >= 4:
            # Tkinter does not support dash on a smoothed arbitrary polyline equally on
            # all versions, so draw alternating short segments explicitly.
            for i in range(0, n - 1, 4):
                j = min(i + 2, n - 1)
                a = i * 2
                b = j * 2
                self.c.create_line(
                    points[a], points[a + 1], points[b], points[b + 1],
                    fill=YELLOW, width=2,
                )

        self.text(
            px1 - 12,
            py0 + 10,
            "MEM B",
            color=YELLOW,
            font=TITLE,
            anchor="ne",
        )
        self.text(
            px1 - 12,
            py0 + 34,
            f"{self.memory.start_mhz:.4f}-{self.memory.stop_mhz:.4f} MHz",
            color=YELLOW,
            font=SMALL,
            anchor="ne",
        )

    def draw_measurement(self, x0, y0, x1, y1) -> None:
        # Base renderer draws live Trace A, markers, menus and USB state.
        super().draw_measurement(x0, y0, x1, y1)
        # Draw memory last so the yellow reference remains clearly visible.
        self._draw_memory_overlay(x0, y0, x1, y1)

        # Permanent status strip for reference comparison.
        mem_state = "MEM B ON" if self.memory.enabled else "MEM B OFF"
        mem_color = YELLOW if self.memory.enabled else DIM
        self.text(x0 + 8, y1 - 43, "TRACE A LIVE", color=GREEN, font=SMALL)
        self.text(x0 + 125, y1 - 43, mem_state, color=mem_color, font=SMALL)
        if self.memory.values:
            self.text(
                x0 + 235,
                y1 - 43,
                f"REF: {self.memory.source_screen}",
                color=mem_color,
                font=SMALL,
            )


if __name__ == "__main__":
    Simulator().run()
