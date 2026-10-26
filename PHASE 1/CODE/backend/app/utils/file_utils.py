import os
import uuid
from pathlib import Path
from app.core.config import settings


def validate_video_extension(filename: str) -> bool:
    """
    Checks if the filename has an allowed video extension.
    Supported extensions: mp4, avi, mov, mkv.
    """
    if not filename or "." not in filename:
        return False
    
    ext = Path(filename).suffix.lstrip(".").lower()
    return ext in settings.ALLOWED_EXTENSIONS


def format_file_size(size_bytes: int) -> str:
    """
    Formats byte size into human readable string (e.g., '45.2 MB', '1.4 GB').
    """
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def generate_unique_filename(original_filename: str) -> tuple[str, str]:
    """
    Generates a unique UUID and corresponding stored filename preserving extension.
    Returns (video_id, stored_filename).
    """
    ext = Path(original_filename).suffix.lower()
    video_id = str(uuid.uuid4())
    stored_filename = f"{video_id}{ext}"
    return video_id, stored_filename
