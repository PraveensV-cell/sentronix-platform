from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from src.core.logger import logger
from src.services.video_detection_service import (
    video_detection_service,
)


router = APIRouter(
    prefix="/detect",
    tags=["Video Detection"],
)


UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    exist_ok=True,
)


ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
}


@router.post("/video")
async def detect_video(
    file: UploadFile = File(...),
):
    """
    Detect objects from uploaded video.
    """

    extension = Path(
        file.filename or "",
    ).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format.",
        )

    filename = f"{uuid.uuid4()}{extension}"

    filepath = UPLOAD_DIR / filename

    try:
        with filepath.open(
            "wb",
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        result = video_detection_service.detect(
            str(filepath),
        )

        return {
            "success": True,
            "filename": filename,
            "result": result,
        }

    except Exception as error:
        logger.error(
            f"Video detection failed: {error}",
        )

        raise HTTPException(
            status_code=500,
            detail="Video detection failed.",
        )

    finally:
        if filepath.exists():
            os.remove(
                filepath,
            )
