<<<<<<< HEAD
# Smart Traffic Violation Detection and Notification System

A full-stack AI-powered traffic monitoring project built with Python, YOLOv8, OpenCV, DeepSORT, FastAPI, SQLite, and SMS notifications.

The system detects two-wheelers, tracks them across frames, checks for helmet violations, detects phone use by riders, flags triple-seat riders, captures evidence images, stores violation records, and displays live analytics in a responsive dashboard.

## Features

- YOLOv8 vehicle detection using Ultralytics
- Helmet violation detection with a custom YOLOv8 model
- Phone-in-hand violation detection for riders using cell phone object recognition
- Triple-seat detection by counting riders inside a motorcycle/bicycle bounding box
- OpenCV webcam, IP camera, or sample video processing
- DeepSORT vehicle tracking
- SQLite violation database
- Unique violation ID generation
- Captured vehicle image evidence
- Twilio or Fast2SMS SMS notification support
- FastAPI backend with Swagger API documentation
- Responsive HTML/CSS/JavaScript dashboard
- UI preview image: `docs/ui_overview.png`

## Folder Structure

```text
megaproject/
  backend/
    __init__.py
    config.py
    database.py
    detection.py
    main.py
    notification.py
    sensor.py
    tracking.py
  captured_violations/
  datasets/
  docs/
    architecture.md
    api.md
    er_diagram.md
    workflow.md
  frontend/
    app.js
    index.html
    styles.css
  hardware/
    arduino_ir_sensor.ino
  models/
  sample_videos/
  .env.example
  requirements.txt
  README.md
```

## Installation

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create your local environment file:

```bash
copy .env.example .env
```

4. Add model files:

```text
models/yolov8n.pt
models/helmet_yolov8.pt
```

`yolov8n.pt` can be downloaded automatically by Ultralytics when internet is available. The helmet model should be trained on your custom dataset and copied into the `models/` folder.

5. Optional: add a test video:

```text
sample_videos/test.mp4
```

Then set this in `.env`:

```text
CAMERA_SOURCE=sample_videos/test.mp4
```

Use `CAMERA_SOURCE=0` for webcam or an RTSP URL for an IP camera.

## Run

```bash
uvicorn backend.main:app --reload
```

Open:

- Dashboard: <http://127.0.0.1:8000>
- Swagger API docs: <http://127.0.0.1:8000/docs>
- ReDoc API docs: <http://127.0.0.1:8000/redoc>

## SMS Setup

While SMS credentials are pending:

```text
NOTIFICATION_PROVIDER=none
```

For the free Textbelt test option:

```text
NOTIFICATION_PROVIDER=textbelt
TEXTBELT_API_KEY=textbelt
VIOLATOR_PHONE=+919999999999
```

The free Textbelt key is limited and should be used for testing only.

For Twilio:

```text
NOTIFICATION_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890
VIOLATOR_PHONE=+919999999999
```

For Fast2SMS:

```text
NOTIFICATION_PROVIDER=fast2sms
FAST2SMS_API_KEY=your_api_key
VIOLATOR_PHONE=9999999999
```

## API Documentation

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Dashboard |
| GET | `/video-feed` | MJPEG live camera stream |
| GET | `/api/stats` | Violation totals |
| GET | `/api/violations?limit=25` | Recent violation records |
| GET | `/api/violations/export.csv` | Export violation records as CSV |
| GET | `/api/docs` | API links |
| GET | `/health` | Health check |

## Dataset Notes

Place datasets under `datasets/` using YOLO format:

```text
datasets/
  helmet/
    images/train/
    images/val/
    labels/train/
    labels/val/
  traffic_signal/
    images/train/
    images/val/
    labels/train/
    labels/val/
```

Recommended classes:

- Helmet model: `helmet`, `no_helmet`
Train with Ultralytics:

```bash
yolo detect train data=datasets/helmet/data.yaml model=yolov8n.pt epochs=50 imgsz=640
```

Copy the best weights into `models/`.

## Future Scope

- Automatic license plate recognition
- Owner lookup through an RTO-style registry
- Email and WhatsApp notifications
- Multi-camera support with camera-specific zones
- Admin login and role-based access
- Cloud storage for violation evidence
- Edge deployment on NVIDIA Jetson or Raspberry Pi
- Model retraining workflow from dashboard feedback

More details are available in the `docs/` folder.
=======
# megaproject
>>>>>>> 24f7898ef2c7de5ae494e2776f8302e0e1e7df6e
