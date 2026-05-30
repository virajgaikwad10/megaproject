from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrackResult:
    track_id: str
    bbox: tuple[int, int, int, int]
    class_name: str
    confidence: float


class VehicleTracker:
    """Wrap DeepSORT and provide a small fallback when the package is unavailable."""

    def __init__(self) -> None:
        self._fallback_id = 0
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort

            self._tracker = DeepSort(max_age=20, n_init=2)
        except Exception:
            self._tracker = None

    def update(self, detections: list[dict], frame) -> list[TrackResult]:
        if self._tracker is None:
            return self._fallback_tracks(detections)

        deep_sort_inputs = []
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            width = x2 - x1
            height = y2 - y1
            deep_sort_inputs.append(
                ([x1, y1, width, height], detection["confidence"], detection["class_name"])
            )

        tracks = self._tracker.update_tracks(deep_sort_inputs, frame=frame)
        results: list[TrackResult] = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            x1, y1, x2, y2 = [int(value) for value in track.to_ltrb()]
            results.append(
                TrackResult(
                    track_id=str(track.track_id),
                    bbox=(x1, y1, x2, y2),
                    class_name=str(track.get_det_class() or "vehicle"),
                    confidence=1.0,
                )
            )
        return results

    def _fallback_tracks(self, detections: list[dict]) -> list[TrackResult]:
        # Beginner-friendly fallback: every current detection gets a simple temporary ID.
        results: list[TrackResult] = []
        for detection in detections:
            self._fallback_id += 1
            results.append(
                TrackResult(
                    track_id=str(self._fallback_id),
                    bbox=detection["bbox"],
                    class_name=detection["class_name"],
                    confidence=detection["confidence"],
                )
            )
        return results
