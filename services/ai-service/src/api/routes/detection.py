import os
import shutil
import uuid

from fastapi import APIRouter
from fastapi import File
from fastapi import UploadFile

from src.services.detection_service import DetectionService

router = APIRouter(
    prefix="/detect",
    tags=["Detection"],
)

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
):
    """
    Detect objects from an uploaded image.
    """

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

    result = DetectionService().detect_image(
        filepath,
    )

    return {
        "filename": filename,
        "detections": result["detections"],
        "annotated_image": result["annotated_image"],
    }
