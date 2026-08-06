"""TR1604-Pro Desktop Display V4.

Slideshow-based CRT desktop build with two data sources:
- SIMULATOR: local synthetic measurement data.
- USB REMOTE: JSON-lines protocol over USB CDC/COM for the future STM32H743.

The CRT remains the primary instrument UI. Windows is only the host and optional
second screen. All settings, storage messages and connection status are rendered
inside the CRT.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from tr1604_sim_v2 import MENUS, GREEN, YELLOW, BRIGHT, DIM, SMALL, TITLE
from tr1604_sim_v3 import Simulator as V3Simulator
from tr1604_sim_v2 import Simulator as V2Simulator

FW_VERSION = "3.1.0"
BUILD_ID = "desktop-v4-001"

# Extend the slideshow setup menu. The list is shared with the V2/V3 renderer.
_setup = MENUS["SYSTEM SETUP"]
for _item in ("DATA SOURCE", "USB PORT", "USB CONNECT/DISCONNECT", "SERVICE INFORMATION"):
    if _item not in _setup:
        _setup.insert(-2, _item)


@dataclass
class RemoteSnapshot:
    connected: bool = False
    port: str = "COM3"
    last_error: str = ""
    last_rx: float = 0.0
    sequence: int = 0
    trace: list[float] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)


class UsbRemoteSource:
    """Optional USB CDC transport.

    Protocol: one UTF-8 JSON object per line. Supported packets:
      {"type":"status", "center_mhz":..., "tg_level_dbm":...}
      {"type":"trace", "sequence":12, "values":[...]}
      {"type":"event", "message":"..."}

    Commands are also JSON lines, for example:
      {"cmd":"set_tg_level", "value_dbm":-20.0}
    """

    def __init__(self) -> None:
        self.snapshot = RemoteSnapshot(port=os.environ.get("TR1604_COM", "COM3"))
        self._serial = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._rx: queue.Queue[dict[str, Any]] = queue.Queue()

    def connect(self, port: str) -> tuple[bool, str]:
        if self.snapshot.connected:
            return True, "already connected"
        try:
            import serial  # type: ignore
        except ImportError:
            return False, "pyserial is not installed"
        try:
            self._serial = serial.Serial(port=port, baudrate=921600, timeout=0.15)
        except Exception as exc:  # hardware/driver dependent
            self.snapshot.last_error = str(exc)
            return False, str(exc)
        self.snapshot.port = port
        self.snapshot.connected = True
        self.snapshot.last_error = ""
        self._stop.clear()
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        self.send({"cmd": "hello", "client": "TR1604-Pro Desktop", "version": FW_VERSION})
        return True, "connected"

    def disconnect(self) -> None:
        self._stop.set()
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
        self.snapshot.connected = False

    def _reader(self) -> None:
        assert self._serial is not None
        while not self._stop.is_set():
            try:
                raw = self._serial.readline()
                if not raw:
                    continue
                packet = json.loads(raw.decode("utf-8", errors="replace"))
                if isinstance(packet, dict):
                    self._rx.put(packet)
            except Exception as exc:
                self.snapshot.last_error = str(exc)
                self.snapshot.connected = False
                break

    def poll(self) -> None:
        while True:
            try:
                packet = self._rx.get_nowait()
            except queue.Empty:
                break
            self.snapshot.last_rx = time.monotonic()
            kind = packet.get("type")
            if kind == "trace" and isinstance(packet.get("values"), list):
                self.snapshot.trace = [float(v) for v in packet["values"]]
                self.snapshot.sequence = int(packet.get("sequence", self.snapshot.sequence + 1))
            elif kind == "status":
                self.snapshot.fields.update(packet)
            elif kind == "event":
                self.snapshot.fields["last_event"] = str(packet.get("message", ""))

    def send(self, packet: dict[str, Any]) -> bool:
        if not self.snapshot.connected or self._serial is None:
            return False
        try:
            self._serial.write((json.dumps(packet, separators=(",", ":")) + "\n").encode("utf-8"))
            return True
        except Exception as exc:
            self.snapshot.last_error = str(exc)
            self.snapshot.connected = False
            return False


class Simulator(V3Simulator):
    def __init__(self) -> None:
        self.data_source = "SIMULATOR"
        self.usb = UsbRemoteSource()
        self.usb_port = self.usb.snapshot.port
        super().__init__()
        self.root.title("TR1604-Pro Desktop Display V4")
        self.root.after(100, self.remote_tick)

    def remote_tick(self) -> None:
        self.usb.poll()
        if self.data_source == "USB REMOTE" and self.usb.snapshot.connected:
            fields = self.usb.snapshot.fields
            for remote, local in (
                ("start_mhz", "start_mhz"), ("stop_mhz", "stop_mhz"),
                ("rbw_khz", "rbw_khz"), ("vbw_khz", "vbw_khz"),
                ("sweep_ms", "sweep_ms"), ("tg_level_dbm", "tg_level_dbm"),
            ):
                if remote in fields:
                    setattr(self.s, local, float(fields[remote]))
            if "tg_enabled" in fields:
                self.s.tg_enabled = bool(fields["tg_enabled"])
        if not self.startup_active:
            self.draw()
        self.root.after(100, self.remote_tick)

    def trace(self, n: int = 700) -> list[float]:
        if self.data_source == "USB REMOTE" and self.usb.snapshot.trace:
            values = self.usb.snapshot.trace
            if len(values) == n:
                return values
            # Linear resampling keeps the renderer independent of firmware point count.
            if len(values) > 1:
                result = []
                for i in range(n):
                    pos = i * (len(values) - 1) / (n - 1)
                    lo = int(pos)
                    hi = min(lo + 1, len(values) - 1)
                    frac = pos - lo
                    result.append(values[lo] * (1.0 - frac) + values[hi] * frac)
                return result
        return V2Simulator.trace(self, n)

    def activate(self) -> None:
        item = MENUS[self.s.screen][self.s.menu_index]
        if item == "DATA SOURCE":
            self.data_source = "USB REMOTE" if self.data_source == "SIMULATOR" else "SIMULATOR"
            self.s.status = f"DATA SOURCE {self.data_source}"
            self.message("DATA SOURCE", f"ACTIVE\n{self.data_source}\n\nUSB remains fail-safe")
            return
        if item == "USB PORT":
            # Existing CRT numeric editor cannot type COM text yet. Cycle common ports.
            ports = [f"COM{i}" for i in range(1, 17)]
            try:
                idx = ports.index(self.usb_port)
            except ValueError:
                idx = 2
            self.usb_port = ports[(idx + 1) % len(ports)]
            self.usb.snapshot.port = self.usb_port
            self.message("USB PORT", f"SELECTED\n{self.usb_port}\n\nPress ENTER")
            return
        if item == "USB CONNECT/DISCONNECT":
            if self.usb.snapshot.connected:
                self.usb.disconnect()
                self.message("USB REMOTE", "DISCONNECTED\nLOCAL OPERATION CONTINUES")
            else:
                ok, detail = self.usb.connect(self.usb_port)
                if ok:
                    self.data_source = "USB REMOTE"
                    self.message("USB REMOTE", f"CONNECTED\n{self.usb_port}\n921600 baud")
                else:
                    self.message("USB CONNECTION", f"FAILED\n{detail}\n\nInstall: py -m pip install pyserial")
            return
        if item == "SERVICE INFORMATION":
            state = "CONNECTED" if self.usb.snapshot.connected else "DISCONNECTED"
            age = "---" if not self.usb.snapshot.last_rx else f"{time.monotonic()-self.usb.snapshot.last_rx:.1f} s"
            self.message(
                "SERVICE INFORMATION",
                "\n".join((
                    f"FIRMWARE       {FW_VERSION}",
                    f"BUILD          {BUILD_ID}",
                    "CPU            STM32H743   OK",
                    "ADC            AD7616      OK",
                    "VECTOR DAC     DUAL 16-BIT OK",
                    "TG PLL         LOCKED      OK",
                    "SD CARD        READY       OK",
                    "BYPASS         SAFE        OK",
                    f"DATA SOURCE    {self.data_source}",
                    f"USB {self.usb_port:<7} {state}",
                    f"LAST USB RX    {age}",
                )),
            )
            return
        if item == "ABOUT":
            self.message(
                "TR1604-PRO",
                "\n".join((
                    f"Firmware {FW_VERSION}",
                    "Digital Memory",
                    "Tracking Generator",
                    "CRT Overlay",
                    "USB Desktop Display",
                    "",
                    "R. Markesteijn",
                    f"Build {BUILD_ID}",
                )),
            )
            return
        super().activate()
        self._send_changed_setting(item)

    def _send_changed_setting(self, item: str) -> None:
        if self.data_source != "USB REMOTE" or not self.usb.snapshot.connected:
            return
        commands = {
            "TG ON/OFF": {"cmd": "set_tg", "enabled": self.s.tg_enabled},
            "TG LEVEL": {"cmd": "set_tg_level", "value_dbm": self.s.tg_level_dbm},
            "SPAN": {"cmd": "set_span", "value_mhz": self.s.span},
            "RBW / VBW": {"cmd": "set_bandwidths", "rbw_khz": self.s.rbw_khz, "vbw_khz": self.s.vbw_khz},
        }
        packet = commands.get(item)
        if packet:
            self.usb.send(packet)

    def draw_setup(self, x0, y0, x1, y1) -> None:
        super().draw_setup(x0, y0, x1, y1)
        usb_state = "CONNECTED" if self.usb.snapshot.connected else "DISCONNECTED"
        self.text(
            x0,
            y0 + 305,
            f"DATA SOURCE      {self.data_source}\nUSB PORT         {self.usb_port}\nUSB STATUS       {usb_state}\nPROTOCOL         JSONL CDC V1",
            color=GREEN if self.usb.snapshot.connected else DIM,
            font=TITLE,
        )

    def draw_measurement(self, x0, y0, x1, y1) -> None:
        super().draw_measurement(x0, y0, x1, y1)
        state = "USB" if self.data_source == "USB REMOTE" else "SIM"
        color = GREEN if self.usb.snapshot.connected or state == "SIM" else YELLOW
        self.text(x1 - 100, y1 - 22, state, color=color, font=SMALL, anchor="ne")


if __name__ == "__main__":
    Simulator().run()
