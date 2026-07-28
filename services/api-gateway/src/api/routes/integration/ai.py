from fastapi import APIRouter
from fastapi import File
from fastapi import UploadFile

from src.clients.ai_client import AIClient

router = APIRouter(
    prefix="/integration/ai",
    tags=["AI Integration"],
)

client = AIClient()


@router.get("/health")
async def ai_health():

    return await client.health()


@router.post("/detect")
async def detect(
    image: UploadFile = File(...),
):

    files = {
        "image": (
            image.filename,
            await image.read(),
            image.content_type,
        )
    }

    return await client.detect(files)
