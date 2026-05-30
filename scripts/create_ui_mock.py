import cv2
import numpy as np
from pathlib import Path

img = np.full((800, 1200, 3), 244, dtype=np.uint8)
cv2.rectangle(img, (30, 30), (1170, 110), (255, 255, 255), -1)
cv2.putText(img, 'Smart Traffic Violation Detection', (40, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (20, 30, 60), 2, cv2.LINE_AA)
cv2.putText(img, 'Live camera, helmet, phone and triple-seat alerts', (40, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (90, 100, 130), 1, cv2.LINE_AA)

colors = [(36, 90, 141), (138, 107, 40), (167, 61, 71), (108, 75, 141), (36, 97, 107)]
labels = ['Total Violations', 'Helmet Violations', 'Phone Violations', 'Triple Seat Violations', 'Owner Notifications']
values = ['0', '0', '0', '0', '0']
for i, (c, label, value) in enumerate(zip(colors, labels, values)):
    x = 40 + (i % 3) * 370
    y = 140 + (i // 3) * 140
    cv2.rectangle(img, (x, y), (x + 340, y + 110), c, -1)
    cv2.putText(img, label, (x + 15, y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(img, value, (x + 15, y + 85), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 255, 255), 2, cv2.LINE_AA)

cv2.rectangle(img, (40, 320), (590, 620), (220, 220, 220), -1)
cv2.putText(img, 'Live Camera Preview', (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 60, 60), 1, cv2.LINE_AA)
cv2.rectangle(img, (610, 320), (1160, 620), (220, 220, 220), -1)
cv2.putText(img, 'Processed Feed', (620, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 60, 60), 1, cv2.LINE_AA)
cv2.rectangle(img, (40, 650), (1160, 760), (255, 255, 255), -1)
cv2.putText(img, 'Latest Captured Violation', (50, 685), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 30, 60), 2, cv2.LINE_AA)
cv2.putText(img, 'Violation metadata and image shown here', (50, 720), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (90, 100, 130), 1, cv2.LINE_AA)

Path('docs').mkdir(exist_ok=True)
cv2.imwrite(str(Path('docs/ui_overview.png')), img)
