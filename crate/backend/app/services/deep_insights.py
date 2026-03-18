"""Deep insights engine: Collection DNA, The Thread, Uncharted Territory, temporal insights."""

import json
import logging

import anthropic

from app.config import settings
from app.graph.connection import get_neo4j_driver
from app.graph.analysis import get_collection_stats, find_shared_personnel, get_hub_nodes

logger = logging.getLogger(__name__)


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def generate_collection_dna(user_id: str) -> dict:
    """Generate a 'Collection DNA' profile — what defines this collector's taste."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        stats = session.execute_read(get_collection_stats, user_id=user_id)
        shared = session.execute_read(find_shared_personnel, user_id=user_id)
        hubs = session.execute_read(get_hub_nodes, label="Artist", limit=10)

        # Decade distribution
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            WHERE a.year IS NOT NULL
            WITH (a.year / 10) * 10 AS decade, count(a) AS count
            RETURN decade, count ORDER BY decade
            """,
            user_id=user_id,
        )
        decades = [r.data() for r in result]

        # Scene coverage
        result2 = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            MATCH (a)-[:PART_OF_SCENE]->(s:Scene)
            RETURN s.name AS scene, count(a) AS count
            ORDER BY count DESC LIMIT 10
            """,
            user_id=user_id,
        )
        scenes = [r.data() for r in result2]

    client = _get_client()
    prompt = f"""Analyze this vinyl collection and write a "Collection DNA" profile — a 2-3 paragraph narrative describing what defines this collector's taste, what threads connect their records, and what it reveals about their musical worldview.

Stats: {json.dumps(stats)}
Top artists (by connections): {json.dumps(hubs[:10])}
Shared personnel (artists on multiple albums): {json.dumps(shared[:10])}
Decade distribution: {json.dumps(decades)}
Scenes: {json.dumps(scenes)}

Write in second person ("Your collection..."). Be specific, reference actual names and patterns. Don't be generic."""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "narrative": msg.content[0].text,
        "stats": stats,
        "decades": decades,
        "top_scenes": scenes,
    }


def generate_thread(album_id_1: int, album_id_2: int) -> dict:
    """Generate 'The Thread' — a narrative connecting two albums through the graph."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Find path
        result = session.run(
            """
            MATCH (a1:Album {discogs_id: $id1}), (a2:Album {discogs_id: $id2})
            MATCH path = shortestPath((a1)-[*..8]-(a2))
            RETURN [n IN nodes(path) | {labels: labels(n), name: coalesce(n.name, n.title)}] AS nodes,
                   [r IN relationships(path) | type(r)] AS rels
            """,
            id1=album_id_1, id2=album_id_2,
        )
        record = result.single()
        if not record:
            return {"narrative": "No connection found between these two albums.", "path": []}

        path_nodes = record["nodes"]
        path_rels = record["rels"]

        # Get album details
        a1 = session.run("MATCH (a:Album {discogs_id: $id}) RETURN a.title AS title", id=album_id_1).single()
        a2 = session.run("MATCH (a:Album {discogs_id: $id}) RETURN a.title AS title", id=album_id_2).single()

    client = _get_client()
    prompt = f"""Two albums in a vinyl collection are connected through a knowledge graph path. Write a compelling narrative explaining the connection — how does "{a1['title']}" connect to "{a2['title']}"?

Path through the graph:
Nodes: {json.dumps(path_nodes)}
Relationships: {json.dumps(path_rels)}

Write a 2-3 paragraph narrative that tells the story of this connection. Reference the specific people, places, and relationships. Explain *why* this connection matters musically and historically."""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"narrative": msg.content[0].text, "path": path_nodes, "rels": path_rels}


def find_uncharted_territory(user_id: str) -> list[dict]:
    """Find 'Uncharted Territory' — scenes/regions the collection touches but doesn't cover deeply."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(owned:Album)
            MATCH (owned)<-[:PERFORMED_ON]-(artist:Artist)-[:PERFORMED_ON]->(unowned:Album)
            WHERE NOT EXISTS {
                MATCH (u)-[:OWNS]->(:Pressing)<-[:HAS_PRESSING]-(unowned)
            }
            MATCH (unowned)-[:PART_OF_SCENE]->(scene:Scene)
            WITH scene, count(DISTINCT unowned) AS available,
                 collect(DISTINCT artist.name)[..3] AS via_artists,
                 collect(DISTINCT unowned.title)[..5] AS sample_albums
            WHERE available >= 2
            RETURN scene.name AS scene, scene.city AS city,
                   scene.era_start AS era_start, scene.era_end AS era_end,
                   available, via_artists, sample_albums
            ORDER BY available DESC
            LIMIT 10
            """,
            user_id=user_id,
        )
        return [r.data() for r in result]


def generate_temporal_insights(user_id: str) -> dict:
    """Generate temporal insights — what decades define the collection and why."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            WHERE a.year IS NOT NULL
            WITH a.year AS year, collect(a.title) AS albums
            RETURN year, albums, size(albums) AS count
            ORDER BY year
            """,
            user_id=user_id,
        )
        year_data = [r.data() for r in result]

    if not year_data:
        return {"narrative": "Not enough dated records for temporal analysis.", "years": []}

    client = _get_client()
    # Summarize by decade for the prompt
    decades = {}
    for entry in year_data:
        decade = (entry["year"] // 10) * 10
        if decade not in decades:
            decades[decade] = {"count": 0, "sample_albums": []}
        decades[decade]["count"] += entry["count"]
        decades[decade]["sample_albums"].extend(entry["albums"][:3])

    prompt = f"""Analyze the temporal distribution of this vinyl collection and write a brief narrative about what it reveals.

Decade breakdown: {json.dumps(decades)}

Write 1-2 paragraphs about what was happening musically in the decades this collection focuses on, and what it tells us about the collector's interests. Be specific."""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"narrative": msg.content[0].text, "years": year_data, "decades": decades}
