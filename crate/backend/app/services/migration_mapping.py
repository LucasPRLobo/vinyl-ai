"""Migration Mapping: track how people, sounds, and ideas moved geographically."""

import json
import logging

import anthropic

from app.config import settings
from app.graph.connection import get_neo4j_driver
from app.services.geocoding import geocode_city_sync

logger = logging.getLogger(__name__)


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def find_artist_migrations(user_id: str | None = None, group_id: str | None = None) -> list[dict]:
    """Find artists in the collection who appear in records from multiple cities."""
    driver = get_neo4j_driver()

    if group_id:
        scope = "MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $scope_id}) MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)"
        scope_id = group_id
    else:
        scope = "MATCH (u:User {id: $scope_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)"
        scope_id = user_id or "default-user"

    with driver.session() as session:
        result = session.run(
            f"""
            {scope}
            MATCH (ar:Artist)-[:PERFORMED_ON]->(a)
            OPTIONAL MATCH (a)-[:RECORDED_AT]->(s:Studio)-[:LOCATED_IN]->(c:City)
            OPTIONAL MATCH (ar)-[:FROM]->(origin:City)
            WITH ar, origin,
                 collect(DISTINCT {{city: c.name, album: a.title, year: a.year}}) AS appearances
            WHERE size(appearances) >= 2
            WITH ar.name AS artist, origin.name AS origin_city,
                 [x IN appearances WHERE x.city IS NOT NULL] AS city_appearances
            WHERE size(city_appearances) >= 2
            RETURN artist, origin_city, city_appearances
            ORDER BY size(city_appearances) DESC
            LIMIT 15
            """,
            scope_id=scope_id,
        )
        migrations = []
        for r in result:
            d = r.data()
            # Build path with geocoding
            cities_seen = {}
            path = []
            for app in sorted(d["city_appearances"], key=lambda x: x.get("year") or 9999):
                city = app["city"]
                if city and city not in cities_seen:
                    coords = geocode_city_sync(city)
                    if coords:
                        cities_seen[city] = True
                        path.append({
                            "city": city,
                            "lat": coords[0],
                            "lng": coords[1],
                            "album": app["album"],
                            "year": app.get("year"),
                        })

            if len(path) >= 2:
                migrations.append({
                    "artist": d["artist"],
                    "origin": d["origin_city"],
                    "path": path,
                    "city_count": len(path),
                })

        return migrations


def find_genre_migrations(user_id: str | None = None, group_id: str | None = None) -> list[dict]:
    """Find how genres spread across cities in the collection."""
    driver = get_neo4j_driver()

    if group_id:
        scope = "MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $scope_id}) MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)"
        scope_id = group_id
    else:
        scope = "MATCH (u:User {id: $scope_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)"
        scope_id = user_id or "default-user"

    with driver.session() as session:
        result = session.run(
            f"""
            {scope}
            MATCH (a)-[:HAS_GENRE]->(g:Genre)
            MATCH (a)<-[:PERFORMED_ON]-(ar:Artist)-[:FROM]->(c:City)
            WITH g.name AS genre, c.name AS city, min(a.year) AS earliest_year,
                 count(DISTINCT a) AS album_count, collect(DISTINCT a.title)[..3] AS sample_albums
            WITH genre, collect({{city: city, year: earliest_year, count: album_count, albums: sample_albums}}) AS cities
            WHERE size(cities) >= 2
            RETURN genre, cities
            ORDER BY size(cities) DESC
            LIMIT 10
            """,
            scope_id=scope_id,
        )
        migrations = []
        for r in result:
            d = r.data()
            # Build geocoded path sorted by earliest year
            path = []
            for city_data in sorted(d["cities"], key=lambda x: x.get("year") or 9999):
                coords = geocode_city_sync(city_data["city"])
                if coords:
                    path.append({
                        "city": city_data["city"],
                        "lat": coords[0],
                        "lng": coords[1],
                        "year": city_data["year"],
                        "album_count": city_data["count"],
                        "sample_albums": city_data["albums"],
                    })

            if len(path) >= 2:
                migrations.append({
                    "genre": d["genre"],
                    "path": path,
                    "city_count": len(path),
                })

        return migrations


def generate_migration_narrative(migration: dict, migration_type: str = "artist") -> str:
    """Generate an AI narrative for a specific migration path."""
    client = _get_client()

    if migration_type == "artist":
        prompt = f"""An artist's musical journey across cities, based on records in a vinyl collection:

Artist: {migration['artist']}
Origin: {migration.get('origin', 'Unknown')}
Path: {json.dumps(migration['path'], indent=2)}

Write a 2-3 paragraph narrative tracing this artist's journey. How did each city change their music? What did they bring to each scene? Reference the specific albums."""
    else:
        prompt = f"""A genre's migration across cities, based on records in a vinyl collection:

Genre: {migration['genre']}
Path: {json.dumps(migration['path'], indent=2)}

Write a 2-3 paragraph narrative explaining how this genre traveled between these cities. What changed at each stop? Who carried the sound? Reference specific albums from the collection."""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
