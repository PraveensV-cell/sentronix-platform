import os
import shutil
import uuid

from fastapi import APIRouter
from fastapi import File
from fastapi import UploadFile

from src.services.video_detection_service import VideoDetectionService

router = APIRouter(
    prefix="/detect",
    tags=["Video Detection"],
)

UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True,
)


@router.post("/video")
async def detect_video(
    file: UploadFile = File(...),
):

    filename = f"{uuid.uuid4()}_{file.filename}"

    filepath = os.path.join(
        UPLOAD_DIR,
        filename,
    )

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    result = VideoDetectionService().detect(
        filepath,
    )

    return result
