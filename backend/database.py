import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from backend import config


def initialize_database() -> None:
    """Create the SQLite database and table if they do not exist yet."""
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(config.DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                violation_id TEXT UNIQUE NOT NULL,
                vehicle_id TEXT NOT NULL,
                plate_number TEXT,
                owner_phone TEXT,
                violation_type TEXT NOT NULL,
                date_time TEXT NOT NULL,
                image_path TEXT NOT NULL,
                notification_status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_owners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT UNIQUE NOT NULL,
                owner_name TEXT NOT NULL,
                phone_number TEXT NOT NULL
            )
            """
        )
        for column, definition in {
            "plate_number": "TEXT",
            "owner_phone": "TEXT",
        }.items():
            columns = connection.execute("PRAGMA table_info(violations)").fetchall()
            if column not in {row[1] for row in columns}:
                connection.execute(f"ALTER TABLE violations ADD COLUMN {column} {definition}")
        connection.commit()


@contextmanager
def get_connection():
    connection = sqlite3.connect(config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def add_violation(
    violation_id: str,
    vehicle_id: str,
    violation_type: str,
    image_path: str | Path,
    plate_number: str | None = None,
    owner_phone: str | None = None,
    notification_status: str = "pending",
) -> dict[str, Any]:
    date_time = datetime.now().isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO violations (
                violation_id, vehicle_id, plate_number, owner_phone, violation_type, date_time, image_path, notification_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                violation_id,
                vehicle_id,
                plate_number,
                owner_phone,
                violation_type,
                date_time,
                str(image_path),
                notification_status,
            ),
        )
    return {
        "violation_id": violation_id,
        "vehicle_id": vehicle_id,
        "plate_number": plate_number,
        "owner_phone": owner_phone,
        "violation_type": violation_type,
        "date_time": date_time,
        "image_path": str(image_path),
        "notification_status": notification_status,
    }


def update_notification_status(violation_id: str, status: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE violations SET notification_status = ? WHERE violation_id = ?",
            (status, violation_id),
        )


def list_recent_violations(limit: int = 25) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT violation_id, vehicle_id, violation_type, date_time, image_path, notification_status
                , plate_number, owner_phone
            FROM violations
            ORDER BY date_time DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def normalize_plate(plate_number: str) -> str:
    return "".join(character for character in plate_number.upper() if character.isalnum())


def upsert_owner(plate_number: str, owner_name: str, phone_number: str) -> dict[str, str]:
    plate = normalize_plate(plate_number)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO vehicle_owners (plate_number, owner_name, phone_number)
            VALUES (?, ?, ?)
            ON CONFLICT(plate_number) DO UPDATE SET
                owner_name = excluded.owner_name,
                phone_number = excluded.phone_number
            """,
            (plate, owner_name, phone_number),
        )
    return {"plate_number": plate, "owner_name": owner_name, "phone_number": phone_number}


def find_owner_by_plate(plate_number: str | None) -> dict[str, str] | None:
    if not plate_number:
        return None
    plate = normalize_plate(plate_number)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT plate_number, owner_name, phone_number
            FROM vehicle_owners
            WHERE plate_number = ?
            """,
            (plate,),
        ).fetchone()
    return dict(row) if row else None


def list_owners() -> list[dict[str, str]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT plate_number, owner_name, phone_number FROM vehicle_owners ORDER BY plate_number"
        ).fetchall()
    return [dict(row) for row in rows]


def get_stats() -> dict[str, int]:
    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
        helmet = connection.execute(
            "SELECT COUNT(*) FROM violations WHERE violation_type = 'helmet'"
        ).fetchone()[0]
        phone = connection.execute(
            "SELECT COUNT(*) FROM violations WHERE violation_type = 'phone'"
        ).fetchone()[0]
        triple_seat = connection.execute(
            "SELECT COUNT(*) FROM violations WHERE violation_type = 'triple_seat'"
        ).fetchone()[0]
    return {
        "total": total,
        "helmet": helmet,
        "phone": phone,
        "triple_seat": triple_seat,
    }
