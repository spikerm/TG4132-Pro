"""TR1604-Pro Desktop Display V5.1.

Footer/layout correction for V5:
- completely masks the inherited legacy footer before redrawing it;
- four marker blocks occupy their own dedicated row;
- status and F-key rows are separated and never overlap marker readouts.
"""
from __future__ import annotations

from tr1604_sim_v2 import BG, BRIGHT, CYAN, DIM, GREEN, SMALL, YELLOW
from tr1604_sim_v5 import Simulator as V5Simulator

FW_VERSION = "3.2.3"
BUILD_ID = "desktop-v5-004"


class Simulator(V5Simulator):
    def _footer_geometry(self, x0, y0, x1, y1):
        mw = 290 if self.s.menu_open else 0
        pr = x1 - mw - (18 if mw else 0)
        px0 = x0 + 45
        px1 = pr
        py1 = y1 - 175
        return px0, px1, py1, pr

    def _clear_legacy_footer(self, x0, y0, x1, y1) -> None:
        px0, px1, py1, _ = self._footer_geometry(x0, y0, x1, y1)
        # Preserve START/CENTER/STOP at py1+10, but erase everything below it.
        self.c.create_rectangle(
            x0 - 4,
            py1 + 42,
            px1 + 4,
            y1 + 2,
            fill=BG,
            outline=BG,
        )

    def _draw_footer_v51(self, x0, y0, x1, y1) -> None:
        px0, px1, py1, _ = self._footer_geometry(x0, y0, x1, y1)
        bw = (px1 - px0) / 4.0
        colors = (YELLOW, CYAN, GREEN, BRIGHT)

        # Dedicated marker row.
        marker_top = py1 + 48
        marker_bottom = marker_top + 62
        for i, marker in enumerate(self.s.markers[:4]):
            xa = px0 + i * bw
            xb = px0 + (i + 1) * bw
            selected = i == self.s.selected_marker
            self.c.create_rectangle(
                xa,
                marker_top,
                xb,
                marker_bottom,
                outline=BRIGHT if selected else DIM,
                width=2 if selected else 1,
            )
            prefix = "> " if selected else "  "
            if marker.enabled:
                if self.s.screen == "ANTENNA ANALYZER":
                    value = f"SWR {self.swr(marker.frequency_mhz):.2f}"
                else:
                    value = f"{self.level(marker.frequency_mhz):.2f} dB"
                text = f"{prefix}MKR {i+1}  ON\n  {marker.frequency_mhz:.4f} MHz\n  {value}"
                color = colors[i]
            else:
                text = f"{prefix}MKR {i+1}  OFF\n  ---.---- MHz\n  ---"
                color = DIM
            self.text(xa + 8, marker_top + 7, text, color=color, font=SMALL)

        # Dedicated status row beneath the marker blocks.
        status_y = marker_bottom + 10
        active = sum(1 for marker in self.s.markers if marker.enabled)
        mem_state = "MEM B ON" if self.memory.enabled else "MEM B OFF"
        self.text(px0, status_y, "TRACE A LIVE", color=GREEN, font=SMALL)
        self.text(px0 + 115, status_y, mem_state, color=YELLOW if self.memory.enabled else DIM, font=SMALL)
        self.text(px0 + 225, status_y, f"MARKERS {active}/4", color=GREEN, font=SMALL)
        self.text(px0 + 325, status_y, "1-4 SELECT   X ON/OFF", color=DIM, font=SMALL)

        # Dedicated soft-key row at the bottom.
        key_y = status_y + 27
        self.text(
            px0,
            key_y,
            "F1 SPECTRUM  F2 DUPLEX  F3 MEMORY  F4 ANTENNA  F5 MARKER  F6 ZOOM  F7 LOSS  F8 SETUP",
            color=GREEN,
            font=SMALL,
        )

    def draw_measurement(self, x0, y0, x1, y1) -> None:
        # Draw normal V5 screen first (trace/menu/memory), then completely replace footer.
        super().draw_measurement(x0, y0, x1, y1)
        self._clear_legacy_footer(x0, y0, x1, y1)
        self._draw_footer_v51(x0, y0, x1, y1)


if __name__ == "__main__":
    Simulator().run()
