import cv2
import numpy as np
from pathlib import Path

out_path = Path(__file__).resolve().parent.parent / 'frontend' / 'demo.mp4'
width, height = 960, 540
fps = 20
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
if not writer.isOpened():
    raise SystemExit('Failed to open VideoWriter')

for i in range(fps * 6):
    frame = np.full((height, width, 3), 32, dtype=np.uint8)
    x = 80 + (i * 8) % (width - 260)
    y = 300
    cv2.rectangle(frame, (x, y), (x + 220, y + 90), (0, 120, 200), -1)
    cv2.rectangle(frame, (x + 20, y + 20), (x + 40, y + 40), (20, 20, 20), -1)
    cv2.rectangle(frame, (x + 160, y + 20), (x + 180, y + 40), (20, 20, 20), -1)
    cv2.putText(frame, 'TRAFFIC VIOLATION', (42, 68), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, 'Demo feed only', (42, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (215, 215, 215), 1, cv2.LINE_AA)
    cv2.circle(frame, (width - 110, 100), 28, (0, 90, 255), -1)
    cv2.circle(frame, (width - 110, 180), 28, (0, 200, 80), -1)
    cv2.rectangle(frame, (62, 262), (width - 62, 286), (255, 255, 255), -1)
    writer.write(frame)

writer.release()
print('Created', out_path)
