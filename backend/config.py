import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: str) -> Path:
    value = os.getenv(name, default)
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DATABASE_PATH = _path_from_env("DATABASE_PATH", "backend/traffic_violations.db")
CAPTURE_DIR = _path_from_env("CAPTURE_DIR", "captured_violations")

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "0")
VEHICLE_MODEL = _path_from_env("VEHICLE_MODEL", "models/yolov8n.pt")
HELMET_MODEL = _path_from_env("HELMET_MODEL", "models/helmet_yolov8.pt")
SIGNAL_MODEL = _path_from_env("SIGNAL_MODEL", "models/signal_yolov8.pt")

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.35"))
VIOLATION_COOLDOWN_SECONDS = int(os.getenv("VIOLATION_COOLDOWN_SECONDS", "8"))

SENSOR_MODE = os.getenv("SENSOR_MODE", "serial").lower()
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", "9600"))

NOTIFICATION_PROVIDER = os.getenv("NOTIFICATION_PROVIDER", "none").lower()
VIOLATOR_PHONE = os.getenv("VIOLATOR_PHONE", "+910000000000")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")
FAST2SMS_SENDER_ID = os.getenv("FAST2SMS_SENDER_ID", "FSTSMS")

TEXTBELT_API_KEY = os.getenv("TEXTBELT_API_KEY", "textbelt")
