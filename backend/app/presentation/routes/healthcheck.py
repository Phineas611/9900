from fastapi import APIRouter
from app.application.models.healthcheck import HealthcheckResponse 

router = APIRouter(tags=["healthcheck"])

@router.get("/healthcheck", response_model=HealthcheckResponse)
def healthcheck():
    """
    Simple API health check endpoint.
    """
    return {"status": "healthy"}
