"""
Analytics API routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.feedback_service import FeedbackService
from app.deps import require_role

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", dependencies=[Depends(require_role("admin", "staff"))])
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get analytics summary"""
    try:
        summary = await FeedbackService.get_analytics_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")


@router.get("/trends", dependencies=[Depends(require_role("admin", "staff"))])
async def get_analytics_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days for trends"),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics trends"""
    try:
        trends = await FeedbackService.get_analytics_trends(db, days=days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")

