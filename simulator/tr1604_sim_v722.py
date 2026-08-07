from __future__ import annotations

from tr1604_sim_v72 import App as V72App, MENUS, G, D, SM, BG, MENU_ROWS

FW = "5.2.2"
BUILD = "desktop-v7.2-003"


class App(V72App):
    """TR1604-Pro V7.2.2 UI polish.

    Keeps the stable V7.2 renderer and adds three targeted presentation fixes:
    - selected marker readout is explicitly prefixed with '>'
    - secondary status never renders 'MEAS MEAS ...'
    - paged menu uses one compact footer line for PAGE / MORE indicators
    """

    def __init__(self):
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V7.2.2")

    def _selected_marker_text(self, antenna: bool) -> str:
        text = super()._selected_marker_text(antenna)
        return f"> {text}"

    def draw_measure(self, w, h):
        # V7.1 initialized this as 'MEAS READY'.  V7.2 adds the MEAS label in
        # the fixed status zone, so strip a legacy prefix before rendering.
        original_readout = self.measurement_readout
        if isinstance(original_readout, str) and original_readout.upper().startswith("MEAS "):
            self.measurement_readout = original_readout[5:].lstrip()

        try:
            super().draw_measure(w, h)
        finally:
            self.measurement_readout = original_readout

        # Replace the old separate PAGE / MORE texts by one instrument-style
        # menu footer.  This is deliberately drawn last so no legacy footer can
        # remain visible underneath it.
        if self.menu_visible:
            x0, y0 = 38, 32
            x1 = w - 38
            right = x1 - 300 - 12
            mx = right + 18

            items = MENUS[self.s.screen]
            self._sync_menu_view()
            first = self.menu_first
            last = min(len(items), first + MENU_ROWS)
            yy = y0 + 62 + (last - first) * 24

            # Clear the complete old footer area, including the former PAGE and
            # bottom MORE labels.
            self.c.create_rectangle(mx - 5, yy - 3, x1 - 3, yy + 24, fill=BG, outline=BG)

            pages = max(1, (len(items) + MENU_ROWS - 1) // MENU_ROWS)
            page = min(pages, first // MENU_ROWS + 1)
            parts = [f"PAGE {page}/{pages}"]
            if first > 0:
                parts.append("▲ MORE")
            if last < len(items):
                parts.append("▼ MORE")
            footer = "        ".join(parts)
            self.txt(mx + 4, yy + 2, footer, D, SM)

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]
        if item == "SERVICE INFORMATION":
            self.msg(
                "SERVICE INFORMATION",
                f"FW {FW}\nBUILD {BUILD}\nTRACE {self.trace_mode}\nTG MODE {self.tg_mode}\n"
                f"CRT PERSIST {self.crt_persistence:.0f}%\nCRT INTENSITY {self.crt_intensity:.0f}%\n"
                f"MENU ROWS {MENU_ROWS}\nDATA {self.usb_mode}\nUSB {self.usb_status}",
            )
            return
        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nV7.2.2 CRT UI polish\n12-row paged context menu\n"
                "Fixed-zone renderer\nMeasurement / Trace Engine\nDigital Memory / Tracking Generator",
            )
            return
        super().activate()


if __name__ == "__main__":
    App().run()
