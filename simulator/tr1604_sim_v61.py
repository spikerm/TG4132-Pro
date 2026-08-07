from __future__ import annotations

from tr1604_sim_v6 import App as V6App, MENUS, G, BR, D, GRID, Y, C, SM, FN, TI

FW = "4.1.0"
BUILD = "desktop-v6.1-001"

# Spectrum-specific zoom controls.
_spec = MENUS["SPECTRUM ANALYZER"]
if "PEAK ZOOM" not in _spec:
    _spec.insert(_spec.index("MARKER TO PEAK") + 1, "PEAK ZOOM")
if "UNZOOM" not in _spec:
    _spec.insert(_spec.index("PEAK ZOOM") + 1, "UNZOOM")


class App(V6App):
    """V6.1: calibrated vertical scales + spectrum peak zoom."""

    def __init__(self):
        self._zoom_stack: list[tuple[float, float]] = []
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V6.1")

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]
        if item == "PEAK ZOOM":
            self.peak_zoom()
            return
        if item == "UNZOOM":
            self.unzoom()
            return
        if item == "SERVICE INFORMATION":
            self.msg(
                "SERVICE INFORMATION",
                f"FW {FW}\nBUILD {BUILD}\nRBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\n"
                f"SWR SCALE 1.0-{self.s.swrmax:g}\nAUTO TRACK {'ON' if self.s.auto_track else 'OFF'}",
            )
            return
        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nV6.1 calibrated CRT scales\nSpectrum Peak Zoom\nDigital Memory\nTracking Generator",
            )
            return
        super().activate()

    def peak_zoom(self):
        if self.s.screen != "SPECTRUM ANALYZER":
            return

        # Find the strongest peak in the currently visible span.
        best_f = self.s.start
        best_level = -1e9
        for i in range(1001):
            f = self.s.start + self.s.span * i / 1000.0
            v = self.level(f)
            if v > best_level:
                best_level = v
                best_f = f

        self.s.markers[self.s.selected].enabled = True
        self.s.markers[self.s.selected].f = best_f
        self._zoom_stack.append((self.s.start, self.s.stop))

        span = self.s.span
        if span > 2.0:
            new_span = 1.0
        elif span > 0.30:
            new_span = 0.20
        elif span > 0.075:
            new_span = 0.05
        else:
            new_span = max(0.010, span / 2.0)

        self.s.start = best_f - new_span / 2.0
        self.s.stop = best_f + new_span / 2.0
        self.s.status = f"PEAK ZOOM {best_f:.6f} MHz / SPAN {new_span:g} MHz"

    def unzoom(self):
        if self._zoom_stack:
            self.s.start, self.s.stop = self._zoom_stack.pop()
            self.s.status = f"UNZOOM / SPAN {self.s.span:g} MHz"
        else:
            self.s.status = "UNZOOM - NO PREVIOUS SPAN"

    @staticmethod
    def _db_y(v, py0, py1):
        # Fixed classic analyzer scale: 0 to -100 dB, 10 dB/div.
        v = max(-100.0, min(0.0, v))
        return py0 + (py1 - py0) * (-v / 100.0)

    def _swr_y(self, v, py0, py1):
        # SWR 1.0 is the bottom line; selected SWR SCALE is the top line.
        vmax = max(1.1, self.s.swrmax)
        v = max(1.0, min(vmax, v))
        return py1 - (py1 - py0) * ((v - 1.0) / (vmax - 1.0))

    def draw_measure(self, w, h):
        x0 = 55
        y0 = 50
        x1 = w - 55
        y1 = h - 50
        menu_w = 300
        pr = x1 - menu_w - 18
        px0 = x0 + 48
        py0 = y0 + 120
        px1 = pr
        py1 = y1 - 230
        ant = self.s.screen == "ANTENNA ANALYZER"

        self.txt(x0, y0, f"TR4132N / TR1604-PRO     {self.s.screen}", G, TI)
        self.txt(x0, y0 + 32, f"CENTER {self.s.center:.4f} MHz\nSPAN   {self.s.span:.4f} MHz")
        scale_text = f"SWR 1.0-{self.s.swrmax:g}" if ant else "10 dB/DIV"
        self.txt(x0 + 250, y0 + 32, f"RBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\n{scale_text}")
        self.txt(pr - 210, y0, f"TG {'ON' if self.s.tg else 'OFF'}  {self.s.tgl:.1f} dBm", G if self.s.tg else Y, TI)

        self.c.create_rectangle(px0, py0, px1, py1, outline=G, width=2)

        # Grid and real Y-axis values. The labels are part of the measurement,
        # not decoration: they remain visible for every mode.
        for i in range(11):
            xx = px0 + (px1 - px0) * i / 10.0
            yy = py0 + (py1 - py0) * i / 10.0
            self.c.create_line(xx, py0, xx, py1, fill=GRID, dash=(2, 3))
            self.c.create_line(px0, yy, px1, yy, fill=GRID, dash=(2, 3))
            if ant:
                value = self.s.swrmax - (self.s.swrmax - 1.0) * i / 10.0
                label = f"{value:.1f}"
            else:
                label = f"{-10 * i:d}"
            self.txt(px0 - 10, yy, label, G, SM, "e")

        # Live trace, always clipped to the selected vertical scale.
        pts = []
        for i in range(700):
            f = self.s.start + self.s.span * i / 699.0
            v = self.swr(f) if ant else self.level(f)
            xx = px0 + (px1 - px0) * i / 699.0
            yy = self._swr_y(v, py0, py1) if ant else self._db_y(v, py0, py1)
            pts.extend((xx, yy))
        self.c.create_line(*pts, fill=G, width=1)

        # Stored/reference trace on exactly the same calibrated scale.
        if self.mem_on and self.mem:
            for i in range(0, 699, 4):
                j = min(i + 2, 699)
                va = self.mem[i]
                vb = self.mem[j]
                xa = px0 + (px1 - px0) * i / 699.0
                xb = px0 + (px1 - px0) * j / 699.0
                if ant and self.mem_kind == "SWR":
                    ya = self._swr_y(va, py0, py1)
                    yb = self._swr_y(vb, py0, py1)
                else:
                    ya = self._db_y(va, py0, py1)
                    yb = self._db_y(vb, py0, py1)
                self.c.create_line(xa, ya, xb, yb, fill=Y, width=2)

        cols = (Y, C, G, BR)
        for i, m in enumerate(self.s.markers):
            if not m.enabled:
                continue
            xx = px0 + (px1 - px0) * (m.f - self.s.start) / self.s.span
            v = self.swr(m.f) if ant else self.level(m.f)
            yy = self._swr_y(v, py0, py1) if ant else self._db_y(v, py0, py1)
            self.c.create_line(xx, py0, xx, py1, fill=cols[i], dash=(5, 4))
            self.txt(xx, max(py0 + 12, yy - 16), str(i + 1), cols[i], TI, "center")

        self.txt(px0, py1 + 8, f"START {self.s.start:.4f} MHz")
        self.txt((px0 + px1) / 2, py1 + 8, f"CENTER {self.s.center:.4f} MHz", G, FN, "n")
        self.txt(px1, py1 + 8, f"STOP {self.s.stop:.4f} MHz", G, FN, "ne")

        by = py1 + 48
        bh = 82
        bw = (px1 - px0) / 4.0
        for i, m in enumerate(self.s.markers):
            xa = px0 + i * bw
            xb = xa + bw
            self.c.create_rectangle(xa, by, xb, by + bh, outline=BR if i == self.s.selected else D, width=2 if i == self.s.selected else 1)
            if m.enabled:
                val = f"SWR {self.swr(m.f):.2f}" if ant else f"{self.level(m.f):.2f} dB"
            else:
                val = "OFF"
            self.txt(xa + 8, by + 8, f"M{i+1} {'ON' if m.enabled else 'OFF'}\n{m.f:.4f} MHz\n{val}", cols[i] if m.enabled else D, SM)

        sy = by + bh + 10
        active = [m for m in self.s.markers if m.enabled]
        delta = "DELTA OFF"
        if self.s.delta and len(active) >= 2:
            a, b = active[0], active[1]
            da = (self.swr(b.f) - self.swr(a.f)) if ant else (self.level(b.f) - self.level(a.f))
            delta = f"DELTA ON  dF {b.f-a.f:.6f} MHz  dA {da:+.2f}{' SWR' if ant else ' dB'}"
        self.txt(px0, sy, f"TRACE A LIVE   MEM B {'ON' if self.mem_on else 'OFF'}   {delta}   AUTO {'ON' if self.s.auto_track else 'OFF'}", Y if self.s.delta else D, SM)
        self.txt(px0, y1 - 18, "F1 SPECTRUM  F2 DUPLEX  F3 MEMORY  F4 ANTENNA  F5 MARKER  F6 ZOOM  F7 LOSS  F8 SETUP", G, SM)

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


if __name__ == "__main__":
    App().run()
