"""TR1604-Pro Windows CRT simulator.

Runs with the standard Python 3 library only (Tkinter). It is an early UI and
measurement-behaviour simulator for the approved green-vector CRT layout.
"""
from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import simpledialog

CRT_BG = "#020b05"
CRT_GREEN = "#63ff72"
CRT_DIM = "#1d7631"
CRT_GRID = "#174d25"
CRT_YELLOW = "#ffe43b"
CRT_CYAN = "#41e9ff"
FONT = ("Consolas", 12)
FONT_SMALL = ("Consolas", 10)
FONT_TITLE = ("Consolas", 14, "bold")


@dataclass
class Marker:
    enabled: bool
    frequency_mhz: float
    trace: str = "A"
    color: str = CRT_YELLOW


@dataclass
class SimulatorState:
    mode: str = "DUPLEX FILTER TUNE"
    start_mhz: float = 429.0
    stop_mhz: float = 433.0
    ref_dbm: float = -20.0
    db_per_div: float = 10.0
    rbw_khz: float = 30.0
    vbw_khz: float = 30.0
    sweep_ms: float = 250.0
    tg_level_dbm: float = -10.0
    selected_marker: int = 0
    markers: list[Marker] = field(default_factory=lambda: [
        Marker(True, 430.3625, "A", CRT_YELLOW),
        Marker(True, 431.9625, "A", CRT_CYAN),
        Marker(False, 431.1625, "A", CRT_GREEN),
        Marker(False, 432.5000, "A", CRT_GREEN),
    ])
    memory_enabled: bool = False
    averaging: int = 4
    show_menu: bool = True

    @property
    def center_mhz(self) -> float:
        return (self.start_mhz + self.stop_mhz) / 2.0

    @property
    def span_mhz(self) -> float:
        return self.stop_mhz - self.start_mhz


class TR1604Simulator:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("TR1604-Pro CRT Simulator")
        self.root.configure(bg="#111")
        self.root.minsize(1024, 700)
        self.canvas = tk.Canvas(self.root, bg="#111", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.state = SimulatorState()
        self._rng = random.Random(4132)
        self.root.bind("<Configure>", lambda _e: self.draw())
        self.root.bind("<Key>", self.on_key)
        self.root.after(50, self.draw)

    def on_key(self, event: tk.Event) -> None:
        key = event.keysym or ""
        raw_char = event.char if isinstance(event.char, str) else ""
        ch = raw_char.lower()

        # Python 3.14/Tk can report an empty event.char for function, modifier and
        # navigation keys. Only parse marker numbers when a real digit was received.
        if ch and ch in "1234":
            self.state.selected_marker = int(ch) - 1
            self.state.markers[self.state.selected_marker].enabled = True
        elif key in ("Left", "Right"):
            direction = -1.0 if key == "Left" else 1.0
            step = self.state.span_mhz / 1000.0
            if event.state & 0x0001:  # Shift
                step /= 10.0
            if event.state & 0x0004:  # Ctrl
                step *= 10.0
            marker = self.state.markers[self.state.selected_marker]
            marker.frequency_mhz = min(
                self.state.stop_mhz,
                max(self.state.start_mhz, marker.frequency_mhz + direction * step),
            )
        elif key == "Return":
            marker = self.state.markers[self.state.selected_marker]
            value = simpledialog.askfloat(
                "Marker frequency",
                "Frequency in MHz:",
                initialvalue=marker.frequency_mhz,
                parent=self.root,
            )
            if value is not None:
                marker.frequency_mhz = min(
                    self.state.stop_mhz,
                    max(self.state.start_mhz, value),
                )
        elif ch == "n":
            marker = self.state.markers[self.state.selected_marker]
            target = 430.3625 if marker.frequency_mhz < self.state.center_mhz else 431.9625
            marker.frequency_mhz = target
        elif ch == "p":
            self.state.markers[self.state.selected_marker].frequency_mhz = self.state.center_mhz
        elif ch == "m":
            self.state.show_menu = not self.state.show_menu
        elif ch == "a":
            self.state.averaging = {1: 4, 4: 8, 8: 16, 16: 1}[self.state.averaging]
        elif ch == "b":
            self.state.memory_enabled = not self.state.memory_enabled
        elif key == "Escape":
            self.state.show_menu = False
        elif key == "F1":
            self.state.mode = "SPECTRUM ANALYZER"
        elif key == "F2":
            self.state.mode = "DUPLEX FILTER TUNE"
        elif key == "F3":
            self.state.mode = "MEMORY / TRACE COMPARE"
        elif key == "F4":
            self.state.mode = "ANTENNA ANALYZER"
        elif ch == "s":
            self.canvas.postscript(file="tr1604_simulator_screen.ps", colormode="color")
        self.draw()

    def trace_level(self, freq: float) -> float:
        baseline = -17.0
        level = baseline
        for marker, depth, width in zip(
            self.state.markers[:2], (70.0, 68.0), (0.055, 0.065)
        ):
            x = (freq - marker.frequency_mhz) / width
            level -= depth / (1.0 + x * x)
        ripple = 0.45 * math.sin(freq * 19.0) + 0.22 * math.sin(freq * 47.0)
        noise = self._rng.uniform(-0.35, 0.35)
        return max(-110.0, level + ripple + noise)

    def marker_level(self, marker: Marker) -> float:
        return self.trace_level(marker.frequency_mhz)

    def draw_text(self, x: float, y: float, text: str, *, color: str = CRT_GREEN, font=FONT, anchor="nw") -> None:
        self.canvas.create_text(x, y, text=text, fill=color, font=font, anchor=anchor)

    def draw(self) -> None:
        self.canvas.delete("all")
        w = max(1000, self.canvas.winfo_width())
        h = max(680, self.canvas.winfo_height())
        pad = 24
        self.canvas.create_rectangle(pad, pad, w-pad, h-pad, fill=CRT_BG, outline="#2a322d", width=6)
        x0, y0, x1, y1 = pad+28, pad+25, w-pad-28, h-pad-25

        menu_w = 250 if self.state.show_menu else 0
        plot_right = x1 - menu_w - (20 if menu_w else 0)
        top_h = 105
        bottom_h = 165
        px0, py0 = x0+40, y0+top_h
        px1, py1 = plot_right, y1-bottom_h

        self.draw_text(x0, y0, f"TR4132N  TR1604-PRO  {self.state.mode}", font=FONT_TITLE)
        self.draw_text(plot_right-220, y0, f"TG ON  {self.state.tg_level_dbm:5.1f} dBm", font=FONT_TITLE)

        left_status = (
            f"REF {self.state.ref_dbm:5.1f} dBm\n"
            f"{self.state.db_per_div:.0f} dB/DIV\n"
            "LOG"
        )
        mid_status = (
            "ATTEN 20 dB\n"
            f"RBW {self.state.rbw_khz:.0f} kHz\n"
            f"VBW {self.state.vbw_khz:.0f} kHz"
        )
        self.draw_text(x0, y0+34, left_status)
        self.draw_text(x0+260, y0+34, mid_status)

        active = [m for m in self.state.markers if m.enabled]
        if active:
            marker = self.state.markers[self.state.selected_marker]
            self.draw_text(
                plot_right-315,
                y0+34,
                f"MKR {self.state.selected_marker+1} {marker.frequency_mhz:9.4f} MHz\n"
                f"{self.marker_level(marker):7.2f} dBm",
            )

        self.canvas.create_rectangle(px0, py0, px1, py1, outline=CRT_GREEN, width=2)
        for i in range(11):
            x = px0 + (px1-px0)*i/10
            self.canvas.create_line(x, py0, x, py1, fill=CRT_GRID, dash=(2,3))
        for i in range(11):
            y = py0 + (py1-py0)*i/10
            self.canvas.create_line(px0, y, px1, y, fill=CRT_GRID, dash=(2,3))
            self.draw_text(px0-10, y, f"{-10*i:>4}", anchor="e", font=FONT_SMALL)

        points = []
        count = 900
        for i in range(count):
            freq = self.state.start_mhz + self.state.span_mhz * i/(count-1)
            db = self.trace_level(freq)
            x = px0 + (px1-px0)*i/(count-1)
            y = py0 + (py1-py0)*(-db)/110.0
            points.extend((x,y))
        self.canvas.create_line(*points, fill=CRT_GREEN, width=2, smooth=False)

        if self.state.memory_enabled:
            mem = []
            for i in range(count):
                freq = self.state.start_mhz + self.state.span_mhz*i/(count-1)
                db = self.trace_level(freq) + 2.0*math.sin(i/80.0)
                x = px0 + (px1-px0)*i/(count-1)
                y = py0 + (py1-py0)*(-db)/110.0
                mem.extend((x,y))
            self.canvas.create_line(*mem, fill=CRT_YELLOW, width=1)

        for idx, marker in enumerate(self.state.markers):
            if not marker.enabled:
                continue
            x = px0 + (px1-px0)*(marker.frequency_mhz-self.state.start_mhz)/self.state.span_mhz
            db = self.marker_level(marker)
            y = py0 + (py1-py0)*(-db)/110.0
            self.canvas.create_line(x, py0, x, py1, fill=marker.color, dash=(5,4))
            self.canvas.create_polygon(x, y, x-7, y-13, x+7, y-13, fill=marker.color)
            self.draw_text(x, y+8, str(idx+1), color=marker.color, anchor="n")

        self.draw_text(px0, py1+10, f"START {self.state.start_mhz:9.4f} MHz")
        self.draw_text((px0+px1)/2, py1+10, f"CENTER {self.state.center_mhz:9.4f} MHz", anchor="n")
        self.draw_text(px1, py1+10, f"STOP {self.state.stop_mhz:9.4f} MHz", anchor="ne")
        self.draw_text((px0+px1)/2, py1+35, f"SPAN {self.state.span_mhz:7.4f} MHz   SWP {self.state.sweep_ms:.0f} ms", anchor="n")

        by = py1 + 68
        box_h = y1-by-38
        box_w = (px1-px0)/4
        for i in range(4):
            self.canvas.create_rectangle(px0+i*box_w, by, px0+(i+1)*box_w, by+box_h, outline=CRT_DIM)
        for i, marker in enumerate(self.state.markers[:2]):
            level = self.marker_level(marker)
            self.draw_text(
                px0+i*box_w+14,
                by+12,
                f"MKR {i+1}\n{marker.frequency_mhz:9.4f} MHz\n{level:7.2f} dBm",
                color=marker.color,
            )
        delta_f = self.state.markers[1].frequency_mhz-self.state.markers[0].frequency_mhz
        delta_db = self.marker_level(self.state.markers[1])-self.marker_level(self.state.markers[0])
        self.draw_text(px0+2*box_w+14, by+12, f"DELTA\n{delta_f:9.4f} MHz\n{delta_db:7.2f} dB")
        self.draw_text(px0+3*box_w+14, by+12, f"TRACE\nA LIVE\nB {'ON' if self.state.memory_enabled else 'OFF'}\nAVG {self.state.averaging}")

        self.draw_text(px0, y1-22, "F1 SPECTRUM  F2 DUPLEX  F3 MEMORY  F4 ANTENNA  M MENU  S SCREENSHOT", font=FONT_SMALL)

        if self.state.show_menu:
            mx = plot_right+18
            self.canvas.create_line(mx-10, y0+32, mx-10, y1, fill=CRT_GREEN)
            menu = [
                "DUPLEX FILTER MENU",
                "> MARKER SELECT",
                "  ENTER FREQUENCY",
                "  MARKER TO NOTCH",
                "  DELTA MARKER",
                "  BANDWIDTH",
                "  INSERT LOSS",
                "  SAVE REFERENCE",
                "  LOAD REFERENCE",
                "  CALIBRATION",
                "",
                "KEYS",
                "1..4 SELECT MARKER",
                "LEFT/RIGHT MOVE",
                "SHIFT = FINE",
                "CTRL = COARSE",
                "ENTER = EXACT FREQ",
                "N = TO NOTCH",
                "B = MEMORY TRACE",
                "A = AVERAGING",
            ]
            self.draw_text(mx, y0+42, "\n".join(menu), font=FONT_SMALL)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    TR1604Simulator().run()
