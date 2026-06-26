from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BACKEND_ROOT / "outputs"
UPLOAD_DIR = OUTPUT_DIR / "uploads"
GENERATED_DIR = OUTPUT_DIR / "generated"
RETOUCHED_DIR = OUTPUT_DIR / "retouched"

for directory in (OUTPUT_DIR, UPLOAD_DIR, GENERATED_DIR, RETOUCHED_DIR):
    directory.mkdir(parents=True, exist_ok=True)
