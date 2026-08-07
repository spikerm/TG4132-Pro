from __future__ import annotations

from tr1604_sim_v61 import App as V61App, MENUS, G, BR, D, Y, C, SM, FN, TI

FW = "4.2.0"
BUILD = "desktop-v6.2-001"


class App(V61App):
    """V6.2: persistent measurement readouts.

    Delta and return loss are measurement values, not temporary dialogs.  They
    remain visible while tuning so the desktop build behaves like the intended
    CRT firmware.
    """

    def __init__(self):
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V6.2")

    @staticmethod
    def _format_df(delta_mhz: float) -> str:
        a = abs(delta_mhz)
        if a >= 1.0:
            return f"{delta_mhz:.6f} MHz"
        if a >= 0.001:
            return f"{delta_mhz * 1000.0:.3f} kHz"
        return f"{delta_mhz * 1_000_000.0:.0f} Hz"

    def _delta_values(self, antenna: bool):
        active = [m for m in self.s.markers if m.enabled]
        if not self.s.delta or len(active) < 2:
            return None
        a, b = active[0], active[1]
        df = b.f - a.f
        if antenna:
            da = self.swr(b.f) - self.swr(a.f)
            return df, da, "SWR"
        da = self.level(b.f) - self.level(a.f)
        return df, da, "dB"

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]
        if item == "RETURN LOSS" and self.s.screen == "ANTENNA ANALYZER":
            m = self.s.markers[self.s.selected]
            m.enabled = True
            self.s.status = (
                f"M{self.s.selected + 1}  SWR {self.swr(m.f):.2f}  "
                f"RL {self.return_loss(m.f):.2f} dB"
            )
            # No modal popup: RL is permanently visible in the measurement UI.
            return
        if item == "SERVICE INFORMATION":
            self.msg(
                "SERVICE INFORMATION",
                f"FW {FW}\nBUILD {BUILD}\nRBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\n"
                f"SWR SCALE 1.0-{self.s.swrmax:g}\nDELTA {'ON' if self.s.delta else 'OFF'}\n"
                f"AUTO TRACK {'ON' if self.s.auto_track else 'OFF'}",
            )
            return
        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nPersistent Delta / Return Loss\nCalibrated CRT scales\n"
                "Spectrum Peak Zoom\nDigital Memory / Tracking Generator",
            )
            return
        super().activate()

    def draw_measure(self, w, h):
        super().draw_measure(w, h)

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
        antenna = self.s.screen == "ANTENNA ANALYZER"

        # Persistent selected-marker measurement strip directly above the grid.
        m = self.s.markers[self.s.selected]
        if m.enabled:
            if antenna:
                selected = (
                    f"M{self.s.selected + 1}  {m.f:.6f} MHz   "
                    f"SWR {self.swr(m.f):.2f}   RL {self.return_loss(m.f):.2f} dB"
                )
            else:
                unit = "dBm" if self.s.screen == "SPECTRUM ANALYZER" else "dB"
                selected = (
                    f"M{self.s.selected + 1}  {m.f:.6f} MHz   "
                    f"{self.level(m.f):.2f} {unit}"
                )
        else:
            selected = f"M{self.s.selected + 1} OFF"

        dv = self._delta_values(antenna)
        if dv is None:
            delta_text = "DELTA OFF" if not self.s.delta else "DELTA -- NEED 2 MARKERS"
            delta_color = D
        else:
            df, da, unit = dv
            delta_text = f"DELTA  dF {self._format_df(df)}   dA {da:+.2f} {unit}"
            delta_color = Y

        # Clear only the slim measurement strip; the plot begins 25 px lower.
        self.c.create_rectangle(px0, py0 - 28, px1, py0 - 3, fill="#020b05", outline="#020b05")
        self.txt(px0, py0 - 27, selected, BR, SM)
        self.txt(px1, py0 - 27, delta_text, delta_color, SM, "ne")

        # Redraw the four marker boxes so Antenna mode always includes Return Loss.
        by = py1 + 48
        bh = 82
        bw = (px1 - px0) / 4.0
        cols = (Y, C, G, BR)
        for i, marker in enumerate(self.s.markers):
            xa = px0 + i * bw
            xb = xa + bw
            # Cover the old box interior, then redraw its border and content.
            self.c.create_rectangle(xa + 1, by + 1, xb - 1, by + bh - 1, fill="#020b05", outline="#020b05")
            self.c.create_rectangle(
                xa, by, xb, by + bh,
                outline=BR if i == self.s.selected else D,
                width=2 if i == self.s.selected else 1,
            )
            if marker.enabled:
                if antenna:
                    value = f"SWR {self.swr(marker.f):.2f}  RL {self.return_loss(marker.f):.1f} dB"
                else:
                    unit = "dBm" if self.s.screen == "SPECTRUM ANALYZER" else "dB"
                    value = f"{self.level(marker.f):.2f} {unit}"
                text = f"M{i+1} ON\n{marker.f:.4f} MHz\n{value}"
                color = cols[i]
            else:
                text = f"M{i+1} OFF\n{marker.f:.4f} MHz\nOFF"
                color = D
            self.txt(xa + 8, by + 8, text, color, SM)

        # Rewrite footer status so Delta can never disappear behind another state.
        sy = by + bh + 10
        self.c.create_rectangle(px0, sy - 2, px1, sy + 18, fill="#020b05", outline="#020b05")
        mem = f"MEM B {'ON' if self.mem_on else 'OFF'}"
        auto = f"AUTO {'ON' if self.s.auto_track else 'OFF'}"
        if dv is None:
            footer_delta = "DELTA OFF" if not self.s.delta else "DELTA --"
        else:
            df, da, unit = dv
            footer_delta = f"DELTA  {self._format_df(df)}  {da:+.2f} {unit}"
        self.txt(px0, sy, f"TRACE A LIVE   {mem}   {footer_delta}   {auto}", Y if self.s.delta else D, SM)


if __name__ == "__main__":
    App().run()
