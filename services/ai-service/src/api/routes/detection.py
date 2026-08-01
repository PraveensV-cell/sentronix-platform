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
from src.services.detection_service import (
    detection_service,
)


router = APIRouter(
    prefix="/detect",
    tags=["Detection"],
)


UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    exist_ok=True,
)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
}


@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
):
    """
    Detect objects immediately from image.
    """

    extension = Path(
        file.filename or "",
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format.",
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

        result = detection_service.detect_image(
            str(filepath),
        )

        return {
            "success": result["success"],
            "filename": filename,
            "detections": result["detections"],
            "annotated_image": result["annotated_image"],
            "total_objects": result["total_objects"],
        }

    except Exception as error:
        logger.error(
            f"Image detection failed: {error}",
        )

        raise HTTPException(
            status_code=500,
            detail="Detection failed.",
        )

    finally:
        if filepath.exists():
            os.remove(
                filepath,
            )


@router.post("/queue")
async def queue_detection(
    file: UploadFile = File(...),
    camera_id: int = 0,
):
    """
    Add image detection task to background worker.
    """

    extension = Path(
        file.filename or "",
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format.",
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

        result = await detection_service.submit_detection_task(
            str(filepath),
            camera_id,
        )

        return {
            "filename": filename,
            **result,
        }

    except Exception as error:
        logger.error(
            f"Queue detection failed: {error}",
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to queue detection.",
        )

    finally:
        if filepath.exists():
            os.remove(
                filepath,
            )
