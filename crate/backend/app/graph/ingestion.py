"""Graph ingestion: takes structured record data and creates/updates Neo4j nodes and edges."""

from app.graph import queries


def ingest_record(driver, *, discogs_id: int, synthesized_data: dict, user_id: str | None = None):
    """
    Ingest a fully synthesized record into the Neo4j graph.

    Args:
        driver: Neo4j driver instance
        discogs_id: Discogs release ID
        synthesized_data: Output from AI synthesis (see prompts/smart_add.py for schema)
        user_id: Optional user ID to create OWNS relationship
    """
    album_data = synthesized_data["album"]
    artists = synthesized_data.get("artists", [])
    labels = synthesized_data.get("labels", [])
    genres = synthesized_data.get("genres", [])
    studios = synthesized_data.get("studios", [])
    scenes = synthesized_data.get("scenes", [])
    pressing_data = synthesized_data.get("pressing", {})

    with driver.session() as session:
        # 1. Create Album node
        session.execute_write(
            queries.merge_album,
            title=album_data["title"],
            discogs_id=discogs_id,
            year=album_data.get("year"),
            country=album_data.get("country"),
        )

        # 2. Create Artist nodes and link to album
        for artist in artists:
            artist_props = {}
            if artist.get("musicbrainz_id"):
                artist_props["musicbrainz_id"] = artist["musicbrainz_id"]
            if artist.get("artist_type"):
                artist_props["artist_type"] = artist["artist_type"]

            session.execute_write(
                queries.merge_artist,
                name=artist["name"],
                **artist_props,
            )

            # Link artist to album with role
            role = artist.get("role", "performer")
            link_props = {}
            if artist.get("instrument"):
                link_props["instrument"] = artist["instrument"]
            if artist.get("tracks"):
                link_props["tracks"] = artist["tracks"]

            session.execute_write(
                queries.link_artist_to_album,
                artist_name=artist["name"],
                album_discogs_id=discogs_id,
                role=role,
                **link_props,
            )

            # Link band membership if specified
            if artist.get("member_of"):
                session.execute_write(
                    queries.link_member_of_band,
                    member_name=artist["name"],
                    band_name=artist["member_of"],
                )

            # Link artist to instrument if specified
            if artist.get("instrument"):
                session.execute_write(
                    queries.merge_instrument,
                    name=artist["instrument"],
                )
                session.execute_write(
                    queries.link_artist_to_instrument,
                    artist_name=artist["name"],
                    instrument_name=artist["instrument"],
                )

            # Link artist to origin city if known
            if artist.get("origin_city"):
                session.execute_write(
                    queries.merge_city,
                    name=artist["origin_city"],
                )
                session.execute_write(
                    queries.link_artist_to_city,
                    artist_name=artist["name"],
                    city_name=artist["origin_city"],
                )

        # 3. Create Label nodes and link
        for label in labels:
            session.execute_write(queries.merge_label, name=label["name"])
            session.execute_write(
                queries.link_album_to_label,
                album_discogs_id=discogs_id,
                label_name=label["name"],
                catalog_number=label.get("catalog_number", ""),
            )

        # 4. Create Genre nodes and link
        for genre_name in genres:
            session.execute_write(queries.merge_genre, name=genre_name)
            session.execute_write(
                queries.link_album_to_genre,
                album_discogs_id=discogs_id,
                genre_name=genre_name,
            )

        # 5. Create Studio nodes and link
        for studio in studios:
            session.execute_write(queries.merge_studio, name=studio["name"])
            session.execute_write(
                queries.link_album_to_studio,
                album_discogs_id=discogs_id,
                studio_name=studio["name"],
            )
            if studio.get("city"):
                session.execute_write(queries.merge_city, name=studio["city"])
                session.execute_write(
                    queries.link_studio_to_city,
                    studio_name=studio["name"],
                    city_name=studio["city"],
                )

        # 6. Create Scene nodes and link
        for scene in scenes:
            scene_props = {}
            if scene.get("era_start"):
                scene_props["era_start"] = scene["era_start"]
            if scene.get("era_end"):
                scene_props["era_end"] = scene["era_end"]

            session.execute_write(queries.merge_scene, name=scene["name"], **scene_props)
            session.execute_write(
                queries.link_album_to_scene,
                album_discogs_id=discogs_id,
                scene_name=scene["name"],
            )
            if scene.get("city"):
                session.execute_write(queries.merge_city, name=scene["city"])
                session.execute_write(
                    queries.link_scene_to_city,
                    scene_name=scene["name"],
                    city_name=scene["city"],
                )

        # 7. Create Pressing node and link
        if pressing_data:
            session.execute_write(
                queries.merge_pressing,
                discogs_id=discogs_id,
                country=pressing_data.get("country"),
                year=pressing_data.get("year"),
                format_detail=pressing_data.get("format_detail"),
                matrix_number=pressing_data.get("matrix_number"),
            )
            session.execute_write(
                queries.link_album_to_pressing,
                album_discogs_id=discogs_id,
                pressing_discogs_id=discogs_id,
            )

        # 8. Link user ownership if provided
        if user_id:
            # Ensure user node exists
            session.run(
                "MERGE (u:User {id: $user_id})",
                user_id=user_id,
            )
            session.execute_write(
                queries.link_user_owns_pressing,
                user_id=user_id,
                pressing_discogs_id=discogs_id,
            )


def get_new_connections(driver, *, discogs_id: int, user_id: str) -> list[dict]:
    """After ingesting a record, find what new connections it created in the user's graph."""
    with driver.session() as session:
        result = session.run(
            """
            // Find artists on the new album who also appear on other albums the user owns
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(other:Album)
            WHERE other.discogs_id <> $discogs_id
            MATCH (new:Album {discogs_id: $discogs_id})<-[:PERFORMED_ON]-(shared:Artist)-[:PERFORMED_ON]->(other)
            RETURN shared.name AS shared_artist,
                   collect(DISTINCT other.title) AS also_on,
                   'shared_artist' AS connection_type
            """,
            user_id=user_id,
            discogs_id=discogs_id,
        )
        connections = [record.data() for record in result]

        # Also check shared labels
        result2 = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(other:Album)
            WHERE other.discogs_id <> $discogs_id
            MATCH (new:Album {discogs_id: $discogs_id})-[:RELEASED_ON]->(l:Label)<-[:RELEASED_ON]-(other)
            RETURN l.name AS shared_label,
                   collect(DISTINCT other.title) AS also_on,
                   'shared_label' AS connection_type
            """,
            user_id=user_id,
            discogs_id=discogs_id,
        )
        connections.extend([record.data() for record in result2])

        return connections
