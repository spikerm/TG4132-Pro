from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UsbStatus:
    mode: str = "SIMULATOR"
    connected: bool = False
    port: str = ""
    message: str = "LOCAL DATA"


class UsbEngine:
    """Transport abstraction for the future STM32 USB CDC link."""

    def __init__(self):
        self.status = UsbStatus()

    def set_simulator(self) -> None:
        self.status = UsbStatus(mode="SIMULATOR", connected=False, message="LOCAL DATA")

    def set_remote(self, port: str = "") -> None:
        self.status = UsbStatus(mode="USB REMOTE", connected=False, port=port, message="WAITING FOR STM32")

    def mark_connected(self, port: str) -> None:
        self.status.mode = "USB REMOTE"
        self.status.connected = True
        self.status.port = port
        self.status.message = "CONNECTED"

    def encode_command(self, command: str, **fields) -> bytes:
        body = " ".join([command.upper()] + [f"{k}={v}" for k, v in fields.items()])
        return (body + "\n").encode("ascii", errors="strict")
