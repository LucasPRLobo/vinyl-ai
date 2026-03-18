"""Store Map API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.store import Store, StoreVisit
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/stores", tags=["stores"])


class CreateStoreRequest(BaseModel):
    name: str
    city: str
    country: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    specialties: str | None = None
    price_range: str | None = None
    url: str | None = None


class StoreResponse(BaseModel):
    id: str
    name: str
    city: str
    country: str
    address: str | None
    lat: float | None
    lng: float | None
    specialties: str | None
    price_range: str | None
    url: str | None
    visit_count: int
    avg_rating: float | None


class AddVisitRequest(BaseModel):
    rating: int | None = None
    notes: str | None = None
    records_found: int | None = None


class VisitResponse(BaseModel):
    id: str
    user_name: str
    rating: int | None
    notes: str | None
    records_found: int | None
    visited_at: str


@router.post("/", response_model=StoreResponse)
async def create_store(
    req: CreateStoreRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = Store(
        name=req.name, city=req.city, country=req.country,
        address=req.address, lat=req.lat, lng=req.lng,
        specialties=req.specialties, price_range=req.price_range,
        url=req.url, added_by=user.id,
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)

    return StoreResponse(
        id=str(store.id), name=store.name, city=store.city, country=store.country,
        address=store.address, lat=store.lat, lng=store.lng,
        specialties=store.specialties, price_range=store.price_range,
        url=store.url, visit_count=0, avg_rating=None,
    )


@router.get("/", response_model=list[StoreResponse])
async def list_stores(
    city: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Store)
    if city:
        query = query.where(Store.city == city)
    result = await db.execute(query.order_by(Store.name))
    stores = result.scalars().all()

    responses = []
    for store in stores:
        visits = await db.execute(
            select(StoreVisit).where(StoreVisit.store_id == store.id)
        )
        visit_list = visits.scalars().all()
        ratings = [v.rating for v in visit_list if v.rating is not None]

        responses.append(StoreResponse(
            id=str(store.id), name=store.name, city=store.city, country=store.country,
            address=store.address, lat=store.lat, lng=store.lng,
            specialties=store.specialties, price_range=store.price_range,
            url=store.url, visit_count=len(visit_list),
            avg_rating=round(sum(ratings) / len(ratings), 1) if ratings else None,
        ))

    return responses


@router.get("/map")
async def store_map_data(db: AsyncSession = Depends(get_db)):
    """Get all stores with coordinates for map display."""
    result = await db.execute(
        select(Store).where(Store.lat.isnot(None), Store.lng.isnot(None))
    )
    stores = result.scalars().all()
    return [
        {
            "id": str(s.id), "name": s.name, "city": s.city,
            "lat": s.lat, "lng": s.lng,
            "specialties": s.specialties, "price_range": s.price_range,
        }
        for s in stores
    ]


@router.post("/{store_id}/visit", response_model=VisitResponse)
async def add_visit(
    store_id: str,
    req: AddVisitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    visit = StoreVisit(
        store_id=uuid.UUID(store_id), user_id=user.id,
        rating=req.rating, notes=req.notes, records_found=req.records_found,
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)

    return VisitResponse(
        id=str(visit.id), user_name=user.name,
        rating=visit.rating, notes=visit.notes,
        records_found=visit.records_found,
        visited_at=visit.visited_at.isoformat(),
    )


@router.get("/{store_id}/visits", response_model=list[VisitResponse])
async def get_visits(store_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StoreVisit, User)
        .join(User, StoreVisit.user_id == User.id)
        .where(StoreVisit.store_id == uuid.UUID(store_id))
        .order_by(StoreVisit.visited_at.desc())
    )
    return [
        VisitResponse(
            id=str(v.id), user_name=u.name,
            rating=v.rating, notes=v.notes,
            records_found=v.records_found,
            visited_at=v.visited_at.isoformat(),
        )
        for v, u in result.all()
    ]
