"""TR1604-Pro simulator V3 launcher with slideshow-style CRT startup.

V3 reuses the V2 instrument simulator and adds the approved startup scene. During
startup the analyzer remains in hardware bypass. After the self-test the normal
Duplex Filter Tune screen opens automatically.
"""
from __future__ import annotations

import time

from tr1604_sim_v2 import (
    BG,
    BRIGHT,
    DIM,
    GREEN,
    RED,
    SMALL,
    TITLE,
    YELLOW,
    Simulator as V2Simulator,
)


class Simulator(V2Simulator):
    STARTUP_SECONDS = 4.5

    def __init__(self) -> None:
        self.startup_active = True
        self.startup_started = time.monotonic()
        super().__init__()
        self.root.title("TR1604-Pro CRT Simulator V3")
        self.root.after(100, self.startup_tick)

    def startup_tick(self) -> None:
        if not self.startup_active:
            return
        elapsed = time.monotonic() - self.startup_started
        if elapsed >= self.STARTUP_SECONDS:
            self.startup_active = False
            self.set_screen("DUPLEX FILTER TUNE")
            self.s.status = "SELF TEST PASS - BYPASS RELEASED"
        self.draw()
        if self.startup_active:
            self.root.after(100, self.startup_tick)

    def key(self, event) -> None:
        if self.startup_active:
            if event.keysym in ("Return", "space"):
                self.startup_started = time.monotonic() - self.STARTUP_SECONDS
            elif event.keysym == "Escape":
                self.root.destroy()
            return
        super().key(event)

    def draw(self) -> None:
        if not self.startup_active:
            super().draw()
            return

        self.c.delete("all")
        width = max(1180, self.c.winfo_width())
        height = max(760, self.c.winfo_height())
        margin = 22
        self.c.create_rectangle(
            margin,
            margin,
            width - margin,
            height - margin,
            fill=BG,
            outline="#2a322d",
            width=6,
        )

        elapsed = max(0.0, time.monotonic() - self.startup_started)
        progress = min(1.0, elapsed / self.STARTUP_SECONDS)
        completed = int(progress * 6)

        cx = width / 2
        self.c.create_text(
            cx,
            105,
            text="TAKEDA RIKEN",
            fill=GREEN,
            font=("Consolas", 28, "bold"),
            anchor="center",
        )
        self.c.create_text(
            cx,
            165,
            text="TR1604-PRO",
            fill=BRIGHT,
            font=("Consolas", 40, "bold"),
            anchor="center",
        )
        self.c.create_text(
            cx,
            218,
            text="DIGITAL MEMORY & TRACKING GENERATOR",
            fill=GREEN,
            font=TITLE,
            anchor="center",
        )
        self.c.create_text(
            cx,
            250,
            text="FOR TR4132 / TR4132N SPECTRUM ANALYZER",
            fill=DIM,
            font=("Consolas", 11),
            anchor="center",
        )

        steps = [
            "CPU / SDRAM",
            "AD7616 X-Y ADC",
            "VECTOR DAC / CRT OUTPUT",
            "TRACKING GENERATOR PLL",
            "SD CARD / PROFILE STORAGE",
            "X-Y-Z FAIL-SAFE BYPASS",
        ]
        y = 315
        for index, label in enumerate(steps):
            if index < completed:
                state = "OK"
                color = GREEN
            elif index == completed and progress < 1.0:
                state = "TEST"
                color = YELLOW
            else:
                state = "--"
                color = DIM
            self.c.create_text(360, y, text=label, fill=GREEN, font=TITLE, anchor="w")
            self.c.create_text(820, y, text=state, fill=color, font=TITLE, anchor="e")
            y += 42

        bar_x0, bar_x1 = 300, width - 300
        bar_y = 600
        self.c.create_rectangle(bar_x0, bar_y, bar_x1, bar_y + 24, outline=GREEN, width=2)
        self.c.create_rectangle(
            bar_x0 + 3,
            bar_y + 3,
            bar_x0 + 3 + (bar_x1 - bar_x0 - 6) * progress,
            bar_y + 21,
            fill=GREEN,
            outline="",
        )
        self.c.create_text(
            cx,
            bar_y + 42,
            text=f"INITIALIZING  {progress * 100:3.0f}%",
            fill=GREEN,
            font=SMALL,
            anchor="center",
        )
        self.c.create_text(
            cx,
            height - 82,
            text="ANALYZER BYPASS ACTIVE - CRT SIGNAL PATH SAFE",
            fill=YELLOW,
            font=TITLE,
            anchor="center",
        )
        self.c.create_text(
            65,
            height - 48,
            text="FW 0.1.0-SIM   ENTER: SKIP SELF TEST   ESC: EXIT",
            fill=DIM,
            font=SMALL,
            anchor="w",
        )


if __name__ == "__main__":
    Simulator().run()
