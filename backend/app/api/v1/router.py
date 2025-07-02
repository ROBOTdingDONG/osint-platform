"""
Main API router for OSINT Platform v1
Aggregates all API endpoints and provides centralized routing
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    data_sources,
    analysis,
    reports,
    alerts,
    dashboard
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["User Management"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    data_sources.router,
    prefix="/data-sources",
    tags=["Data Sources"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Data Analysis"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alerts & Notifications"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={401: {"description": "Unauthorized"}}
)