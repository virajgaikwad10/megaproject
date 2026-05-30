from __future__ import annotations

from backend import config


class LineCrossingSensor:
    """Read an IR line-crossing signal from serial hardware."""

    def __init__(self) -> None:
        self.mode = config.SENSOR_MODE
        self._serial = None

        if self.mode == "serial":
            import serial

            self._serial = serial.Serial(
                config.SERIAL_PORT,
                config.SERIAL_BAUDRATE,
                timeout=0.05,
            )
        elif self.mode != "disabled":
            raise ValueError("SENSOR_MODE must be 'serial' or 'disabled' for the final product.")

    def is_line_crossed(self) -> bool:
        if self.mode == "serial" and self._serial:
            # Arduino/ESP32/Raspberry Pi should send "1" when the IR beam/line is crossed.
            value = self._serial.readline().decode(errors="ignore").strip()
            return value == "1"
        return False
