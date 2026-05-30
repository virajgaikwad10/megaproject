from __future__ import annotations

import asyncio
import base64
import csv
import io
import threading
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import config
from backend.database import (
    get_connection,
    get_stats,
    initialize_database,
    list_owners,
    list_recent_violations,
    upsert_owner,
)
from backend.detection import TrafficViolationDetector
from backend.notification import NotificationService

app = FastAPI(
    title="Smart Traffic Violation Detection and Notification System",
    description="YOLOv8, OpenCV, DeepSORT, SQLite, and SMS powered traffic violation monitoring.",
    version="1.0.0",
)

frontend_dir = config.ROOT_DIR / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
app.mount("/captured_violations", StaticFiles(directory=config.CAPTURE_DIR), name="captures")

initialize_database()
detector = TrafficViolationDetector()
notifications = NotificationService()
latest_jpeg: bytes | None = None
camera_lock = threading.Lock()
camera_running = False
camera_status = "starting"


class BrowserFrame(BaseModel):
    image: str


class OwnerRegistration(BaseModel):
    plate_number: str
    owner_name: str
    phone_number: str


def parse_camera_source():
    if config.CAMERA_SOURCE.isdigit():
        return int(config.CAMERA_SOURCE)
    return str(config.ROOT_DIR / config.CAMERA_SOURCE) if not config.CAMERA_SOURCE.startswith(("rtsp://", "http://", "https://")) else config.CAMERA_SOURCE


def open_camera_source():
    source = parse_camera_source()
    if isinstance(source, int):
        for index in [source, 0, 1, 2, 3, 4, 5]:
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                capture = cv2.VideoCapture(index, backend)
                if capture.isOpened():
                    return capture
                capture.release()
        return cv2.VideoCapture(source)
    return cv2.VideoCapture(source)


def status_frame(message: str, detail: str) -> bytes | None:
    frame = np.zeros((540, 960, 3), dtype=np.uint8)
    cv2.rectangle(frame, (0, 0), (960, 540), (14, 24, 36), -1)
    cv2.putText(frame, message, (70, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(frame, detail, (70, 295), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (130, 190, 255), 2)
    success, buffer = cv2.imencode(".jpg", frame)
    return buffer.tobytes() if success else None


def camera_worker() -> None:
    global latest_jpeg, camera_running, camera_status
    camera_running = True
    camera_status = "starting"
    capture = open_camera_source()

    if not capture.isOpened():
        camera_status = "waiting_for_browser_camera"
        with camera_lock:
            latest_jpeg = status_frame("Browser camera mode", "Click Start Camera on dashboard")
        camera_running = False
        return

    camera_status = "running"
    while camera_running:
        ok, frame = capture.read()
        if not ok:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = capture.read()
            if not ok:
                camera_status = "frame_read_failed"
                with camera_lock:
                    latest_jpeg = status_frame("Frame read failed", "Check camera, stream, or test video")
                break

        processed_frame, _ = detector.process_frame(frame)
        success, buffer = cv2.imencode(".jpg", processed_frame)
        if success:
            with camera_lock:
                latest_jpeg = buffer.tobytes()

    capture.release()
    camera_running = False


@app.on_event("startup")
def start_camera() -> None:
    thread = threading.Thread(target=camera_worker, daemon=True)
    thread.start()


@app.on_event("shutdown")
def stop_camera() -> None:
    global camera_running
    camera_running = False


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/stats")
def stats() -> dict[str, int]:
    return get_stats()


@app.get("/api/status")
def status() -> dict[str, str]:
    return {
        "camera": camera_status,
        "notifications": config.NOTIFICATION_PROVIDER,
        "vehicle_model": detector.model_status.get(config.VEHICLE_MODEL.name, "unknown"),
        "helmet_model": detector.model_status.get(config.HELMET_MODEL.name, "unknown"),
    }


@app.post("/api/test-sms")
def test_sms() -> dict:
    return notifications.send_test_sms(config.VIOLATOR_PHONE)


@app.post("/api/video-source")
async def upload_video_source(video: UploadFile = File(...)) -> dict[str, str]:
    sample_dir = config.ROOT_DIR / "sample_videos"
    sample_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(video.filename or "uploaded.mp4").suffix or ".mp4"
    target = sample_dir / f"uploaded_source{suffix}"
    with target.open("wb") as file:
        file.write(await video.read())
    return {
        "message": "Video uploaded. Set CAMERA_SOURCE to this path and restart the server.",
        "camera_source": str(target.relative_to(config.ROOT_DIR)).replace("\\", "/"),
    }


@app.post("/api/browser-frame")
def browser_frame(payload: BrowserFrame) -> dict[str, str | int]:
    global latest_jpeg, camera_status
    image_data = payload.image.split(",", 1)[-1]
    frame_bytes = base64.b64decode(image_data)
    array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="invalid frame")

    processed_frame, violations = detector.process_frame(frame)
    success, buffer = cv2.imencode(".jpg", processed_frame)
    if success:
        with camera_lock:
            latest_jpeg = buffer.tobytes()
    camera_status = "browser_camera"
    return {"status": "ok", "violations": len(violations)}


@app.get("/api/violations")
def violations(limit: int = 25) -> list[dict]:
    return list_recent_violations(limit)


@app.get("/api/owners")
def owners() -> list[dict[str, str]]:
    return list_owners()


@app.post("/api/owners")
def save_owner(owner: OwnerRegistration) -> dict[str, str]:
    return upsert_owner(owner.plate_number, owner.owner_name, owner.phone_number)


@app.get("/api/violations/export.csv")
def export_violations() -> Response:
    records = list_recent_violations(1000)
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "violation_id",
            "vehicle_id",
            "plate_number",
            "owner_phone",
            "violation_type",
            "date_time",
            "image_path",
            "notification_status",
        ],
    )
    writer.writeheader()
    writer.writerows(records)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=traffic_violations.csv"},
    )


@app.get("/api/violations/latest")
def latest_violation() -> dict:
    recent = list_recent_violations(1)
    if not recent:
        raise HTTPException(status_code=404, detail="no violations found")
    return recent[0]


@app.get("/api/violations/{violation_id}/image")
def violation_image(violation_id: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT image_path FROM violations WHERE violation_id = ?",
            (violation_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="violation not found")
    img_file = config.ROOT_DIR / row[0]
    if not img_file.exists():
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(img_file)


@app.get("/api/docs")
def api_docs() -> dict:
    return {
        "openapi": "/openapi.json",
        "swagger": "/docs",
        "redoc": "/redoc",
        "endpoints": [
            "/api/status",
            "/api/test-sms",
            "/api/video-source",
            "/api/browser-frame",
            "/api/owners",
            "/api/stats",
            "/api/violations",
            "/api/violations/export.csv",
            "/api/violations/latest",
            "/api/violations/{violation_id}/image",
            "/video-feed",
        ],
    }


@app.get("/video-feed")
async def video_feed() -> StreamingResponse:
    async def frame_stream():
        while True:
            with camera_lock:
                frame = latest_jpeg
            if frame:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            await asyncio.sleep(0.04)

    return StreamingResponse(frame_stream(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=config.APP_HOST, port=config.APP_PORT, reload=True)
