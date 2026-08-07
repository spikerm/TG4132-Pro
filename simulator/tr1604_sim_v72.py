from __future__ import annotations

import time

from tr1604_sim_v71 import App as V71App, MENUS, FW as V71_FW, G, BR, D, Y, C, SM
from tr1604_sim_v7 import GRID, FN, TI

FW = "5.2.0"
BUILD = "desktop-v7.2-001"
BG = "#020b05"
MENU_WIDTH = 300


class App(V71App):
    """TR1604-Pro V7.2 modular fixed-zone renderer.

    V7.2 keeps the V7.1 measurement/trace engine but gives every visual module
    its own fixed rectangle: header, measurement bar, graph, marker bank,
    primary status, secondary status and softkeys.  No module is allowed to
    draw in another module's area, which removes the footer overlap seen in
    V7.1 and mirrors the layout planned for the STM32 CRT firmware.
    """

    def __init__(self):
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V7.2")
        self.grid_brightness = 0.55

    # ------------------------------------------------------------------
    # Small formatting helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _db_unit(screen: str) -> str:
        return "dBm" if screen == "SPECTRUM ANALYZER" else "dB"

    def _selected_marker_text(self, antenna: bool) -> str:
        m = self.s.markers[self.s.selected]
        if not m.enabled:
            return f"M{self.s.selected + 1} OFF"
        if antenna:
            return (
                f"M{self.s.selected + 1}  {m.f:.6f} MHz   "
                f"SWR {self.swr(m.f):.2f}   RL {self.return_loss(m.f):.2f} dB"
            )
        return (
            f"M{self.s.selected + 1}  {m.f:.6f} MHz   "
            f"{self.level(m.f):.2f} {self._db_unit(self.s.screen)}"
        )

    def _marker_box_text(self, index: int, antenna: bool) -> tuple[str, str]:
        m = self.s.markers[index]
        colours = (Y, C, G, BR)
        if not m.enabled:
            return f"M{index+1} OFF\n{m.f:.6f} MHz\nOFF", D
        if antenna:
            value = f"SWR {self.swr(m.f):.2f}\nRL {self.return_loss(m.f):.1f} dB"
        else:
            value = f"{self.level(m.f):.2f} {self._db_unit(self.s.screen)}"
        return f"M{index+1} ON\n{m.f:.6f} MHz\n{value}", colours[index]

    # ------------------------------------------------------------------
    # Renderer
    # ------------------------------------------------------------------
    def draw_measure(self, w, h):
        x0, y0 = 38, 32
        x1, y1 = w - 38, h - 32
        right = x1 - MENU_WIDTH - 12 if self.menu_visible else x1
        antenna = self.s.screen == "ANTENNA ANALYZER"

        # Fixed vertical zones.  These are intentionally explicit so a future
        # STM32 renderer can use the same geometry contract.
        header_top = y0
        header_bottom = y0 + 96
        measure_top = header_bottom
        measure_bottom = header_bottom + 28
        graph_top = measure_bottom + 2
        graph_bottom = h - 275
        freq_top = graph_bottom + 8
        marker_top = graph_bottom + 48
        marker_bottom = marker_top + 92
        status1_y = marker_bottom + 10
        status2_y = status1_y + 24
        softkey_y = h - 56

        px0 = x0 + 58
        px1 = right
        py0 = graph_top
        py1 = graph_bottom

        # ---------------- Header ----------------
        self.txt(x0, header_top, f"TR4132N / TR1604-PRO     {self.s.screen}", G, TI)
        self.txt(x0, header_top + 34, f"CENTER {self.s.center:.6f} MHz\nSPAN   {self.s.span:.6f} MHz")
        if antenna:
            scale = f"SWR 1.0-{self.s.swrmax:g}"
        else:
            scale = f"REF {self.ref_level:.1f} dBm\n10 dB/DIV"
        self.txt(x0 + 260, header_top + 34, f"RBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\n{scale}")
        self.txt(
            right - 210,
            header_top,
            f"TG {'ON' if self.s.tg else 'OFF'}   {self.s.tgl:.1f} dBm",
            G if self.s.tg else Y,
            TI,
        )

        # ---------------- Measurement bar ----------------
        dtext, dcol = self._delta_readout(antenna)
        self.txt(px0, measure_top + 4, self._selected_marker_text(antenna), BR, SM)
        self.txt(px1, measure_top + 4, dtext, dcol, SM, "ne")

        # ---------------- Graph / graticule ----------------
        self.c.create_rectangle(px0, py0, px1, py1, outline=G, width=2)
        for i in range(11):
            xx = px0 + (px1 - px0) * i / 10.0
            yy = py0 + (py1 - py0) * i / 10.0
            self.c.create_line(xx, py0, xx, py1, fill=GRID, dash=(2, 4))
            self.c.create_line(px0, yy, px1, yy, fill=GRID, dash=(2, 4))
            if antenna:
                label = f"{self.s.swrmax - (self.s.swrmax - 1.0) * i / 10.0:.1f}"
            else:
                label = f"{self.ref_level - 10.0 * i:.0f}"
            self.txt(px0 - 10, yy, label, G, SM, "e")

        # 5 dB minor ticks for normal analyzer displays.
        if not antenna:
            for i in range(10):
                yy = py0 + (py1 - py0) * (i + 0.5) / 10.0
                self.c.create_line(px0 - 5, yy, px0 + 5, yy, fill=D)

        # Trace A with a restrained phosphor persistence ghost.
        pts = []
        ghost = []
        for i in range(700):
            f = self.s.start + self.s.span * i / 699.0
            v = self.swr(f) if antenna else self.level(f)
            xx = px0 + (px1 - px0) * i / 699.0
            yy = self._swr_y(v, py0, py1) if antenna else self._db_y_v7(v, py0, py1)
            pts.extend((xx, yy))
            ghost.extend((xx, min(py1, yy + 1.0)))
        if self.crt_persistence > 0:
            self.c.create_line(*ghost, fill=D, width=1)
        self.c.create_line(*pts, fill=G, width=1)

        # Sweep cursor.
        sweep_period = max(0.08, self.s.sweep / 1000.0)
        phase = ((time.monotonic() - self.sweep_started) % sweep_period) / sweep_period
        sx = px0 + (px1 - px0) * phase
        self.c.create_line(sx, py0, sx, py1, fill=BR, width=1)

        # Trace B / reference overlay.
        if self.mem_on and self.mem:
            last = min(699, len(self.mem) - 1)
            for i in range(0, last, 4):
                j = min(i + 2, last)
                xa = px0 + (px1 - px0) * i / 699.0
                xb = px0 + (px1 - px0) * j / 699.0
                va, vb = self.mem[i], self.mem[j]
                if antenna and self.mem_kind == "SWR":
                    ya, yb = self._swr_y(va, py0, py1), self._swr_y(vb, py0, py1)
                else:
                    ya, yb = self._db_y_v7(va, py0, py1), self._db_y_v7(vb, py0, py1)
                self.c.create_line(xa, ya, xb, yb, fill=Y, width=2)

        # Markers and off-screen indicators.
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
            v = self.swr(m.f) if antenna else self.level(m.f)
            yy = self._swr_y(v, py0, py1) if antenna else self._db_y_v7(v, py0, py1)
            self.c.create_line(xx, py0, xx, py1, fill=colours[i], dash=(5, 4))
            self.txt(xx, max(py0 + 12, yy - 16), str(i + 1), colours[i], TI, "center")

        # Frequency bar is isolated from markers/status.
        self.txt(px0, freq_top, f"START {self.s.start:.6f} MHz")
        self.txt((px0 + px1) / 2, freq_top, f"CENTER {self.s.center:.6f} MHz", G, FN, "n")
        self.txt(px1, freq_top, f"STOP {self.s.stop:.6f} MHz", G, FN, "ne")

        # ---------------- Marker bank ----------------
        bw = (px1 - px0) / 4.0
        for i in range(4):
            xa = px0 + i * bw
            xb = px0 + (i + 1) * bw
            selected = i == self.s.selected
            self.c.create_rectangle(
                xa, marker_top, xb, marker_bottom,
                outline=BR if selected else D,
                width=2 if selected else 1,
            )
            text, colour = self._marker_box_text(i, antenna)
            self.txt((xa + xb) / 2, marker_top + 8, text, colour, SM, "n")

        # ---------------- Status bars ----------------
        footer_delta, _ = self._delta_readout(antenna)
        tg = f"TG {self.s.tgl:.1f} dBm" if self.s.tg else "TG OFF"
        self.txt(
            px0,
            status1_y,
            f"TRACE A {self.trace_mode}   MEM B {'ON' if self.mem_on else 'OFF'}   "
            f"{footer_delta}   AUTO {'ON' if self.s.auto_track else 'OFF'}   {tg}",
            Y if self.s.delta else G,
            SM,
        )
        tgmode = f"TG {self.tg_mode}"
        if self.tg_mode == "CW":
            tgmode += f" {self.tg_cw_freq:.6f} MHz"
        self.txt(
            px0,
            status2_y,
            f"MEAS {self.measurement_readout}   {tgmode}   CRT P{self.crt_persistence:.0f}% "
            f"I{self.crt_intensity:.0f}%   DATA {self.usb_mode}",
            BR,
            SM,
        )

        # ---------------- Softkeys ----------------
        self.txt(
            px0,
            softkey_y,
            "F1 SPECTRUM   F2 DUPLEX   F3 MEMORY   F4 ANTENNA   F5 MARKER   F6 ZOOM   F7 LOSS   F8 SETUP",
            G,
            SM,
        )

        # ---------------- Context menu ----------------
        if self.menu_visible:
            mx = right + 18
            self.c.create_line(mx - 10, y0 + 12, mx - 10, h - 40, fill=G)
            self.txt(mx, y0 + 16, self.s.screen, G, TI)
            yy = y0 + 52
            max_y = h - 55
            for i, item in enumerate(MENUS[self.s.screen]):
                if yy > max_y:
                    self.txt(mx + 4, max_y, "...", D, SM)
                    break
                if i == self.s.menu:
                    self.c.create_rectangle(mx - 4, yy - 2, x1 - 4, yy + 19, outline=G)
                    self.txt(mx + 4, yy, "> " + item, BR, SM)
                else:
                    self.txt(mx + 4, yy, "  " + item, G, SM)
                yy += 24
        else:
            self.txt(x1 - 4, softkey_y, "M MENU", D, SM, "ne")

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]
        if item == "SERVICE INFORMATION":
            self.msg(
                "SERVICE INFORMATION",
                f"FW {FW}\nBUILD {BUILD}\nTRACE {self.trace_mode}\nTG MODE {self.tg_mode}\n"
                f"CRT PERSIST {self.crt_persistence:.0f}%\nCRT INTENSITY {self.crt_intensity:.0f}%\n"
                f"DATA {self.usb_mode}\nUSB {self.usb_status}",
            )
            return
        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nV7.2 Modular Fixed-Zone Renderer\nV7.1 Measurement / Trace Engine\n"
                "Digital Memory / Tracking Generator\nAntenna SWR / Return Loss",
            )
            return
        super().activate()


if __name__ == "__main__":
    App().run()
