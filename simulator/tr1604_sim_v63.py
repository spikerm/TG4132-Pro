from __future__ import annotations

from tr1604_sim_v62 import App as V62App, MENUS, FW as V62_FW, G, D, SM

FW = "4.3.0"
BUILD = "desktop-v6.3-001"
MENU_WIDTH = 318


class App(V62App):
    """V6.3: hideable context menu with true full-width measurement display."""

    def __init__(self):
        self.menu_visible = True
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V6.3")

    def key(self, event):
        key = event.keysym or ""
        ch = event.char.lower() if isinstance(event.char, str) and event.char else ""

        # Dialogs keep ownership of Escape/typing until closed.
        if self.dialog:
            super().key(event)
            return

        # During startup only the inherited startup controls are active.
        if self.startup:
            super().key(event)
            return

        # M behaves as the physical MENU key: toggle context menu.
        if ch == "m":
            self.menu_visible = not self.menu_visible
            self.s.status = f"MENU {'ON' if self.menu_visible else 'OFF'}"
            self.draw()
            return

        # ESC closes the menu first, like a bench instrument.
        if key == "Escape" and self.menu_visible:
            self.menu_visible = False
            self.s.status = "MENU OFF"
            self.draw()
            return

        # If hidden, Up/Down opens the menu so the current selection is visible.
        if key in ("Up", "Down") and not self.menu_visible:
            self.menu_visible = True

        super().key(event)

    def activate(self):
        item = MENUS[self.s.screen][self.s.menu]
        if item == "SERVICE INFORMATION":
            self.msg(
                "SERVICE INFORMATION",
                f"FW {FW}\nBUILD {BUILD}\nRBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\n"
                f"SWR SCALE 1.0-{self.s.swrmax:g}\nDELTA {'ON' if self.s.delta else 'OFF'}\n"
                f"AUTO TRACK {'ON' if self.s.auto_track else 'OFF'}\n"
                f"MENU {'ON' if self.menu_visible else 'OFF'}",
            )
            return
        if item == "ABOUT":
            self.msg(
                "TR1604-PRO",
                f"Firmware {FW}\nFull-width hideable menu\nPersistent Delta / Return Loss\n"
                "Calibrated CRT scales\nSpectrum Peak Zoom\nDigital Memory / Tracking Generator",
            )
            return
        super().activate()

    def draw_measure(self, w, h):
        # V6.2 calculates the plot's right edge by reserving a 318 px menu area.
        # Supplying a wider virtual canvas while the menu is hidden moves that
        # reserved area off-screen and lets the plot occupy the real CRT width.
        effective_w = w if self.menu_visible else w + MENU_WIDTH
        super().draw_measure(effective_w, h)

        if not self.menu_visible:
            # Keep an unobtrusive reminder at the real lower-right edge.
            self.txt(w - 72, h - 70, "M MENU", D, SM, "e")


if __name__ == "__main__":
    App().run()
