from __future__ import annotations

import re

import cv2
import numpy as np


class PlateRecognizer:
    """Extract a likely Indian number plate string using optional OCR."""

    def __init__(self) -> None:
        try:
            import pytesseract

            self._ocr = pytesseract
        except Exception:
            self._ocr = None

    def read_plate(self, frame: np.ndarray) -> str | None:
        if self._ocr is None:
            return None

        candidates = self._plate_candidates(frame)
        candidates.append(frame)
        for candidate in candidates:
            text = self._ocr.image_to_string(
                candidate,
                config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            )
            plate = self._clean_plate(text)
            if plate:
                return plate
        return None

    def _plate_candidates(self, frame: np.ndarray) -> list[np.ndarray]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        edges = cv2.Canny(gray, 30, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[np.ndarray] = []
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:20]:
            x, y, w, h = cv2.boundingRect(contour)
            if w < 80 or h < 20:
                continue
            ratio = w / float(h)
            if 2.0 <= ratio <= 6.5:
                crop = frame[max(y - 4, 0) : y + h + 4, max(x - 4, 0) : x + w + 4]
                if crop.size:
                    candidates.append(crop)
        return candidates

    def _clean_plate(self, text: str) -> str | None:
        compact = re.sub(r"[^A-Z0-9]", "", text.upper())
        match = re.search(r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4}", compact)
        if match:
            return match.group(0)
        return compact if 6 <= len(compact) <= 12 else None
