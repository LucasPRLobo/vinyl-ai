"""Feed API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.services.feed import get_user_feed, get_group_feed

router = APIRouter(prefix="/feed", tags=["feed"])


class FeedEventResponse(BaseModel):
    id: str
    user_id: str
    group_id: str | None
    event_type: str
    discogs_id: int | None
    title: str
    body: str | None
    metadata_json: dict | None
    created_at: str


@router.get("/", response_model=list[FeedEventResponse])
async def my_feed(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the feed for the current user (all groups)."""
    events = await get_user_feed(db, user_id=str(user.id), limit=limit, offset=offset)
    return [
        FeedEventResponse(
            id=str(e.id),
            user_id=str(e.user_id),
            group_id=str(e.group_id) if e.group_id else None,
            event_type=e.event_type,
            discogs_id=e.discogs_id,
            title=e.title,
            body=e.body,
            metadata_json=e.metadata_json,
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]


@router.get("/group/{group_id}", response_model=list[FeedEventResponse])
async def group_feed(
    group_id: str,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the feed for a specific group."""
    events = await get_group_feed(db, group_id=group_id, limit=limit, offset=offset)
    return [
        FeedEventResponse(
            id=str(e.id),
            user_id=str(e.user_id),
            group_id=str(e.group_id) if e.group_id else None,
            event_type=e.event_type,
            discogs_id=e.discogs_id,
            title=e.title,
            body=e.body,
            metadata_json=e.metadata_json,
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]
