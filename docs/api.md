# API Documentation

FastAPI automatically exposes interactive documentation:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Endpoints

### `GET /`

Returns the dashboard HTML page.

### `GET /video-feed`

Streams the processed camera feed as MJPEG.

### `GET /api/stats`

Returns violation totals.

Response:

```json
{
  "total": 12,
  "helmet": 7,
  "red_light": 5
}
```

### `GET /api/violations?limit=25`

Returns recent violation records.

Response:

```json
[
  {
    "violation_id": "VIO-ABC123",
    "vehicle_id": "8",
    "violation_type": "helmet",
    "date_time": "2026-05-26T13:15:00",
    "image_path": "captured_violations/VIO-ABC123.jpg",
    "notification_status": "sent"
  }
]
```

### `GET /api/violations/export.csv`

Downloads recent violation records as a CSV file.

### `GET /api/docs`

Returns links to API documentation resources.

### `GET /health`

Returns:

```json
{
  "status": "ok"
}
```
