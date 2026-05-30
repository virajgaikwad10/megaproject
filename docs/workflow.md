# Workflow Explanation

1. OpenCV reads frames from a webcam, IP camera, or sample video.
2. YOLOv8 detects vehicles in each frame.
3. DeepSORT assigns a stable tracking ID to each detected vehicle.
4. The helmet model checks motorcycle or bicycle riders for missing helmets.
5. If a helmet violation is detected, the system creates a unique violation ID.
6. The vehicle image is captured and saved in `captured_violations/`.
7. SQLite stores the vehicle ID, violation type, timestamp, image path, and notification status.
8. Textbelt, Twilio, or Fast2SMS sends an SMS alert when configured.
9. The FastAPI dashboard displays the live feed, counts, and recent alerts.

## Violation Rules

- Helmet violation: tracked motorcycle or bicycle rider has `no_helmet`, or the custom model reports a rider class without a helmet.
