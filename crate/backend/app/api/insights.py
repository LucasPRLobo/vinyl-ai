"""Insights API routes."""

from fastapi import APIRouter

from app.services.insights import get_shared_personnel_insights

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/shared-personnel")
def shared_personnel_insights(user_id: str = "default-user"):
    """Get insights about shared personnel across the collection."""
    return get_shared_personnel_insights(user_id)
