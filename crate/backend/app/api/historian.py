"""AI Music Historian API: invisible networks, pattern discovery, migration mapping, group rituals."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.ritual import Rotation, DigChallenge
from app.models.user import User
from app.dependencies import get_current_user
from app.services.invisible_networks import find_invisible_networks
from app.services.pattern_discovery import discover_patterns
from app.services.migration_mapping import (
    find_artist_migrations,
    find_genre_migrations,
    generate_migration_narrative,
)

router = APIRouter(prefix="/historian", tags=["historian"])


# --- Invisible Networks ---

@router.get("/invisible-networks")
def invisible_networks(user_id: str | None = None, group_id: str | None = None):
    """Surface the most connected but least famous nodes — the unsung heroes."""
    return find_invisible_networks(user_id=user_id, group_id=group_id)


# --- Pattern Discovery ---

@router.get("/patterns")
def patterns(user_id: str | None = None, group_id: str | None = None):
    """Discover emergent patterns in the graph with AI explanations."""
    return discover_patterns(user_id=user_id, group_id=group_id)


# --- Migration Mapping ---

@router.get("/migrations/artists")
def artist_migrations(user_id: str | None = None, group_id: str | None = None):
    """Track how artists moved across cities."""
    return find_artist_migrations(user_id=user_id, group_id=group_id)


@router.get("/migrations/genres")
def genre_migrations(user_id: str | None = None, group_id: str | None = None):
    """Track how genres spread across cities."""
    return find_genre_migrations(user_id=user_id, group_id=group_id)


@router.post("/migrations/narrative")
def migration_narrative(migration: dict, migration_type: str = "artist"):
    """Generate an AI narrative for a specific migration path."""
    return {"narrative": generate_migration_narrative(migration, migration_type)}


# --- Group Rituals ---

class CreateRotationRequest(BaseModel):
    group_id: str
    discogs_id: int
    album_title: str


class CreateChallengeRequest(BaseModel):
    group_id: str


@router.post("/rotation")
async def create_rotation(
    req: CreateRotationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a monthly rotation pick."""
    month = datetime.now().strftime("%Y-%m")

    # Generate AI briefing for the picked record
    from app.services.deep_insights import generate_thread
    from app.graph.connection import get_neo4j_driver
    import json

    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (a:Album {discogs_id: $did})-[r]-(connected)
            RETURN type(r) AS rel, labels(connected) AS labels,
                   coalesce(connected.name, connected.title) AS name
            LIMIT 20
            """,
            did=req.discogs_id,
        )
        connections = [r.data() for r in result]

    from app.services.research import _get_client as get_ai_client
    client = get_ai_client()
    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": f"""Write a deep briefing for a group listening session of this album:

Album: {req.album_title}
Connections in the knowledge graph: {json.dumps(connections, indent=2)}

Write 2-3 paragraphs: what makes this album special, who's on it, what scene it belongs to, what to listen for. Like liner notes from a knowledgeable friend."""}],
    )
    briefing = msg.content[0].text

    rotation = Rotation(
        group_id=uuid.UUID(req.group_id),
        picker_id=user.id,
        discogs_id=req.discogs_id,
        album_title=req.album_title,
        briefing=briefing,
        month=month,
    )
    db.add(rotation)
    await db.commit()

    return {"month": month, "album": req.album_title, "briefing": briefing}


@router.get("/rotation/{group_id}")
async def get_rotations(group_id: str, db: AsyncSession = Depends(get_db)):
    """Get rotation history for a group."""
    result = await db.execute(
        select(Rotation, User)
        .join(User, Rotation.picker_id == User.id)
        .where(Rotation.group_id == uuid.UUID(group_id))
        .order_by(Rotation.created_at.desc())
    )
    return [
        {
            "month": r.month, "album": r.album_title, "discogs_id": r.discogs_id,
            "picker": u.name, "briefing": r.briefing,
        }
        for r, u in result.all()
    ]


@router.post("/dig-challenge")
async def create_dig_challenge(
    req: CreateChallengeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a dig challenge from the group graph's white spaces."""
    from app.graph.connection import get_neo4j_driver

    driver = get_neo4j_driver()
    month = datetime.now().strftime("%Y-%m")

    with driver.session() as session:
        # Find labels nobody in the group owns
        result = session.run(
            """
            MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $gid})
            MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(owned:Album)
            MATCH (owned)<-[:PERFORMED_ON]-(ar:Artist)-[:PERFORMED_ON]->(other:Album)
            MATCH (other)-[:RELEASED_ON]->(l:Label)
            WHERE NOT EXISTS {
                MATCH (any:User)-[:MEMBER_OF_GROUP]->(g)
                MATCH (any)-[:OWNS]->(:Pressing)<-[:HAS_PRESSING]-(:Album)-[:RELEASED_ON]->(l)
            }
            RETURN l.name AS label, count(DISTINCT other) AS available
            ORDER BY available DESC
            LIMIT 5
            """,
            gid=req.group_id,
        )
        unexplored_labels = [r.data() for r in result]

    if unexplored_labels:
        target = unexplored_labels[0]
        challenge = DigChallenge(
            group_id=uuid.UUID(req.group_id),
            challenge_text=f"Find a record from {target['label']} — nobody in the group has one yet, but {target['available']} albums in your graph connect to it.",
            target_type="label",
            target_name=target["label"],
            month=month,
        )
        db.add(challenge)
        await db.commit()

        return {
            "month": month,
            "challenge": challenge.challenge_text,
            "target": target["label"],
            "alternatives": [l["label"] for l in unexplored_labels[1:]],
        }

    return {"month": month, "challenge": "No white spaces found — your group has great coverage!", "target": None}


@router.get("/dig-challenge/{group_id}")
async def get_challenges(group_id: str, db: AsyncSession = Depends(get_db)):
    """Get dig challenge history for a group."""
    result = await db.execute(
        select(DigChallenge)
        .where(DigChallenge.group_id == uuid.UUID(group_id))
        .order_by(DigChallenge.created_at.desc())
    )
    return [
        {"month": c.month, "challenge": c.challenge_text, "target": c.target_name, "type": c.target_type}
        for c in result.scalars().all()
    ]
