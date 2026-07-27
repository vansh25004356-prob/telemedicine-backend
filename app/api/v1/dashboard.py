"""
Dashboard API router - handles dashboard analytics and statistics endpoints.

Provides:
- GET  /dashboard/stats - Platform-wide statistics
- GET  /dashboard/recent-activity - Recent platform activity
- GET  /dashboard/trends - Consultation trends over time
- GET  /dashboard/ai-usage - AI service usage statistics
- GET  /dashboard/notifications - User notifications
- POST /dashboard/notifications/{id}/read - Mark notification as read
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.schemas.common import APIResponse
from app.services.dashboard_service import dashboard_service
from app.core.security import get_current_user
from app.exceptions import NotFoundException, ValidationException

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get platform-wide statistics for the dashboard."""
    try:
        stats = dashboard_service.get_platform_stats()
        return APIResponse(
            success=True,
            message="Dashboard stats fetched successfully",
            data=stats,
        )
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complete")
async def get_complete_dashboard(current_user: dict = Depends(get_current_user)):
    """Get a complete dashboard with all stats, activity, trends, and AI usage."""
    try:
        data = dashboard_service.get_complete_dashboard()
        return APIResponse(
            success=True,
            message="Complete dashboard data fetched successfully",
            data=data,
        )
    except Exception as e:
        logger.error(f"Error fetching complete dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Get recent platform activity."""
    try:
        activity = dashboard_service.get_recent_activity(limit)
        return APIResponse(
            success=True,
            message=f"Found {len(activity)} recent activities",
            data=activity,
        )
    except Exception as e:
        logger.error(f"Error fetching recent activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_consultation_trends(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Get consultation trends over a specified number of days."""
    try:
        trends = dashboard_service.get_consultation_trends(days)
        return APIResponse(
            success=True,
            message=f"Consultation trends for last {days} days",
            data=trends,
        )
    except Exception as e:
        logger.error(f"Error fetching consultation trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-usage")
async def get_ai_usage(current_user: dict = Depends(get_current_user)):
    """Get AI service usage statistics."""
    try:
        ai_stats = dashboard_service.get_ai_usage_stats()
        return APIResponse(
            success=True,
            message="AI usage stats fetched successfully",
            data=ai_stats,
        )
    except Exception as e:
        logger.error(f"Error fetching AI usage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications")
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Get notifications for the current user."""
    try:
        notifications = dashboard_service.get_notifications(
            current_user["id"], limit
        )
        return APIResponse(
            success=True,
            message=f"Found {len(notifications)} notifications",
            data=notifications,
        )
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a notification as read."""
    try:
        success = dashboard_service.mark_notification_read(notification_id)
        if success:
            return APIResponse(
                success=True,
                message="Notification marked as read",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to mark notification as read",
            )
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

