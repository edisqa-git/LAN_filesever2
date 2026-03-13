from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from db import execute, query_all, query_one


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def _unique_filename(original_name: str) -> str:
    safe_name = secure_filename(original_name)
    if not safe_name:
        raise ValueError("Invalid filename.")

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    candidate = upload_dir / safe_name
    stem = candidate.stem
    suffix = candidate.suffix
    idx = 1

    while candidate.exists():
        candidate = upload_dir / f"{stem}_{idx}{suffix}"
        idx += 1

    return candidate.name


def save_uploaded_file(file_storage, user_id: int) -> int:
    if file_storage.filename == "":
        raise ValueError("No file selected.")
    if not allowed_file(file_storage.filename):
        allowed = ", ".join(f".{ext}" for ext in sorted(current_app.config["ALLOWED_EXTENSIONS"]))
        raise ValueError(f"File type is not allowed. Accepted formats: {allowed}.")

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_name = _unique_filename(file_storage.filename)
    save_path = upload_dir / stored_name
    file_storage.save(save_path)
    size = save_path.stat().st_size

    return execute(
        "INSERT INTO files (filename, filepath, size, uploaded_by) VALUES (?, ?, ?, ?)",
        (stored_name, str(save_path), size, user_id),
    )


def list_files():
    return query_all(
        """
        SELECT f.id, f.filename, f.size, f.uploaded_at, f.uploaded_by, u.username
        FROM files AS f
        JOIN users AS u ON f.uploaded_by = u.id
        ORDER BY f.uploaded_at DESC, f.id DESC
        """
    )


def get_file_by_id(file_id: int):
    return query_one(
        """
        SELECT f.id, f.filename, f.filepath, f.size, f.uploaded_at, f.uploaded_by, u.username
        FROM files AS f
        JOIN users AS u ON f.uploaded_by = u.id
        WHERE f.id = ?
        """,
        (file_id,),
    )


def delete_file(file_row, requester_id: int) -> None:
    if file_row["uploaded_by"] != requester_id:
        raise PermissionError("You can only delete your own files.")

    path = Path(file_row["filepath"])
    if path.exists():
        path.unlink()

    execute("DELETE FROM files WHERE id = ?", (file_row["id"],))
