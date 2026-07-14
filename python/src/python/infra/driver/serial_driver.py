import math
import struct

import serial

from python.domain.config import SerialConfig
from python.domain.driver.base import RobotXY
from python.domain.model.shared import Shared
from python.domain.runtime import Runtime


class SerialDriver:
    def __init__(self, shared: Shared) -> None:
        sc = SerialConfig()

        self.port = sc.serial_port
        self.baudrate = sc.baudrate
        self.shared = shared
        self.predict = Runtime()

        # self.serial_connection = None

        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)

    def send_target(self, target: RobotXY) -> None:
        if not self.ser.is_open:
            return

        target_x = target.x
        target_y = target.y

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
        if not self.ser.is_open:
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

    def run(self) -> None:
        while True:
            fb = self.read_feedback()

            if fb is not None:
                with self.shared.lock:
                    self.shared.striker = fb
                    ba = self.shared.ball
                st = fb
            else:
                with self.shared.lock:
                    st = self.shared.striker
                    ba = self.shared.ball

            resp = self.predict.predict(ba, st)

            self.send_target(resp)

    def stop(self) -> None:
        if self.ser.is_open:
            try:
                self.ser.close()
                print(f"MCU Serial Connection closed port {self.port}.")
            except Exception as e:
                print(f"Error closing serial port {self.port}: {e}")
