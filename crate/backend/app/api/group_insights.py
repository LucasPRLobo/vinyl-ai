"""Group insights API routes."""

from fastapi import APIRouter, Depends

from app.models.user import User
from app.dependencies import get_current_user
from app.graph.connection import get_neo4j_driver
from app.graph.group_analysis import (
    group_collection_overlap,
    group_bridges,
    group_blind_spots,
    group_taste_distance,
    group_stats,
)

router = APIRouter(prefix="/groups/{group_id}/insights", tags=["group-insights"])


@router.get("/stats")
def get_group_stats(group_id: str):
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(group_stats, group_id=group_id)


@router.get("/overlap")
def get_overlap(group_id: str):
    """Albums owned by multiple group members."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(group_collection_overlap, group_id=group_id)


@router.get("/bridges")
def get_bridges(group_id: str):
    """Members who uniquely cover certain genres — the bridges in the group graph."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(group_bridges, group_id=group_id)


@router.get("/blind-spots")
def get_blind_spots(group_id: str):
    """Genres/scenes adjacent to the group's collection but not covered."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(group_blind_spots, group_id=group_id)


@router.get("/taste-distance")
def get_taste_distance(group_id: str):
    """Taste similarity between group members."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(group_taste_distance, group_id=group_id)
