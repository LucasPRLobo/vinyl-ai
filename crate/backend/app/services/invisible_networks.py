"""Invisible Networks: surface the most connected but least famous nodes in the graph."""

import json
import logging

import anthropic

from app.config import settings
from app.graph.connection import get_neo4j_driver

logger = logging.getLogger(__name__)


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def find_invisible_networks(user_id: str | None = None, group_id: str | None = None) -> dict:
    """Find the most connected but least well-known nodes across the collection."""
    driver = get_neo4j_driver()

    # Scope to user or group
    if group_id:
        scope_match = """
            MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $scope_id})
            MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        """
        scope_id = group_id
    else:
        scope_match = """
            MATCH (u:User {id: $scope_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        """
        scope_id = user_id or "default-user"

    with driver.session() as session:
        # Find artists by how many albums they appear on (but aren't the main artist)
        result = session.run(
            f"""
            {scope_match}
            MATCH (ar:Artist)-[:PERFORMED_ON]->(a)
            WHERE NOT (ar)-[:PERFORMED_ON {{role: 'Main Artist'}}]->(a)
            WITH ar, collect(DISTINCT a.title) AS albums, count(DISTINCT a) AS album_count
            WHERE album_count >= 2
            RETURN ar.name AS name, ar.origin_city AS origin_city,
                   albums, album_count
            ORDER BY album_count DESC
            LIMIT 20
            """,
            scope_id=scope_id,
        )
        unsung_artists = [r.data() for r in result]

        # Find studios that appear on multiple albums
        result2 = session.run(
            f"""
            {scope_match}
            MATCH (a)-[:RECORDED_AT]->(s:Studio)
            WITH s, collect(DISTINCT a.title) AS albums, count(DISTINCT a) AS album_count
            WHERE album_count >= 2
            RETURN s.name AS name, s.city AS city, albums, album_count
            ORDER BY album_count DESC
            LIMIT 10
            """,
            scope_id=scope_id,
        )
        key_studios = [r.data() for r in result2]

        # Find labels with most albums
        result3 = session.run(
            f"""
            {scope_match}
            MATCH (a)-[:RELEASED_ON]->(l:Label)
            WITH l, collect(DISTINCT a.title) AS albums, count(DISTINCT a) AS album_count
            WHERE album_count >= 2
            RETURN l.name AS name, albums, album_count
            ORDER BY album_count DESC
            LIMIT 10
            """,
            scope_id=scope_id,
        )
        key_labels = [r.data() for r in result3]

        # Find engineers/producers across multiple albums
        result4 = session.run(
            f"""
            {scope_match}
            MATCH (ar:Artist)-[:PRODUCED|ENGINEERED]->(a)
            WITH ar, collect(DISTINCT a.title) AS albums, count(DISTINCT a) AS album_count
            WHERE album_count >= 2
            RETURN ar.name AS name, albums, album_count, 'producer/engineer' AS role
            ORDER BY album_count DESC
            LIMIT 10
            """,
            scope_id=scope_id,
        )
        key_producers = [r.data() for r in result4]

    # Generate AI profiles for the top unsung figures
    profiles = []
    if unsung_artists:
        client = _get_client()
        top_unsung = unsung_artists[:5]
        prompt = f"""These are the most connected but non-headlining musicians in a vinyl collection's knowledge graph. For each one, write a 2-3 sentence profile explaining who they are, why they matter, and what they reveal about the collection.

Musicians:
{json.dumps(top_unsung, indent=2)}

Also consider these key studios and labels:
Studios: {json.dumps(key_studios[:3], indent=2)}
Labels: {json.dumps(key_labels[:3], indent=2)}
Producers/Engineers: {json.dumps(key_producers[:3], indent=2)}

Return as JSON array:
```json
[{{"name": "...", "profile": "2-3 sentence profile", "type": "artist|studio|label|producer"}}]
```"""

        msg = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            profiles = json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            profiles = [{"name": a["name"], "profile": f"Appears on {a['album_count']} albums", "type": "artist"} for a in top_unsung]

    return {
        "unsung_artists": unsung_artists,
        "key_studios": key_studios,
        "key_labels": key_labels,
        "key_producers": key_producers,
        "profiles": profiles,
    }
