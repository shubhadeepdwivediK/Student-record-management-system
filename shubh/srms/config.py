"""Central configuration. Paths can be overridden with environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SRMS_DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.environ.get("SRMS_DB_PATH", DATA_DIR / "srms.db"))
LOG_DIR = Path(os.environ.get("SRMS_LOG_DIR", BASE_DIR / "logs"))
EXPORT_DIR = Path(os.environ.get("SRMS_EXPORT_DIR", DATA_DIR / "exports"))

MAX_LOGIN_ATTEMPTS = 3
PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_LENGTH = 8
