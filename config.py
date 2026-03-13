from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATABASE_PATH = INSTANCE_DIR / "lan_fileserver.db"


class Config:
    SECRET_KEY = "change-me-in-production"
    DATABASE = DATABASE_PATH
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {
        "csv",
        "gif",
        "jpeg",
        "jpg",
        "json",
        "log",
        "pcap",
        "pcapng",
        "pdf",
        "png",
        "txt",
    }
