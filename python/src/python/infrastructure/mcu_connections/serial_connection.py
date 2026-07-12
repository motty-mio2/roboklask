import math
import struct

import serial

from python.domain import RobotXY
from python.domain.config import settings
from python.domain.mcu_connection import McuConnection


class SerialMcuConnection(McuConnection):
    """Bidirectional serial connection to the MCU supporting command sending and encoder feedback reading."""

    def __init__(
        self,
        port: str | None = None,
        baudrate: int | None = None,
    ) -> None:
        self.port: str = port or str(settings.uart.port)
        self.baudrate: int = baudrate or settings.uart.baudrate
        self.ser: serial.Serial | None = None

    def start(self) -> None:
        try:
            # Open serial port; non-blocking writes
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"MCU Serial Connection initialized on port {self.port} at {self.baudrate} baud.")
        except Exception as e:
            print(f"Warning: Could not open serial port {self.port} ({e}). MCU communication is disabled.")
            self.ser = None

    def send_target(self, target: RobotXY | None) -> None:
        if self.ser is None or not self.ser.is_open:
            return

        if target is not None:
            target_x = target.x
            target_y = target.y
        else:
            target_x = float("nan")
            target_y = float("nan")

        try:
            # Packet structure (9 bytes total):
            # - Header: 0xAA (1 byte, unsigned char)
            # - X position target: float (4 bytes, Little-Endian)
            # - Y position target: float (4 bytes, Little-Endian)
            packet = struct.pack("<Bff", 0xAA, target_x, target_y)
            self.ser.write(packet)
            self.ser.flush()
        except Exception as e:
            print(f"Error writing binary packet to serial port {self.port}: {e}")

    def read_feedback(self) -> RobotXY | None:
        if self.ser is None or not self.ser.is_open:
            return None

        try:
            bytes_to_read = self.ser.in_waiting
            if bytes_to_read < 9:
                return None

            data = self.ser.read(bytes_to_read)

            # Search backwards from the end of the buffer to extract the most recent valid packet.
            # A valid packet starts with 0xAA (integer 170) followed by 8 bytes of payload.
            idx = len(data) - 9
            while idx >= 0:
                if data[idx] == 0xAA:
                    x_val, y_val = struct.unpack("<ff", data[idx + 1 : idx + 9])
                    if not (math.isnan(x_val) or math.isnan(y_val) or math.isinf(x_val) or math.isinf(y_val)):
                        return RobotXY(
                            x=max(-1.0, min(1.0, float(x_val))),
                            y=max(-1.0, min(1.0, float(y_val))),
                        )
                idx -= 1

        except Exception as e:
            print(f"Error reading feedback from serial port: {e}")

        return None

    def stop(self) -> None:
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
                print(f"MCU Serial Connection closed port {self.port}.")
            except Exception as e:
                print(f"Error closing serial port {self.port}: {e}")
            self.ser = None
