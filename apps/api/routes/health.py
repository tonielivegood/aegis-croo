from fastapi import APIRouter

from src.aegis_croo.config import SERVICE_MODE, SERVICE_NAME


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "mode": SERVICE_MODE,
    }
