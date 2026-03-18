"""Geographic graph queries for the Sound Map."""

from app.services.geocoding import geocode_city_sync


def get_collection_by_city(tx, *, user_id: str):
    """Get albums grouped by origin city (artist origin or studio location)."""
    result = tx.run(
        """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        OPTIONAL MATCH (a)<-[:PERFORMED_ON]-(ar:Artist)-[:FROM]->(c:City)
        OPTIONAL MATCH (a)-[:RECORDED_AT]->(s:Studio)-[:LOCATED_IN]->(sc:City)
        WITH a, collect(DISTINCT c.name) + collect(DISTINCT sc.name) AS cities
        UNWIND cities AS city
        WITH city, collect(DISTINCT {title: a.title, discogs_id: a.discogs_id, year: a.year}) AS albums
        WHERE city IS NOT NULL
        RETURN city, albums, size(albums) AS count
        ORDER BY count DESC
        """,
        user_id=user_id,
    )
    return [r.data() for r in result]


def get_group_collection_by_city(tx, *, group_id: str):
    """Get the group's combined collection grouped by origin city."""
    result = tx.run(
        """
        MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
        MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        OPTIONAL MATCH (a)<-[:PERFORMED_ON]-(ar:Artist)-[:FROM]->(c:City)
        OPTIONAL MATCH (a)-[:RECORDED_AT]->(s:Studio)-[:LOCATED_IN]->(sc:City)
        WITH a, u, collect(DISTINCT c.name) + collect(DISTINCT sc.name) AS cities
        UNWIND cities AS city
        WITH city,
             collect(DISTINCT {title: a.title, discogs_id: a.discogs_id, owner: u.name}) AS albums
        WHERE city IS NOT NULL
        RETURN city, albums, size(albums) AS count
        ORDER BY count DESC
        """,
        group_id=group_id,
    )
    return [r.data() for r in result]


def get_scenes_by_city(tx, *, city_name: str):
    """Get all scenes associated with a city."""
    result = tx.run(
        """
        MATCH (s:Scene)-[:LOCATED_IN]->(c:City {name: $city_name})
        OPTIONAL MATCH (a:Album)-[:PART_OF_SCENE]->(s)
        RETURN s.name AS scene, s.era_start AS era_start, s.era_end AS era_end,
               collect(DISTINCT a.title) AS albums, count(DISTINCT a) AS album_count
        ORDER BY s.era_start
        """,
        city_name=city_name,
    )
    return [r.data() for r in result]


def build_sound_map_data(tx, *, user_id: str | None = None, group_id: str | None = None):
    """Build the full Sound Map dataset with geocoded points."""
    if group_id:
        city_data = get_group_collection_by_city(tx, group_id=group_id)
    elif user_id:
        city_data = get_collection_by_city(tx, user_id=user_id)
    else:
        return []

    points = []
    for entry in city_data:
        coords = geocode_city_sync(entry["city"])
        if coords:
            lat, lng = coords
            points.append({
                "city": entry["city"],
                "lat": lat,
                "lng": lng,
                "count": entry["count"],
                "albums": entry["albums"][:20],  # Cap for response size
            })

    return points
