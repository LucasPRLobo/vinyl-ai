"""Deep insights API routes."""

from fastapi import APIRouter, Depends

from app.services.deep_insights import (
    generate_collection_dna,
    generate_thread,
    find_uncharted_territory,
    generate_temporal_insights,
)
from app.dependencies import get_user_id

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/dna")
def collection_dna(uid: str = Depends(get_user_id)):
    return generate_collection_dna(uid)


@router.get("/thread")
def the_thread(album_id_1: int, album_id_2: int):
    return generate_thread(album_id_1, album_id_2)


@router.get("/uncharted")
def uncharted_territory(uid: str = Depends(get_user_id)):
    return find_uncharted_territory(uid)


@router.get("/temporal")
def temporal_insights(uid: str = Depends(get_user_id)):
    return generate_temporal_insights(uid)
