"""TR1604-Pro Windows CRT simulator.

Tkinter-only simulator for the approved CRT interface. F1-F4 select genuinely
separate measurement modes. Menus are navigable with Up/Down and Enter.
"""
from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import messagebox, simpledialog

CRT_BG = "#020b05"
CRT_GREEN = "#63ff72"
CRT_BRIGHT = "#b7ffbe"
CRT_DIM = "#1d7631"
CRT_GRID = "#174d25"
CRT_YELLOW = "#ffe43b"
CRT_CYAN = "#41e9ff"
FONT = ("Consolas", 12)
FONT_SMALL = ("Consolas", 10)
FONT_TITLE = ("Consolas", 14, "bold")

MODE_PRESETS = {
    "SPECTRUM ANALYZER": (140.0, 150.0),
    "DUPLEX FILTER TUNE": (429.0, 433.0),
    "MEMORY / TRACE COMPARE": (429.0, 433.0),
    "ANTENNA ANALYZER": (140.0, 150.0),
}

MODE_MENUS = {
    "SPECTRUM ANALYZER": [
        "TRACKING GENERATOR ON/OFF", "MARKER SELECT", "ENTER FREQUENCY",
        "MARKER TO PEAK", "CENTER = MARKER", "SET START / STOP", "SET SPAN",
        "RBW / VBW", "TRACE MODE", "SAVE TRACE",
    ],
    "DUPLEX FILTER TUNE": [
        "TRACKING GENERATOR ON/OFF", "MARKER SELECT", "ENTER FREQUENCY",
        "MARKER TO NOTCH", "DELTA MARKER", "BANDWIDTH", "INSERTION LOSS",
        "PASS / FAIL LIMITS", "SAVE PROFILE", "LOAD PROFILE", "CALIBRATION",
    ],
    "MEMORY / TRACE COMPARE": [
        "TRACKING GENERATOR ON/OFF", "TRACE A LIVE", "TRACE B ON / OFF",
        "STORE TRACE B", "A - B", "MAX HOLD", "MIN HOLD", "AVERAGING",
        "SAVE TO SD", "RECALL FROM SD",
    ],
    "ANTENNA ANALYZER": [
        "TRACKING GENERATOR ON/OFF", "MARKER SELECT", "ENTER FREQUENCY",
        "MARKER TO MIN SWR", "RETURN LOSS", "SWR SCALE", "BANDWIDTH SWR < 2",
        "OPEN / SHORT / LOAD", "SAVE RESULT",
    ],
}


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
    tg_enabled: bool = True
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
    menu_index: int = 0
    status_message: str = "READY"

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

    def set_mode(self, mode: str) -> None:
        self.state.mode = mode
        self.state.start_mhz, self.state.stop_mhz = MODE_PRESETS[mode]
        self.state.menu_index = 0
        if mode == "SPECTRUM ANALYZER":
            freqs = (145.425, 146.275)
        elif mode in ("DUPLEX FILTER TUNE", "MEMORY / TRACE COMPARE"):
            freqs = (430.3625, 431.9625)
        else:
            freqs = (145.425, 147.000)
        self.state.markers[0].frequency_mhz = freqs[0]
        self.state.markers[1].frequency_mhz = freqs[1]
        self.state.status_message = mode

    def toggle_tg(self) -> None:
        self.state.tg_enabled = not self.state.tg_enabled
        self.state.status_message = "TG ON" if self.state.tg_enabled else "TG OFF"

    def on_key(self, event: tk.Event) -> None:
        key = event.keysym or ""
        ch = event.char.lower() if isinstance(event.char, str) and event.char else ""

        if key == "F1": self.set_mode("SPECTRUM ANALYZER")
        elif key == "F2": self.set_mode("DUPLEX FILTER TUNE")
        elif key == "F3": self.set_mode("MEMORY / TRACE COMPARE")
        elif key == "F4": self.set_mode("ANTENNA ANALYZER")
        elif ch == "t": self.toggle_tg()
        elif ch in "1234" and ch:
            self.state.selected_marker = int(ch) - 1
            self.state.markers[self.state.selected_marker].enabled = True
            self.state.status_message = f"MARKER {ch} SELECTED"
        elif key in ("Up", "Down") and self.state.show_menu:
            size = len(MODE_MENUS[self.state.mode])
            self.state.menu_index = (self.state.menu_index + (-1 if key == "Up" else 1)) % size
        elif key in ("Left", "Right"):
            direction = -1.0 if key == "Left" else 1.0
            step = self.state.span_mhz / 1000.0
            if event.state & 0x0001: step /= 10.0
            if event.state & 0x0004: step *= 10.0
            marker = self.state.markers[self.state.selected_marker]
            marker.frequency_mhz = min(self.state.stop_mhz, max(self.state.start_mhz, marker.frequency_mhz + direction * step))
        elif key == "Return":
            if self.state.show_menu: self.activate_menu_item()
            else: self.enter_marker_frequency()
        elif ch in ("n", "p"): self.marker_to_feature()
        elif ch == "m": self.state.show_menu = not self.state.show_menu
        elif ch == "a":
            self.state.averaging = {1: 4, 4: 8, 8: 16, 16: 1}[self.state.averaging]
            self.state.status_message = f"AVERAGING {self.state.averaging}"
        elif ch == "b":
            self.state.memory_enabled = not self.state.memory_enabled
            self.state.status_message = "TRACE B ON" if self.state.memory_enabled else "TRACE B OFF"
        elif key == "Escape": self.state.show_menu = False
        elif ch == "s":
            self.canvas.postscript(file="tr1604_simulator_screen.ps", colormode="color")
            self.state.status_message = "SCREEN SAVED"
        self.draw()

    def enter_marker_frequency(self) -> None:
        marker = self.state.markers[self.state.selected_marker]
        value = simpledialog.askfloat("Marker frequency", "Frequency in MHz:", initialvalue=marker.frequency_mhz, parent=self.root)
        if value is not None:
            marker.frequency_mhz = min(self.state.stop_mhz, max(self.state.start_mhz, value))
            self.state.status_message = "MARKER FREQUENCY SET"

    def marker_to_feature(self) -> None:
        marker = self.state.markers[self.state.selected_marker]
        if self.state.mode in ("DUPLEX FILTER TUNE", "MEMORY / TRACE COMPARE"):
            targets = (430.3625, 431.9625)
        elif self.state.mode == "SPECTRUM ANALYZER":
            targets = (145.425, 146.275)
        else:
            targets = (145.425,)
        marker.frequency_mhz = min(targets, key=lambda f: abs(f - marker.frequency_mhz))
        self.state.status_message = "MARKER TO FEATURE"

    def activate_menu_item(self) -> None:
        item = MODE_MENUS[self.state.mode][self.state.menu_index]
        if item == "TRACKING GENERATOR ON/OFF": self.toggle_tg()
        elif item == "ENTER FREQUENCY": self.enter_marker_frequency()
        elif "MARKER TO" in item: self.marker_to_feature()
        elif item == "TRACE B ON / OFF":
            self.state.memory_enabled = not self.state.memory_enabled
        elif item == "AVERAGING":
            self.state.averaging = {1: 4, 4: 8, 8: 16, 16: 1}[self.state.averaging]
        elif item == "SET START / STOP":
            start = simpledialog.askfloat("Start frequency", "Start MHz:", initialvalue=self.state.start_mhz, parent=self.root)
            stop = simpledialog.askfloat("Stop frequency", "Stop MHz:", initialvalue=self.state.stop_mhz, parent=self.root)
            if start is not None and stop is not None and stop > start:
                self.state.start_mhz, self.state.stop_mhz = start, stop
        elif item == "SET SPAN":
            span = simpledialog.askfloat("Span", "Span MHz:", initialvalue=self.state.span_mhz, parent=self.root)
            if span and span > 0:
                center = self.state.center_mhz
                self.state.start_mhz, self.state.stop_mhz = center-span/2, center+span/2
        else:
            messagebox.showinfo("TR1604-Pro", f"{item}\n\nDeze functie wordt in de volgende softwarestap aangesloten.", parent=self.root)
        self.state.status_message = item

    def trace_level(self, freq: float) -> float:
        if not self.state.tg_enabled and self.state.mode != "SPECTRUM ANALYZER":
            return -92.0 + self._rng.uniform(-2.0, 2.0)
        if self.state.mode == "SPECTRUM ANALYZER":
            level = -88.0
            for peak, amp, width in ((145.425, 67.0, 0.10), (146.275, 49.0, 0.16)):
                x = (freq-peak)/width
                level += amp/(1+x*x)
            return min(-4.0, level + self._rng.uniform(-0.8, 0.8))
        if self.state.mode in ("DUPLEX FILTER TUNE", "MEMORY / TRACE COMPARE"):
            level = -17.0
            for marker, depth, width in zip(self.state.markers[:2], (70.0, 68.0), (0.055, 0.065)):
                x = (freq-marker.frequency_mhz)/width
                level -= depth/(1+x*x)
            return max(-110.0, level + 0.45*math.sin(freq*19.0) + self._rng.uniform(-0.35, 0.35))
        # Antenna analyzer uses return-loss style dip.
        x = (freq-145.425)/0.42
        return max(-50.0, -4.0 - 38.0/(1+x*x) + self._rng.uniform(-0.25, 0.25))

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
        menu_w = 270 if self.state.show_menu else 0
        plot_right = x1-menu_w-(20 if menu_w else 0)
        top_h, bottom_h = 105, 165
        px0, py0 = x0+40, y0+top_h
        px1, py1 = plot_right, y1-bottom_h

        self.draw_text(x0, y0, f"TR4132N  TR1604-PRO  {self.state.mode}", font=FONT_TITLE)
        tg_text = f"TG {'ON ' + format(self.state.tg_level_dbm, '5.1f') + ' dBm' if self.state.tg_enabled else 'OFF'}"
        self.draw_text(plot_right-230, y0, tg_text, color=CRT_GREEN if self.state.tg_enabled else CRT_YELLOW, font=FONT_TITLE)
        self.draw_text(x0, y0+34, f"REF {self.state.ref_dbm:5.1f} dBm\n{self.state.db_per_div:.0f} dB/DIV\nLOG")
        self.draw_text(x0+260, y0+34, f"ATTEN 20 dB\nRBW {self.state.rbw_khz:.0f} kHz\nVBW {self.state.vbw_khz:.0f} kHz")
        marker = self.state.markers[self.state.selected_marker]
        self.draw_text(plot_right-320, y0+34, f"MKR {self.state.selected_marker+1}  {marker.frequency_mhz:9.4f} MHz\n{self.marker_level(marker):7.2f} dB")

        self.canvas.create_rectangle(px0, py0, px1, py1, outline=CRT_GREEN, width=2)
        for i in range(11):
            x = px0+(px1-px0)*i/10
            self.canvas.create_line(x, py0, x, py1, fill=CRT_GRID, dash=(2,3))
            y = py0+(py1-py0)*i/10
            self.canvas.create_line(px0, y, px1, y, fill=CRT_GRID, dash=(2,3))
            self.draw_text(px0-10, y, f"{-10*i:>4}", anchor="e", font=FONT_SMALL)

        count, points = 900, []
        for i in range(count):
            freq = self.state.start_mhz+self.state.span_mhz*i/(count-1)
            db = self.trace_level(freq)
            points += [px0+(px1-px0)*i/(count-1), py0+(py1-py0)*(-db)/110.0]
        self.canvas.create_line(*points, fill=CRT_GREEN, width=2)

        if self.state.memory_enabled:
            mem = []
            for i in range(count):
                freq = self.state.start_mhz+self.state.span_mhz*i/(count-1)
                db = self.trace_level(freq)+2.0*math.sin(i/80.0)
                mem += [px0+(px1-px0)*i/(count-1), py0+(py1-py0)*(-db)/110.0]
            self.canvas.create_line(*mem, fill=CRT_YELLOW, width=1)

        for idx, m in enumerate(self.state.markers):
            if not m.enabled or not self.state.start_mhz <= m.frequency_mhz <= self.state.stop_mhz: continue
            x = px0+(px1-px0)*(m.frequency_mhz-self.state.start_mhz)/self.state.span_mhz
            y = py0+(py1-py0)*(-self.marker_level(m))/110.0
            width = 3 if idx == self.state.selected_marker else 1
            self.canvas.create_line(x, py0, x, py1, fill=m.color, dash=(5,4), width=width)
            self.canvas.create_polygon(x, y, x-7, y-13, x+7, y-13, fill=m.color)
            self.draw_text(x, y+8, str(idx+1), color=m.color, anchor="n")

        self.draw_text(px0, py1+10, f"START {self.state.start_mhz:9.4f} MHz")
        self.draw_text((px0+px1)/2, py1+10, f"CENTER {self.state.center_mhz:9.4f} MHz", anchor="n")
        self.draw_text(px1, py1+10, f"STOP {self.state.stop_mhz:9.4f} MHz", anchor="ne")
        self.draw_text((px0+px1)/2, py1+35, f"SPAN {self.state.span_mhz:7.4f} MHz   SWP {self.state.sweep_ms:.0f} ms", anchor="n")

        by, box_w = py1+68, (px1-px0)/4
        box_h = y1-by-38
        for i in range(4): self.canvas.create_rectangle(px0+i*box_w, by, px0+(i+1)*box_w, by+box_h, outline=CRT_DIM)
        for i, m in enumerate(self.state.markers[:2]):
            self.draw_text(px0+i*box_w+14, by+12, f"MKR {i+1}\n{m.frequency_mhz:9.4f} MHz\n{self.marker_level(m):7.2f} dB", color=m.color)
        delta_f = self.state.markers[1].frequency_mhz-self.state.markers[0].frequency_mhz
        delta_db = self.marker_level(self.state.markers[1])-self.marker_level(self.state.markers[0])
        self.draw_text(px0+2*box_w+14, by+12, f"DELTA\n{delta_f:9.4f} MHz\n{delta_db:7.2f} dB")
        self.draw_text(px0+3*box_w+14, by+12, f"TRACE\nA LIVE\nB {'ON' if self.state.memory_enabled else 'OFF'}\nAVG {self.state.averaging}")
        self.draw_text(px0, y1-22, f"F1 SPECTRUM  F2 DUPLEX  F3 MEMORY  F4 ANTENNA  T TG ON/OFF  M MENU   {self.state.status_message}", font=FONT_SMALL)

        if self.state.show_menu:
            mx = plot_right+18
            self.canvas.create_line(mx-10, y0+32, mx-10, y1, fill=CRT_GREEN)
            self.draw_text(mx, y0+42, f"{self.state.mode} MENU", font=FONT_SMALL)
            y = y0+70
            for idx, item in enumerate(MODE_MENUS[self.state.mode]):
                selected = idx == self.state.menu_index
                prefix = "> " if selected else "  "
                self.draw_text(mx, y, prefix+item, color=CRT_BRIGHT if selected else CRT_GREEN, font=FONT_SMALL)
                y += 20
            self.draw_text(mx, y+16, "UP/DOWN = SELECT\nENTER = ACTIVATE\nT = TG ON/OFF\n1..4 = MARKER\nLEFT/RIGHT = MOVE", font=FONT_SMALL)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    TR1604Simulator().run()
