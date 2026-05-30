from __future__ import annotations

import time
import uuid
from pathlib import Path

import cv2
import numpy as np

from backend import config
from backend.database import add_violation, find_owner_by_plate, update_notification_status
from backend.notification import NotificationService
from backend.plate_recognition import PlateRecognizer
from backend.tracking import TrackResult, VehicleTracker


VEHICLE_CLASSES = {"motorcycle", "bicycle"}
PERSON_CLASS = "person"
PHONE_CLASS = "cell phone"


class TrafficViolationDetector:
    """Runs YOLO detection, DeepSORT tracking, violation logic, and image capture."""

    def __init__(self) -> None:
        self.model_status: dict[str, str] = {}
        self.vehicle_model = self._load_yolo(config.VEHICLE_MODEL)
        self.helmet_model = self._load_yolo(config.HELMET_MODEL)
        self.tracker = VehicleTracker()
        self.notifications = NotificationService()
        self.plates = PlateRecognizer()
        self.last_violation_by_vehicle: dict[str, float] = {}
        config.CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_yolo(self, path: Path):
        try:
            from ultralytics import YOLO

            if not path.exists() and path.name != "yolov8n.pt":
                self.model_status[path.name] = "missing"
                return None
            self.model_status[path.name] = "loaded"
            return YOLO(str(path))
        except Exception:
            self.model_status[path.name] = "error"
            return None

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, list[dict]]:
        vehicle_detections, person_detections, phone_detections = self._detect_scene(frame)
        tracks = self.tracker.update(vehicle_detections, frame)
        violations: list[dict] = []

        for track in tracks:
            self._draw_track(frame, track)
            if track.class_name not in VEHICLE_CLASSES:
                continue

            if self._has_recent_violation(track.track_id, "helmet") is False and self._helmet_missing(frame, track.bbox):
                violations.append(self._record_violation(frame, track, "helmet"))

            if self._has_recent_violation(track.track_id, "triple_seat") is False and self._has_triple_seat(track.bbox, person_detections):
                violations.append(self._record_violation(frame, track, "triple_seat"))

            if self._has_recent_violation(track.track_id, "phone") is False and self._is_phone_use(track.bbox, person_detections, phone_detections):
                violations.append(self._record_violation(frame, track, "phone"))

        self._draw_status(frame)
        return frame, violations

    def _detect_scene(self, frame: np.ndarray) -> tuple[list[dict], list[dict], list[dict]]:
        if self.vehicle_model is None:
            return [], [], []

        results = self.vehicle_model.predict(
            frame,
            conf=config.CONFIDENCE_THRESHOLD,
            verbose=False,
        )

        vehicles: list[dict] = []
        persons: list[dict] = []
        phones: list[dict] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = str(names[class_id]).lower()
                x1, y1, x2, y2 = [int(value) for value in box.xyxy[0]]
                detection = {
                    "bbox": (x1, y1, x2, y2),
                    "confidence": float(box.conf[0]),
                    "class_name": class_name,
                }

                if class_name in VEHICLE_CLASSES:
                    vehicles.append(detection)
                elif class_name == PERSON_CLASS:
                    persons.append(detection)
                elif class_name == PHONE_CLASS:
                    phones.append(detection)

        for phone in phones:
            x1, y1, x2, y2 = phone["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                frame,
                "Phone",
                (x1, max(y1 - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 255),
                2,
            )

        for person in persons:
            x1, y1, x2, y2 = person["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 174, 0), 1)
        return vehicles, persons, phones

    def _has_triple_seat(self, vehicle_box: tuple[int, int, int, int], persons: list[dict]) -> bool:
        x1, y1, x2, y2 = vehicle_box
        count = 0
        for person in persons:
            px1, py1, px2, py2 = person["bbox"]
            center_x = (px1 + px2) // 2
            center_y = (py1 + py2) // 2
            if x1 <= center_x <= x2 and y1 <= center_y <= y2:
                count += 1
        return count >= 3

    def _is_phone_use(
        self,
        vehicle_box: tuple[int, int, int, int],
        persons: list[dict],
        phones: list[dict],
    ) -> bool:
        rider_persons = [person for person in persons if self._is_person_in_vehicle(person["bbox"], vehicle_box)]
        if not rider_persons:
            return False

        for phone in phones:
            if any(self._boxes_intersect(phone["bbox"], person["bbox"]) for person in rider_persons):
                return True
            if self._boxes_intersect(phone["bbox"], vehicle_box):
                return True
        return False

    def _is_person_in_vehicle(self, person_box: tuple[int, int, int, int], vehicle_box: tuple[int, int, int, int]) -> bool:
        px1, py1, px2, py2 = person_box
        x1, y1, x2, y2 = vehicle_box
        center_x = (px1 + px2) // 2
        center_y = (py1 + py2) // 2
        return x1 <= center_x <= x2 and y1 <= center_y <= y2

    def _boxes_intersect(
        self,
        box_a: tuple[int, int, int, int],
        box_b: tuple[int, int, int, int],
    ) -> bool:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    def _detect_vehicles(self, frame: np.ndarray) -> list[dict]:
        if self.vehicle_model is None:
            return []

        results = self.vehicle_model.predict(
            frame,
            conf=config.CONFIDENCE_THRESHOLD,
            verbose=False,
        )
        detections: list[dict] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = str(names[class_id])
                if class_name not in VEHICLE_CLASSES:
                    continue
                x1, y1, x2, y2 = [int(value) for value in box.xyxy[0]]
                detections.append(
                    {
                        "bbox": (x1, y1, x2, y2),
                        "confidence": float(box.conf[0]),
                        "class_name": class_name,
                    }
                )
        return detections

    def _helmet_missing(self, frame: np.ndarray, bbox: tuple[int, int, int, int]) -> bool:
        if self.helmet_model is None:
            return False

        x1, y1, x2, y2 = bbox
        rider_region = frame[max(y1, 0) : max(y2, 0), max(x1, 0) : max(x2, 0)]
        if rider_region.size == 0:
            return False

        results = self.helmet_model.predict(
            rider_region,
            conf=config.CONFIDENCE_THRESHOLD,
            verbose=False,
        )
        labels: set[str] = set()
        for result in results:
            for box in result.boxes:
                labels.add(str(result.names[int(box.cls[0])]).lower())

        normalized_labels = {label.replace(" ", "_").replace("-", "_") for label in labels}
        no_helmet_labels = {"no_helmet", "without_helmet", "withouthelmet", "nohelmet"}
        helmet_labels = {"helmet", "with_helmet", "withhelmet"}
        return bool(normalized_labels & no_helmet_labels) or (
            bool(normalized_labels) and not bool(normalized_labels & helmet_labels)
        )

    def _record_violation(self, frame: np.ndarray, track: TrackResult, violation_type: str) -> dict:
        self.last_violation_by_vehicle[f"{track.track_id}:{violation_type}"] = time.time()
        violation_id = f"VIO-{uuid.uuid4().hex[:10].upper()}"
        image_path = self._save_vehicle_image(frame, track.bbox, violation_id)
        plate_number = self.plates.read_plate(frame)
        owner = find_owner_by_plate(plate_number)
        owner_phone = owner["phone_number"] if owner else None
        violation = add_violation(
            violation_id=violation_id,
            vehicle_id=track.track_id,
            violation_type=violation_type,
            image_path=image_path,
            plate_number=plate_number,
            owner_phone=owner_phone,
        )

        try:
            status = self.notifications.send_violation_sms(owner_phone or config.VIOLATOR_PHONE, violation)
        except Exception:
            status = "failed"
        update_notification_status(violation_id, status)
        violation["notification_status"] = status
        return violation

    def _save_vehicle_image(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        violation_id: str,
    ) -> str:
        x1, y1, x2, y2 = bbox
        crop = frame[max(y1, 0) : max(y2, 0), max(x1, 0) : max(x2, 0)]
        if crop.size == 0:
            crop = frame
        image_path = config.CAPTURE_DIR / f"{violation_id}.jpg"
        cv2.imwrite(str(image_path), crop)
        return str(image_path.relative_to(config.ROOT_DIR))

    def _has_recent_violation(self, vehicle_id: str, violation_type: str) -> bool:
        key = f"{vehicle_id}:{violation_type}"
        last_seen = self.last_violation_by_vehicle.get(key, 0)
        return time.time() - last_seen < config.VIOLATION_COOLDOWN_SECONDS

    def _draw_track(self, frame: np.ndarray, track: TrackResult) -> None:
        x1, y1, x2, y2 = track.bbox
        color = (0, 180, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            f"ID {track.track_id} {track.class_name}",
            (x1, max(y1 - 8, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    def _draw_status(self, frame: np.ndarray) -> None:
        status = "Helmet, phone & seat detection active"
        cv2.rectangle(frame, (12, 12), (490, 48), (20, 20, 20), -1)
        cv2.putText(frame, status, (24, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
