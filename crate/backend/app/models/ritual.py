import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Rotation(Base):
    """Monthly rotation: one person picks a record, everyone listens."""
    __tablename__ = "rotations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id"), index=True)
    picker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    discogs_id: Mapped[int] = mapped_column(Integer)
    album_title: Mapped[str] = mapped_column(String(500))
    briefing: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI-generated deep briefing
    month: Mapped[str] = mapped_column(String(7))  # "2026-03"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DigChallenge(Base):
    """Monthly dig challenge: find something from a white space in the group graph."""
    __tablename__ = "dig_challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id"), index=True)
    challenge_text: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str] = mapped_column(String(50))  # label, genre, scene, city
    target_name: Mapped[str] = mapped_column(String(255))
    month: Mapped[str] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrateCensus(Base):
    """Yearly group summary."""
    __tablename__ = "crate_censuses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI narrative
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
