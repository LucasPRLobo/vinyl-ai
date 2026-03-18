import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class FeedEvent(Base):
    __tablename__ = "feed_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # record_added, annotation, trip_report
    discogs_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI-enriched context
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # connections, insights, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
