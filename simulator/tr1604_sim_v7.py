from __future__ import annotations

import time

from tr1604_sim_v62 import App as V62App, MENUS, G, BR, D, GRID, Y, C, SM, FN, TI

FW = "5.0.0"
BUILD = "desktop-v7-001"
BG = "#020b05"
MENU_WIDTH = 300

# V7 instrument controls. Keep the existing measurement functions and add the
# controls a bench spectrum analyser normally exposes directly.
for _screen in ("SPECTRUM ANALYZER", "DUPLEX FILTER TUNE", "MEMORY / TRACE COMPARE", "INSERTION LOSS"):
    _menu = MENUS[_screen]
    if "REF LEVEL" not in _menu:
        insert_at = _menu.index("RBW") if "RBW" in _menu else 0
        _menu.insert(insert_at, "REF LEVEL")
    if "ATTENUATION" not in _menu:
        insert_at = _menu.index("REF LEVEL") + 1
        _menu.insert(insert_at, "ATTENUATION")


class App(V62App):
    """TR1604-Pro V7 reference desktop firmware UI.

    V7 no longer fakes a hidden menu by drawing it outside the window.  The
    measurement renderer computes a true full-width plot and simply omits the
    menu tree when the MENU key is released.
    """

    def __init__(self):
        self.menu_visible = True
        self.ref_level = 0.0
        self.attenuation = 0.0
        self.sweep_started = time.monotonic()
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V7")

    # ------------------------------------------------------------------
    # Input / menu behaviour
    # ------------------------------------------------------------------
    def key(self, event):
        key = event.keysym or ""
        ch = event.char.lower() if isinstance(event.char, str) and event.char else ""

        if self.dialog or self.startup:
            super().key(event)
            return

        if ch == "m":
            self.menu_visible = not self.menu_visible
            self.s.status = f"MENU {'ON' if self.menu_visible else 'OFF'}"
            self.draw()
            return

        if key == "Escape":
            if self.menu_visible:
                self.menu_visible = False
                self.s.status = "MENU OFF"
                self.draw()
            return

        if key in ("Up", "Down") and not self.menu_visible:
            self.menu_visible = True

        super().key(event)

    def dialog_key(self, key, ch):
        # V6 handles normal numeric input.  Capture V7-only targets here while
        # retaining the same on-CRT editor.
        if self.dialog and self.dialog.get("type") == "value" and key == "Return":
            target = self.dialog.get("target")
            if target in ("ref_level", "attenuation"):
                try:
                    value = float(self.dialog.get("value", ""))
                except ValueError:
                    self.msg("INPUT ERROR", "INVALID NUMBER")
                    return
                if target == "ref_level":
                    self.ref_level = max(-100.0, min(30.0, value))
                    self.s.status = f"REF LEVEL {self.ref_level:.1f} dBm"
                else:
                    self.attenuation = max(0.0, min(70.0, value))
                    self.s.status = f"ATTENUATION {self.attenuation:.0f} dB"
                self.dialog = None
                return
        super().dialog_key(key, ch)

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]
        if item == "REF LEVEL":
            self.valdlg("REFERENCE LEVEL dBm", "ref_level")
            return
        if item == "ATTENUATION":
            self.valdlg("INPUT ATTENUATION dB", "attenuation")
            return
        if item == "SERVICE INFORMATION":
            self.msg(
                "SERVICE INFORMATION",
                f"FW {FW}\nBUILD {BUILD}\nREF LEVEL {self.ref_level:.1f} dBm\n"
                f"ATTENUATION {self.attenuation:.0f} dB\nRBW {self.s.rbw:g} kHz\n"
                f"VBW {self.s.vbw:g} kHz\nSWR SCALE 1.0-{self.s.swrmax:g}\n"
                f"DELTA {'ON' if self.s.delta else 'OFF'}\nAUTO TRACK {'ON' if self.s.auto_track else 'OFF'}\n"
                f"MENU {'ON' if self.menu_visible else 'OFF'}",
            )
            return
        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nV7 Reference Instrument UI\nDigital Memory / Trace B\n"
                "Tracking Generator\nAntenna SWR / Return Loss\nPeak / Notch Tracking",
            )
            return
        super().activate()

    # ------------------------------------------------------------------
    # Measurement helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format_df(delta_mhz: float) -> str:
        a = abs(delta_mhz)
        if a >= 1.0:
            return f"{delta_mhz:.6f} MHz"
        if a >= 0.001:
            return f"{delta_mhz * 1000.0:.3f} kHz"
        return f"{delta_mhz * 1_000_000.0:.0f} Hz"

    def _db_y_v7(self, value, py0, py1):
        # Ten vertical divisions, 10 dB/div.  REF LEVEL is the top grid line.
        bottom = self.ref_level - 100.0
        value = max(bottom, min(self.ref_level, value))
        return py0 + (py1 - py0) * ((self.ref_level - value) / 100.0)

    def _delta_readout(self, antenna: bool):
        active = [m for m in self.s.markers if m.enabled]
        if not self.s.delta:
            return "DELTA OFF", D
        if len(active) < 2:
            return "DELTA -- NEED 2 MARKERS", D
        a, b = active[0], active[1]
        df = b.f - a.f
        if antenna:
            da = self.swr(b.f) - self.swr(a.f)
            return f"DELTA  dF {self._format_df(df)}   dSWR {da:+.2f}", Y
        da = self.level(b.f) - self.level(a.f)
        return f"DELTA  dF {self._format_df(df)}   dA {da:+.2f} dB", Y

    # ------------------------------------------------------------------
    # Renderer
    # ------------------------------------------------------------------
    def draw_measure(self, w, h):
        x0, y0 = 55, 50
        x1, y1 = w - 55, h - 50
        pr = x1 - MENU_WIDTH - 18 if self.menu_visible else x1
        px0 = x0 + 58
        py0 = y0 + 125
        px1 = pr
        py1 = y1 - 230
        antenna = self.s.screen == "ANTENNA ANALYZER"

        # Header: fixed instrument information, independent of the context menu.
        self.txt(x0, y0, f"TR4132N / TR1604-PRO     {self.s.screen}", G, TI)
        self.txt(x0, y0 + 34, f"CENTER {self.s.center:.6f} MHz\nSPAN   {self.s.span:.6f} MHz")
        if antenna:
            scale_line = f"SWR 1.0-{self.s.swrmax:g}"
        else:
            scale_line = f"REF {self.ref_level:.1f} dBm\n10 dB/DIV"
        self.txt(x0 + 260, y0 + 34, f"RBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\n{scale_line}")
        self.txt(
            pr - 210,
            y0,
            f"TG {'ON' if self.s.tg else 'OFF'}   {self.s.tgl:.1f} dBm",
            G if self.s.tg else Y,
            TI,
        )

        # Selected marker + Delta is permanently visible above the plot.
        marker = self.s.markers[self.s.selected]
        if marker.enabled:
            if antenna:
                mtext = (
                    f"M{self.s.selected+1}  {marker.f:.6f} MHz   "
                    f"SWR {self.swr(marker.f):.2f}   RL {self.return_loss(marker.f):.2f} dB"
                )
            else:
                unit = "dBm" if self.s.screen == "SPECTRUM ANALYZER" else "dB"
                mtext = f"M{self.s.selected+1}  {marker.f:.6f} MHz   {self.level(marker.f):.2f} {unit}"
        else:
            mtext = f"M{self.s.selected+1} OFF"
        dtext, dcol = self._delta_readout(antenna)
        self.txt(px0, py0 - 28, mtext, BR, SM)
        self.txt(px1, py0 - 28, dtext, dcol, SM, "ne")

        # Grid + real scale values.
        self.c.create_rectangle(px0, py0, px1, py1, outline=G, width=2)
        for i in range(11):
            xx = px0 + (px1 - px0) * i / 10.0
            yy = py0 + (py1 - py0) * i / 10.0
            self.c.create_line(xx, py0, xx, py1, fill=GRID, dash=(2, 3))
            self.c.create_line(px0, yy, px1, yy, fill=GRID, dash=(2, 3))
            if antenna:
                label = f"{self.s.swrmax - (self.s.swrmax - 1.0) * i / 10.0:.1f}"
            else:
                label = f"{self.ref_level - 10.0 * i:.0f}"
            self.txt(px0 - 10, yy, label, G, SM, "e")

        # Live trace.  A subtle dim persistence trace is drawn first to mimic
        # phosphor memory without obscuring the actual measurement.
        points = []
        dim_points = []
        for i in range(700):
            f = self.s.start + self.s.span * i / 699.0
            value = self.swr(f) if antenna else self.level(f)
            xx = px0 + (px1 - px0) * i / 699.0
            yy = self._swr_y(value, py0, py1) if antenna else self._db_y_v7(value, py0, py1)
            points.extend((xx, yy))
            dim_points.extend((xx, yy + 1))
        self.c.create_line(*dim_points, fill=D, width=2)
        self.c.create_line(*points, fill=G, width=1)

        # A moving sweep cursor gives the desktop display the same live feel as
        # the eventual CRT/vector implementation.
        sweep_period = max(0.08, self.s.sweep / 1000.0)
        phase = ((time.monotonic() - self.sweep_started) % sweep_period) / sweep_period
        sweep_x = px0 + (px1 - px0) * phase
        self.c.create_line(sweep_x, py0, sweep_x, py1, fill=BR, width=1)

        # Memory B/reference overlay, always on the same calibrated scale.
        if self.mem_on and self.mem:
            for i in range(0, min(699, len(self.mem) - 1), 4):
                j = min(i + 2, len(self.mem) - 1)
                xa = px0 + (px1 - px0) * i / 699.0
                xb = px0 + (px1 - px0) * j / 699.0
                va, vb = self.mem[i], self.mem[j]
                if antenna and self.mem_kind == "SWR":
                    ya, yb = self._swr_y(va, py0, py1), self._swr_y(vb, py0, py1)
                else:
                    ya, yb = self._db_y_v7(va, py0, py1), self._db_y_v7(vb, py0, py1)
                self.c.create_line(xa, ya, xb, yb, fill=Y, width=2)

        # Markers: visible markers get a line; off-screen markers get a small
        # edge indicator without corrupting their stored frequency.
        colours = (Y, C, G, BR)
        for i, m in enumerate(self.s.markers):
            if not m.enabled:
                continue
            if m.f < self.s.start:
                self.txt(px0 + 4, py0 + 12 + i * 18, f"< M{i+1}", colours[i], SM)
                continue
            if m.f > self.s.stop:
                self.txt(px1 - 4, py0 + 12 + i * 18, f"M{i+1} >", colours[i], SM, "ne")
                continue
            xx = px0 + (px1 - px0) * (m.f - self.s.start) / self.s.span
            value = self.swr(m.f) if antenna else self.level(m.f)
            yy = self._swr_y(value, py0, py1) if antenna else self._db_y_v7(value, py0, py1)
            self.c.create_line(xx, py0, xx, py1, fill=colours[i], dash=(5, 4))
            self.txt(xx, max(py0 + 12, yy - 16), str(i + 1), colours[i], TI, "center")

        self.txt(px0, py1 + 8, f"START {self.s.start:.6f} MHz")
        self.txt((px0 + px1) / 2, py1 + 8, f"CENTER {self.s.center:.6f} MHz", G, FN, "n")
        self.txt(px1, py1 + 8, f"STOP {self.s.stop:.6f} MHz", G, FN, "ne")

        # Four fixed marker cells.  Antenna cells include Return Loss.
        by, bh = py1 + 48, 82
        bw = (px1 - px0) / 4.0
        for i, m in enumerate(self.s.markers):
            xa, xb = px0 + i * bw, px0 + (i + 1) * bw
            selected = i == self.s.selected
            self.c.create_rectangle(xa, by, xb, by + bh, outline=BR if selected else D, width=2 if selected else 1)
            if m.enabled:
                if antenna:
                    value = f"SWR {self.swr(m.f):.2f}  RL {self.return_loss(m.f):.1f} dB"
                else:
                    unit = "dBm" if self.s.screen == "SPECTRUM ANALYZER" else "dB"
                    value = f"{self.level(m.f):.2f} {unit}"
                text = f"M{i+1} ON\n{m.f:.6f} MHz\n{value}"
                col = colours[i]
            else:
                text, col = f"M{i+1} OFF\n{m.f:.6f} MHz\nOFF", D
            self.txt((xa + xb) / 2, by + 8, text, col, SM, "n")

        # Compact but complete status bar.
        status_y = by + bh + 10
        footer_delta, _ = self._delta_readout(antenna)
        tg = f"TG {self.s.tgl:.1f} dBm" if self.s.tg else "TG OFF"
        self.txt(
            px0,
            status_y,
            f"TRACE A LIVE   MEM B {'ON' if self.mem_on else 'OFF'}   {footer_delta}   "
            f"AUTO {'ON' if self.s.auto_track else 'OFF'}   {tg}",
            Y if self.s.delta else G,
            SM,
        )
        self.txt(
            px0,
            y1 - 18,
            "F1 SPECTRUM  F2 DUPLEX  F3 MEMORY  F4 ANTENNA  F5 MARKER  F6 ZOOM  F7 LOSS  F8 SETUP",
            G,
            SM,
        )

        # Context menu is genuinely absent when hidden: no divider, no text,
        # no reserved canvas.  The plot above already consumes that space.
        if self.menu_visible:
            mx = pr + 18
            self.c.create_line(mx - 10, y0 + 20, mx - 10, y1, fill=G)
            self.txt(mx, y0 + 25, self.s.screen, G, TI)
            yy = y0 + 60
            for i, item in enumerate(MENUS[self.s.screen]):
                if i == self.s.menu:
                    self.c.create_rectangle(mx - 4, yy - 2, x1 - 5, yy + 19, outline=G)
                    self.txt(mx + 4, yy, "> " + item, BR, SM)
                else:
                    self.txt(mx + 4, yy, "  " + item, G, SM)
                yy += 24
        else:
            self.txt(x1 - 5, y1 - 18, "M MENU", D, SM, "ne")


if __name__ == "__main__":
    App().run()
