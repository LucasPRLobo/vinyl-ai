import uuid
from datetime import datetime

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    specialties: Mapped[str | None] = mapped_column(Text, nullable=True)  # Comma-separated tags
    price_range: Mapped[str | None] = mapped_column(String(50), nullable=True)  # $, $$, $$$
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    added_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StoreVisit(Base):
    __tablename__ = "store_visits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    records_found: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
