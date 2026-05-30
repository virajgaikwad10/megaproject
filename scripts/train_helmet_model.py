from pathlib import Path
from shutil import copy2

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
DATA_YAML = ROOT / "datasets" / "helmet" / "data.yaml"
OUTPUT_MODEL = ROOT / "models" / "helmet_yolov8.pt"


def main() -> None:
    if not DATA_YAML.exists():
        raise FileNotFoundError(f"Dataset config not found: {DATA_YAML}")

    model = YOLO(str(ROOT / "models" / "yolov8n.pt"))
    result = model.train(
        data=str(DATA_YAML),
        epochs=50,
        imgsz=640,
        batch=8,
        project=str(ROOT / "runs"),
        name="helmet_train",
        exist_ok=True,
    )

    best_model = Path(result.save_dir) / "weights" / "best.pt"
    if not best_model.exists():
        raise FileNotFoundError(f"Training finished but best.pt was not found: {best_model}")

    OUTPUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    copy2(best_model, OUTPUT_MODEL)
    print(f"Saved trained helmet model to {OUTPUT_MODEL}")


if __name__ == "__main__":
    main()
