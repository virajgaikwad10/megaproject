# System Architecture

```mermaid
flowchart LR
    Camera[Webcam / IP Camera / Test Video] --> OpenCV[OpenCV Frame Processor]
    OpenCV --> YOLO[YOLOv8 Detection]
    YOLO --> Tracker[DeepSORT Tracking]
    Tracker --> Logic
    Logic --> Capture[Capture Vehicle Image]
    Logic --> DB[(SQLite Database)]
    Logic --> SMS[Twilio / Fast2SMS]
    DB --> API[FastAPI Backend]
    Capture --> API
    API --> Dashboard[Responsive Dashboard]
```

## Components

- `backend/detection.py`: YOLOv8 inference, violation rules, image capture, and frame annotation.
- `backend/tracking.py`: DeepSORT vehicle tracking.
- `backend/database.py`: SQLite table creation and query helpers.
- `backend/notification.py`: Twilio and Fast2SMS SMS adapters.
- `backend/main.py`: FastAPI app, video streaming, API routes, and dashboard serving.
- `frontend/`: Live dashboard UI.
