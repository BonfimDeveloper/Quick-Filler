import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"

MAX_UPLOAD_SIZE = 10 * 1024 * 1024

DATABASE_PATH = BASE_DIR / "quick_filler.db"

TESSERACT_CMD = os.getenv("TESSERACT_CMD")
TESSDATA_DIR = os.getenv("TESSDATA_DIR")
