"""Feed service: create and retrieve feed events."""

import uuid
import logging

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feed_event import FeedEvent
from app.models.group import GroupMembership

logger = logging.getLogger(__name__)


async def create_record_added_event(
    db: AsyncSession,
    user_id: str,
    user_name: str,
    album_title: str,
    discogs_id: int,
    artists_added: int,
    connections: list[dict],
    group_ids: list[str] | None = None,
):
    """Create feed events when a record is added. One event per group the user belongs to."""
    # Build context body
    body = f"{user_name} added {album_title}."
    if connections:
        conn_strs = []
        for c in connections[:3]:
            if c.get("connection_type") == "shared_artist":
                conn_strs.append(f"{c['shared_artist']} also on {', '.join(c['also_on'][:2])}")
            elif c.get("connection_type") == "shared_label":
                conn_strs.append(f"Label {c['shared_label']} also on {', '.join(c['also_on'][:2])}")
        if conn_strs:
            body += " Connections: " + "; ".join(conn_strs) + "."

    metadata = {
        "artists_added": artists_added,
        "connections": connections[:5],
    }

    if group_ids:
        for gid in group_ids:
            event = FeedEvent(
                user_id=uuid.UUID(user_id),
                group_id=uuid.UUID(gid),
                event_type="record_added",
                discogs_id=discogs_id,
                title=f"{user_name} added {album_title}",
                body=body,
                metadata_json=metadata,
            )
            db.add(event)
    else:
        # Personal event (no group)
        event = FeedEvent(
            user_id=uuid.UUID(user_id),
            event_type="record_added",
            discogs_id=discogs_id,
            title=f"{user_name} added {album_title}",
            body=body,
            metadata_json=metadata,
        )
        db.add(event)

    await db.commit()


async def get_group_feed(
    db: AsyncSession,
    group_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[FeedEvent]:
    """Get chronological feed for a group."""
    result = await db.execute(
        select(FeedEvent)
        .where(FeedEvent.group_id == uuid.UUID(group_id))
        .order_by(desc(FeedEvent.created_at))
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_user_feed(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[FeedEvent]:
    """Get feed for all groups a user belongs to."""
    # Get user's group IDs
    memberships = await db.execute(
        select(GroupMembership.group_id).where(GroupMembership.user_id == uuid.UUID(user_id))
    )
    group_ids = [m for (m,) in memberships.all()]

    if not group_ids:
        # Return personal events only
        result = await db.execute(
            select(FeedEvent)
            .where(FeedEvent.user_id == uuid.UUID(user_id))
            .order_by(desc(FeedEvent.created_at))
            .offset(offset)
            .limit(limit)
        )
    else:
        result = await db.execute(
            select(FeedEvent)
            .where(FeedEvent.group_id.in_(group_ids))
            .order_by(desc(FeedEvent.created_at))
            .offset(offset)
            .limit(limit)
        )

    return list(result.scalars().all())


async def get_user_group_ids(db: AsyncSession, user_id: str) -> list[str]:
    """Get all group IDs a user belongs to."""
    result = await db.execute(
        select(GroupMembership.group_id).where(GroupMembership.user_id == uuid.UUID(user_id))
    )
    return [str(gid) for (gid,) in result.all()]
