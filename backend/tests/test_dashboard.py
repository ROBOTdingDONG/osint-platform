"""
Tests for dashboard endpoints
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.db.models.user import User


class TestDashboardEndpoints:
    """Test dashboard endpoints."""
    
    async def test_get_dashboard_metrics_authenticated(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting dashboard metrics with authentication."""
        response = await async_client.get("/api/v1/dashboard/metrics", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required fields
        required_fields = [
            "total_sources",
            "active_alerts", 
            "recent_analyses",
            "sentiment_trend",
            "data_points_collected"
        ]
        
        for field in required_fields:
            assert field in data
        
        # Check data types
        assert isinstance(data["total_sources"], int)
        assert isinstance(data["active_alerts"], int)
        assert isinstance(data["recent_analyses"], int)
        assert isinstance(data["data_points_collected"], int)
        assert isinstance(data["sentiment_trend"], str)
    
    async def test_get_dashboard_metrics_unauthorized(self, async_client: AsyncClient):
        """Test getting dashboard metrics without authentication."""
        response = await async_client.get("/api/v1/dashboard/metrics")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_recent_activity_authenticated(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting recent activity with authentication."""
        response = await async_client.get("/api/v1/dashboard/recent-activity", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check structure
        assert "activities" in data
        assert isinstance(data["activities"], list)
        
        # If there are activities, check their structure
        if data["activities"]:
            activity = data["activities"][0]
            required_fields = ["type", "description", "timestamp"]
            
            for field in required_fields:
                assert field in activity
    
    async def test_get_recent_activity_unauthorized(self, async_client: AsyncClient):
        """Test getting recent activity without authentication."""
        response = await async_client.get("/api/v1/dashboard/recent-activity")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
