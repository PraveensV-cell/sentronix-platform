from fastapi import APIRouter
from pydantic import BaseModel

from src.services.ai_client import ai_client


router = APIRouter(
    prefix="/ai",
    tags=["AI Service"],
)


class DetectRequest(BaseModel):
    image_path: str


@router.get("/health")
async def health():

    return await ai_client.health()


@router.post("/detect")
async def detect(
    request: DetectRequest,
):

    return await ai_client.detect(
        request.image_path,
    )
