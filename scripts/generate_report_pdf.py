from pathlib import Path
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

root = Path(__file__).resolve().parents[1]
report_path = root / "Traffic_Violation_Report.pdf"

c = canvas.Canvas(str(report_path), pagesize=A4)
width, height = A4
margin = 25 * mm
x = margin
y = height - margin
line_height = 11 * mm

header = "Smart Traffic Violation Detection Report"
c.setFont("Helvetica-Bold", 18)
c.drawString(x, y, header)
y -= 2 * line_height

c.setFont("Helvetica", 11)
lines = [
    "Project: Traffic Violation Detection System",
    "Date: May 30, 2026",
    "",
    "Implemented features:",
    "- Helmet violation detection for two-wheelers",
    "- Phone-in-hand rider detection",
    "- Triple-seat rider detection",
    "- Live YOLOv8 processing and DeepSORT tracking",
    "- Violations saved with evidence images",
    "- Owner SMS notification via number plate registry",
    "",
    "Updated dashboard:",
    "- Added Phone Violations and Triple Seat Violations metrics",
    "- Live processed feed and latest violation card",
    "",
    "How to run:",
    "1. Activate .venv",
    "2. Install dependencies: pip install -r requirements.txt",
    "3. Start server: uvicorn backend.main:app --host 0.0.0.0 --port 8000",
    "4. Open http://127.0.0.1:8000",
    "",
    "Important files:",
    "- backend/detection.py",
    "- backend/database.py",
    "- frontend/index.html",
    "- frontend/app.js",
    "- frontend/styles.css",
    "- docs/ui_overview.png",
    "- Traffic_Violation_Report.pdf",
    "",
    "Notes:",
    "The system now detects helmet, phone use, and triple-seat violations in real time from the camera feed.",
    "Violations are stored in SQLite and shown on the dashboard with image evidence.",
]

for line in lines:
    for wrapped in textwrap.wrap(line, width=95):
        c.drawString(x, y, wrapped)
        y -= 8 * mm
        if y < margin + 100 * mm:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - margin
    y -= 4 * mm

ui_path = root / "docs" / "ui_overview.png"
if ui_path.exists():
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, height - margin, "UI Overview Screenshot")
    try:
        image = ImageReader(str(ui_path))
        image_width = width - 2 * margin
        image_height = image_width * 0.65
        c.drawImage(image, x, height - margin - image_height - 20 * mm, width=image_width, height=image_height, preserveAspectRatio=True, anchor="c")
    except Exception:
        c.setFont("Helvetica", 12)
        c.drawString(x, height - margin - 14 * mm, "Unable to include screenshot image.")

c.save()
print(f"Created report at: {report_path}")
