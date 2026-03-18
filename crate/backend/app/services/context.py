"""Lazy context generation: generates rich context for a record on first view, then caches it."""

import json
import logging

import anthropic

from app.config import settings
from app.graph.connection import get_neo4j_driver
from app.prompts.smart_add import CONTEXT_SYSTEM, CONTEXT_PROMPT

logger = logging.getLogger(__name__)


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def get_or_generate_context(discogs_id: int) -> dict | None:
    """Get cached context for a record, or generate it on first access.

    Returns dict with keys: historical_note, significance, anecdotes.
    Returns None if record not found.
    """
    driver = get_neo4j_driver()

    with driver.session() as session:
        # Check if context already cached on the Album node
        result = session.run(
            """
            MATCH (a:Album {discogs_id: $did})
            RETURN a.title AS title, a.year AS year,
                   a.context_historical AS historical_note,
                   a.context_significance AS significance,
                   a.context_anecdotes AS anecdotes,
                   a.context_confidence AS confidence,
                   a.context_sources AS sources_used
            """,
            did=discogs_id,
        )
        record = result.single()
        if not record:
            return None

        # If context already exists, return it
        if record["historical_note"]:
            return {
                "historical_note": record["historical_note"],
                "significance": record["significance"],
                "anecdotes": record["anecdotes"],
                "confidence": record["confidence"],
                "sources_used": record["sources_used"],
            }

        # Otherwise, gather data and generate context
        title = record["title"]
        year = record["year"]

        # Get connected data for the prompt
        credits_result = session.run(
            """
            MATCH (a:Album {discogs_id: $did})<-[r:PERFORMED_ON|PRODUCED|ENGINEERED]-(ar:Artist)
            RETURN ar.name AS name, type(r) AS role, r.instrument AS instrument
            """,
            did=discogs_id,
        )
        credits = [r.data() for r in credits_result]

        label_result = session.run(
            "MATCH (a:Album {discogs_id: $did})-[:RELEASED_ON]->(l:Label) RETURN l.name AS name",
            did=discogs_id,
        )
        labels = [r["name"] for r in label_result]

        genre_result = session.run(
            "MATCH (a:Album {discogs_id: $did})-[:HAS_GENRE]->(g:Genre) RETURN g.name AS name",
            did=discogs_id,
        )
        genres = [r["name"] for r in genre_result]

        scene_result = session.run(
            "MATCH (a:Album {discogs_id: $did})-[:PART_OF_SCENE]->(s:Scene) RETURN s.name AS name",
            did=discogs_id,
        )
        scenes = [r["name"] for r in scene_result]

        artist_result = session.run(
            """
            MATCH (a:Album {discogs_id: $did})<-[:PERFORMED_ON]-(ar:Artist)
            WHERE EXISTS { (ar)-[:PERFORMED_ON {role: 'Main Artist'}]->(a) }
               OR NOT EXISTS { (:Artist)-[:PERFORMED_ON {role: 'Main Artist'}]->(a) }
            RETURN ar.name AS name LIMIT 1
            """,
            did=discogs_id,
        )
        artist_rec = artist_result.single()
        artist_name = artist_rec["name"] if artist_rec else "Unknown"

    # Generate context with Claude
    credits_str = json.dumps(credits, indent=2) if credits else "No detailed credits available."
    prompt = CONTEXT_PROMPT.format(
        artist=artist_name,
        title=title,
        year=year or "Unknown",
        genres=", ".join(genres) if genres else "Unknown",
        label=", ".join(labels) if labels else "Unknown",
        credits=credits_str,
        scenes=", ".join(scenes) if scenes else "None identified",
    )

    try:
        client = _get_client()
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=CONTEXT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text

        # Parse JSON
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0]
        else:
            json_str = text

        context = json.loads(json_str)
    except Exception as e:
        logger.error(f"Failed to generate context for {discogs_id}: {e}")
        return None

    # Cache on the Album node
    with driver.session() as session:
        session.run(
            """
            MATCH (a:Album {discogs_id: $did})
            SET a.context_historical = $historical,
                a.context_significance = $significance,
                a.context_anecdotes = $anecdotes,
                a.context_confidence = $confidence,
                a.context_sources = $sources
            """,
            did=discogs_id,
            historical=context.get("historical_note", ""),
            significance=context.get("significance", ""),
            anecdotes=context.get("anecdotes"),
            confidence=context.get("confidence", "medium"),
            sources=context.get("sources_used", ""),
        )

    logger.info(f"Generated and cached context for album {discogs_id} (confidence: {context.get('confidence', '?')})")
    return context
