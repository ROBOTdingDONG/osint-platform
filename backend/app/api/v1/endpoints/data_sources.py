"""
Data sources endpoints for OSINT Platform
Manages data collection sources and configurations
"""

from fastapi import APIRouter, Depends
from app.api.v1.deps import CurrentUser
from app.core.logging_config import get_logger

logger = get_logger('data_sources')
router = APIRouter()


@router.get("/")
async def list_data_sources(current_user: CurrentUser):
    """List configured data sources"""
    return {
        "sources": [
            {"id": "1", "name": "Twitter", "type": "social_media", "status": "active"},
            {"id": "2", "name": "News API", "type": "news", "status": "active"}
        ]
    }


@router.post("/")
async def create_data_source(current_user: CurrentUser):
    """Create new data source"""
    return {"message": "Data source creation endpoint - coming soon"}
