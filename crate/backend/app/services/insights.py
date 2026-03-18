"""Insights engine: generates narrative insights from graph data."""

import json
import logging

from app.graph.connection import get_neo4j_driver
from app.graph.analysis import get_collection_stats, find_shared_personnel
from app.graph.ingestion import get_new_connections
from app.services.research import generate_insights_on_add

logger = logging.getLogger(__name__)


def generate_add_insights(discogs_id: int, user_id: str, synthesized_data: dict) -> list[dict]:
    """Generate 'Did you know?' insights after adding a record.

    Called after Smart Add ingestion to surface interesting connections.
    """
    driver = get_neo4j_driver()

    # Get new connections this record created
    connections = get_new_connections(driver, discogs_id=discogs_id, user_id=user_id)

    # Get overall collection stats for context
    with driver.session() as session:
        stats = session.execute_read(get_collection_stats, user_id=user_id)

    if not connections and stats.get("total_albums", 0) < 3:
        # Too few records for meaningful insights
        return []

    # Build summaries for the AI
    album = synthesized_data.get("album", {})
    artists = synthesized_data.get("artists", [])
    record_summary = (
        f"{album.get('title', '?')} — "
        f"Artists: {', '.join(a['name'] for a in artists[:5])}. "
        f"Genres: {', '.join(synthesized_data.get('genres', []))}. "
        f"Scenes: {', '.join(s['name'] for s in synthesized_data.get('scenes', []))}."
    )

    connections_str = json.dumps(connections, indent=2, default=str) if connections else "No direct connections found."
    stats_str = json.dumps(stats, indent=2, default=str)

    try:
        insights = generate_insights_on_add(
            record_summary=record_summary,
            connections=connections_str,
            collection_stats=stats_str,
        )
        return insights
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        return []


def get_shared_personnel_insights(user_id: str) -> list[dict]:
    """Generate insights about shared personnel across the collection."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        shared = session.execute_read(find_shared_personnel, user_id=user_id)

    insights = []
    for s in shared[:5]:
        insights.append({
            "type": "connection",
            "text": f"{s['artist']} appears on {s['album_count']} albums in your collection: {', '.join(s['albums'])}",
        })
    return insights
