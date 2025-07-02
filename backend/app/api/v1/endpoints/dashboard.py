"""
Dashboard endpoints for OSINT Platform
Provides dashboard data and metrics
"""

from fastapi import APIRouter, Depends
from app.api.v1.deps import CurrentUser
from app.core.logging_config import get_logger

logger = get_logger('dashboard')
router = APIRouter()


@router.get("/metrics")
async def get_dashboard_metrics(current_user: CurrentUser):
    """Get dashboard metrics"""
    return {
        "total_sources": 12,
        "active_alerts": 3,
        "recent_analyses": 25,
        "sentiment_trend": "positive",
        "data_points_collected": 1247
    }


@router.get("/recent-activity")
async def get_recent_activity(current_user: CurrentUser):
    """Get recent platform activity"""
    return {
        "activities": [
            {
                "type": "data_collection",
                "description": "Collected 15 new social media posts",
                "timestamp": "2024-01-15T10:00:00Z"
            },
            {
                "type": "analysis",
                "description": "Sentiment analysis completed",
                "timestamp": "2024-01-15T09:45:00Z"
            }
        ]
    }
