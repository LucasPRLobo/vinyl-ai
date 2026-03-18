"""Pattern Discovery: scan the graph for emergent patterns and generate AI explanations."""

import json
import logging

import anthropic

from app.config import settings
from app.graph.connection import get_neo4j_driver

logger = logging.getLogger(__name__)


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def discover_patterns(user_id: str | None = None, group_id: str | None = None) -> list[dict]:
    """Scan the graph for emergent patterns. Returns a list of discovered patterns with AI explanations."""
    driver = get_neo4j_driver()
    patterns = []

    if group_id:
        scope = "MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $scope_id}) MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)"
        scope_id = group_id
    else:
        scope = "MATCH (u:User {id: $scope_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)"
        scope_id = user_id or "default-user"

    with driver.session() as session:
        # 1. Instrument clusters
        result = session.run(
            f"""
            {scope}
            MATCH (ar:Artist)-[r:PERFORMED_ON]->(a)
            WHERE r.instrument IS NOT NULL
            WITH r.instrument AS instrument, collect(DISTINCT a.title) AS albums, count(DISTINCT a) AS count
            WHERE count >= 3
            RETURN instrument, albums, count
            ORDER BY count DESC
            LIMIT 5
            """,
            scope_id=scope_id,
        )
        for r in result:
            d = r.data()
            patterns.append({
                "type": "instrument_cluster",
                "title": f"{d['instrument']} appears on {d['count']} records",
                "data": d,
            })

        # 2. Temporal hotspots
        result2 = session.run(
            f"""
            {scope}
            WHERE a.year IS NOT NULL
            WITH a.year AS year, collect(a.title) AS albums, count(a) AS count
            ORDER BY count DESC
            LIMIT 3
            """,
            scope_id=scope_id,
        )
        for r in result2:
            d = r.data()
            if d["count"] >= 3:
                patterns.append({
                    "type": "temporal_hotspot",
                    "title": f"{d['year']} has {d['count']} records",
                    "data": d,
                })

        # 3. Cross-genre bridges (artists who span genres)
        result3 = session.run(
            f"""
            {scope}
            MATCH (ar:Artist)-[:PERFORMED_ON]->(a)-[:HAS_GENRE]->(g:Genre)
            WITH ar, collect(DISTINCT g.name) AS genres, count(DISTINCT g) AS genre_count,
                 collect(DISTINCT a.title) AS albums
            WHERE genre_count >= 2
            RETURN ar.name AS artist, genres, genre_count, albums
            ORDER BY genre_count DESC
            LIMIT 5
            """,
            scope_id=scope_id,
        )
        for r in result3:
            d = r.data()
            patterns.append({
                "type": "cross_genre_bridge",
                "title": f"{d['artist']} bridges {', '.join(d['genres'])}",
                "data": d,
            })

        # 4. Geographic echoes (cities with shared musical DNA)
        result4 = session.run(
            f"""
            {scope}
            MATCH (ar:Artist)-[:FROM]->(c:City)
            MATCH (ar)-[:PERFORMED_ON]->(a)-[:HAS_GENRE]->(g:Genre)
            WITH c.name AS city, collect(DISTINCT g.name) AS genres,
                 count(DISTINCT a) AS album_count, collect(DISTINCT ar.name) AS artists
            WHERE album_count >= 2
            RETURN city, genres, album_count, artists[..5] AS sample_artists
            ORDER BY album_count DESC
            LIMIT 5
            """,
            scope_id=scope_id,
        )
        for r in result4:
            d = r.data()
            patterns.append({
                "type": "geographic_echo",
                "title": f"{d['city']}: {d['album_count']} records",
                "data": d,
            })

        # 5. Convergence (if group: members who independently collected from the same scene)
        if group_id:
            result5 = session.run(
                """
                MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $scope_id})
                MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)-[:PART_OF_SCENE]->(s:Scene)
                WITH s, collect(DISTINCT u.name) AS collectors, count(DISTINCT u) AS collector_count,
                     count(DISTINCT a) AS album_count
                WHERE collector_count >= 2
                RETURN s.name AS scene, collectors, collector_count, album_count
                ORDER BY collector_count DESC
                LIMIT 5
                """,
                scope_id=scope_id,
            )
            for r in result5:
                d = r.data()
                patterns.append({
                    "type": "convergence",
                    "title": f"{d['collector_count']} members independently collected from {d['scene']}",
                    "data": d,
                })

    # Generate AI explanations for the most interesting patterns
    if patterns:
        patterns = _explain_patterns(patterns[:10])

    return patterns


def _explain_patterns(patterns: list[dict]) -> list[dict]:
    """Use AI to explain why each pattern matters."""
    client = _get_client()
    prompt = f"""These patterns were discovered in a vinyl collection's knowledge graph. For each one, write a brief (1-2 sentence) explanation of why this pattern is interesting and what it reveals about music history.

Patterns:
{json.dumps([{"type": p["type"], "title": p["title"]} for p in patterns], indent=2)}

Return as JSON array:
```json
[{{"title": "...", "explanation": "1-2 sentence explanation"}}]
```"""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
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
        explanations = json.loads(json_str)
        # Merge explanations back into patterns
        for i, p in enumerate(patterns):
            if i < len(explanations):
                p["explanation"] = explanations[i].get("explanation", "")
    except (json.JSONDecodeError, IndexError):
        pass

    return patterns
