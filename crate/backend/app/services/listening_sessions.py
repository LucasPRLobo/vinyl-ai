"""Listening session generator: graph-informed curation."""

import json
import logging

import anthropic

from app.config import settings
from app.graph.connection import get_neo4j_driver

logger = logging.getLogger(__name__)


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def generate_session(
    user_id: str,
    prompt_text: str,
    group_id: str | None = None,
    max_records: int = 10,
) -> dict:
    """Generate a listening session based on a user's request.

    Args:
        user_id: The requesting user
        prompt_text: What they want (e.g. "5 funk records for tonight",
                     "a journey through 1970s music", "records featuring flute")
        group_id: If set, draw from the group's combined collection
        max_records: Maximum records to include
    """
    driver = get_neo4j_driver()

    # Get the collection with rich metadata
    if group_id:
        query = """
            MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
            MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            OPTIONAL MATCH (a)-[:HAS_GENRE]->(genre:Genre)
            OPTIONAL MATCH (a)<-[:PERFORMED_ON]-(ar:Artist)
            OPTIONAL MATCH (a)-[:PART_OF_SCENE]->(s:Scene)
            RETURN a.discogs_id AS discogs_id, a.title AS title, a.year AS year,
                   collect(DISTINCT genre.name) AS genres,
                   collect(DISTINCT ar.name) AS artists,
                   collect(DISTINCT s.name) AS scenes,
                   u.name AS owner
        """
        params = {"group_id": group_id}
    else:
        query = """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            OPTIONAL MATCH (a)-[:HAS_GENRE]->(genre:Genre)
            OPTIONAL MATCH (a)<-[:PERFORMED_ON]-(ar:Artist)
            OPTIONAL MATCH (a)-[:PART_OF_SCENE]->(s:Scene)
            RETURN a.discogs_id AS discogs_id, a.title AS title, a.year AS year,
                   collect(DISTINCT genre.name) AS genres,
                   collect(DISTINCT ar.name) AS artists,
                   collect(DISTINCT s.name) AS scenes
        """
        params = {"user_id": user_id}

    with driver.session() as session:
        result = session.run(query, **params)
        collection = [r.data() for r in result]

    if not collection:
        return {"session": [], "narrative": "No records in collection to build a session from."}

    # Get shared personnel for connection-based sequencing
    with driver.session() as session:
        shared_query = """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            MATCH (ar:Artist)-[:PERFORMED_ON]->(a)
            WITH ar.name AS artist, collect(DISTINCT a.title) AS albums
            WHERE size(albums) > 1
            RETURN artist, albums
            LIMIT 20
        """ if not group_id else """
            MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
            MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            MATCH (ar:Artist)-[:PERFORMED_ON]->(a)
            WITH ar.name AS artist, collect(DISTINCT a.title) AS albums
            WHERE size(albums) > 1
            RETURN artist, albums
            LIMIT 20
        """
        shared_params = {"group_id": group_id} if group_id else {"user_id": user_id}
        shared_result = session.run(shared_query, **shared_params)
        shared_personnel = [r.data() for r in shared_result]

    client = _get_client()
    ai_prompt = f"""You are a music curator building a vinyl listening session. The user wants:

"{prompt_text}"

Available collection ({len(collection)} records):
{json.dumps(collection[:100], indent=1)}

Shared musicians across the collection (for connection-based sequencing):
{json.dumps(shared_personnel, indent=1)}

Select up to {max_records} records and arrange them in an order that tells a story.
For each record, explain briefly why it's in this position and how it connects to the next.

Return as JSON:
```json
{{
  "title": "Session title",
  "records": [
    {{
      "discogs_id": 12345,
      "title": "Album title",
      "reason": "Why this record and why in this position",
      "connection_to_next": "How this connects to the next record (null for last)"
    }}
  ],
  "narrative": "A 2-3 sentence description of the journey this session takes"
}}
```"""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=2048,
        messages=[{"role": "user", "content": ai_prompt}],
    )

    # Parse response
    text = msg.content[0].text
    try:
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0]
        else:
            json_str = text
        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        return {"session": [], "narrative": text}
