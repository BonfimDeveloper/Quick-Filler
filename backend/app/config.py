import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = Path(
    os.getenv("UPLOADS_DIR", BASE_DIR / "uploads")
)

MAX_UPLOAD_SIZE = int(
    os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
)

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", BASE_DIR / "quick_filler.db")
)

TESSERACT_CMD = os.getenv("TESSERACT_CMD")
TESSDATA_DIR = os.getenv("TESSDATA_DIR")

RETENTION_HOURS = int(
    os.getenv("RETENTION_HOURS", "24")
)
