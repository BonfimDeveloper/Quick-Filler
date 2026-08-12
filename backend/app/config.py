from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"

MAX_UPLOAD_SIZE = 10 * 1024 * 1024