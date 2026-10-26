import os
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.utils.file_utils import (
    validate_video_extension,
    format_file_size,
    generate_unique_filename,
)
from app.models.schemas import UploadResponse

CHUNK_SIZE = 1024 * 1024  # 1 MB chunk streaming


class UploadService:
    @staticmethod
    async def process_video_upload(file: UploadFile) -> UploadResponse:
        """
        Validates video file type and size, then streams content to local storage.
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided in upload request."
            )

        # 1. Validate file extension
        if not validate_video_extension(file.filename):
            allowed_str = ", ".join([f".{ext}" for ext in sorted(settings.ALLOWED_EXTENSIONS)])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Only video files ({allowed_str}) are allowed."
            )

        # 2. Generate unique filename & destination path
        video_id, stored_filename = generate_unique_filename(file.filename)
        destination_path = settings.UPLOADS_DIR / stored_filename

        total_bytes = 0

        # 3. Stream write file to local disk in chunks
        try:
            with open(destination_path, "wb") as buffer:
                while chunk := await file.read(CHUNK_SIZE):
                    total_bytes += len(chunk)
                    
                    # Check size limit on the fly
                    if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                        buffer.close()
                        if destination_path.exists():
                            destination_path.unlink()  # Clean up partial file
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Large file. Maximum allowed upload size is 2GB."
                        )
                    
                    buffer.write(chunk)

        except HTTPException:
            raise
        except Exception as err:
            if destination_path.exists():
                destination_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {str(err)}"
            )

        formatted_size = format_file_size(total_bytes)

        return UploadResponse(
            video_id=video_id,
            filename=stored_filename,
            original_name=file.filename,
            size=formatted_size,
            status="uploaded"
        )
