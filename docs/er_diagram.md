# ER Diagram

```mermaid
erDiagram
    VIOLATIONS {
        integer id PK
        string violation_id UK
        string vehicle_id
        string violation_type
        string date_time
        string image_path
        string notification_status
    }
```

## Table Description

`violations` stores every detected traffic violation with the tracked vehicle ID, violation category, evidence image path, timestamp, and SMS notification status.
