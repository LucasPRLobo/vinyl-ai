"""Core Cypher query builders for the Crate knowledge graph."""


def merge_artist(tx, *, name: str, musicbrainz_id: str | None = None, **props):
    """Create or update an Artist node. Matches on musicbrainz_id if available, else name."""
    if musicbrainz_id:
        result = tx.run(
            """
            MERGE (a:Artist {musicbrainz_id: $musicbrainz_id})
            ON CREATE SET a.name = $name, a += $props
            ON MATCH SET a += $props
            RETURN a
            """,
            musicbrainz_id=musicbrainz_id,
            name=name,
            props=props,
        )
    else:
        result = tx.run(
            """
            MERGE (a:Artist {name: $name})
            ON CREATE SET a += $props
            ON MATCH SET a += $props
            RETURN a
            """,
            name=name,
            props=props,
        )
    return result.single()


def merge_album(tx, *, title: str, discogs_id: int | None = None, **props):
    """Create or update an Album node."""
    if discogs_id:
        result = tx.run(
            """
            MERGE (a:Album {discogs_id: $discogs_id})
            ON CREATE SET a.title = $title, a += $props
            ON MATCH SET a += $props
            RETURN a
            """,
            discogs_id=discogs_id,
            title=title,
            props=props,
        )
    else:
        result = tx.run(
            """
            MERGE (a:Album {title: $title})
            ON CREATE SET a += $props
            ON MATCH SET a += $props
            RETURN a
            """,
            title=title,
            props=props,
        )
    return result.single()


def merge_label(tx, *, name: str, discogs_id: int | None = None, **props):
    if discogs_id:
        result = tx.run(
            """
            MERGE (l:Label {discogs_id: $discogs_id})
            ON CREATE SET l.name = $name, l += $props
            ON MATCH SET l += $props
            RETURN l
            """,
            discogs_id=discogs_id,
            name=name,
            props=props,
        )
    else:
        result = tx.run(
            """
            MERGE (l:Label {name: $name})
            ON CREATE SET l += $props
            ON MATCH SET l += $props
            RETURN l
            """,
            name=name,
            props=props,
        )
    return result.single()


def merge_genre(tx, *, name: str):
    result = tx.run("MERGE (g:Genre {name: $name}) RETURN g", name=name)
    return result.single()


def merge_city(tx, *, name: str, country: str | None = None, **props):
    result = tx.run(
        """
        MERGE (c:City {name: $name})
        ON CREATE SET c += $props
        ON MATCH SET c += $props
        RETURN c
        """,
        name=name,
        props={"country": country, **props} if country else props,
    )
    return result.single()


def merge_studio(tx, *, name: str, **props):
    result = tx.run(
        """
        MERGE (s:Studio {name: $name})
        ON CREATE SET s += $props
        ON MATCH SET s += $props
        RETURN s
        """,
        name=name,
        props=props,
    )
    return result.single()


def merge_instrument(tx, *, name: str):
    result = tx.run("MERGE (i:Instrument {name: $name}) RETURN i", name=name)
    return result.single()


def merge_scene(tx, *, name: str, **props):
    result = tx.run(
        """
        MERGE (s:Scene {name: $name})
        ON CREATE SET s += $props
        ON MATCH SET s += $props
        RETURN s
        """,
        name=name,
        props=props,
    )
    return result.single()


def merge_pressing(tx, *, discogs_id: int, **props):
    result = tx.run(
        """
        MERGE (p:Pressing {discogs_id: $discogs_id})
        ON CREATE SET p += $props
        ON MATCH SET p += $props
        RETURN p
        """,
        discogs_id=discogs_id,
        props=props,
    )
    return result.single()


def merge_track(tx, *, album_discogs_id: int, position: str, title: str, **props):
    result = tx.run(
        """
        MATCH (a:Album {discogs_id: $album_discogs_id})
        MERGE (t:Track {title: $title, album_discogs_id: $album_discogs_id})
        ON CREATE SET t.position = $position, t += $props
        MERGE (a)-[:HAS_TRACK {position: $position}]->(t)
        RETURN t
        """,
        album_discogs_id=album_discogs_id,
        position=position,
        title=title,
        props=props,
    )
    return result.single()


# --- Relationship creators ---


def link_artist_to_album(tx, *, artist_name: str, album_discogs_id: int, role: str, **props):
    """Link an artist to an album with a specific role."""
    rel_type = {
        "performer": "PERFORMED_ON",
        "main_artist": "MAIN_ARTIST",
        "producer": "PRODUCED",
        "engineer": "ENGINEERED",
        "writer": "WROTE",
    }.get(role, "PERFORMED_ON")

    tx.run(
        f"""
        MATCH (ar:Artist {{name: $artist_name}})
        MATCH (al:Album {{discogs_id: $album_discogs_id}})
        MERGE (ar)-[r:{rel_type}]->(al)
        SET r += $props
        """,
        artist_name=artist_name,
        album_discogs_id=album_discogs_id,
        props=props,
    )


def link_member_of_band(tx, *, member_name: str, band_name: str):
    """Link an artist as a member of a band/group."""
    tx.run(
        """
        MATCH (member:Artist {name: $member_name})
        MATCH (band:Artist {name: $band_name})
        MERGE (member)-[:MEMBER_OF]->(band)
        """,
        member_name=member_name,
        band_name=band_name,
    )


def link_album_to_label(tx, *, album_discogs_id: int, label_name: str, **props):
    tx.run(
        """
        MATCH (a:Album {discogs_id: $album_discogs_id})
        MATCH (l:Label {name: $label_name})
        MERGE (a)-[r:RELEASED_ON]->(l)
        SET r += $props
        """,
        album_discogs_id=album_discogs_id,
        label_name=label_name,
        props=props,
    )


def link_album_to_genre(tx, *, album_discogs_id: int, genre_name: str):
    tx.run(
        """
        MATCH (a:Album {discogs_id: $album_discogs_id})
        MATCH (g:Genre {name: $genre_name})
        MERGE (a)-[:HAS_GENRE]->(g)
        """,
        album_discogs_id=album_discogs_id,
        genre_name=genre_name,
    )


def link_album_to_studio(tx, *, album_discogs_id: int, studio_name: str):
    tx.run(
        """
        MATCH (a:Album {discogs_id: $album_discogs_id})
        MATCH (s:Studio {name: $studio_name})
        MERGE (a)-[:RECORDED_AT]->(s)
        """,
        album_discogs_id=album_discogs_id,
        studio_name=studio_name,
    )


def link_album_to_scene(tx, *, album_discogs_id: int, scene_name: str):
    tx.run(
        """
        MATCH (a:Album {discogs_id: $album_discogs_id})
        MATCH (s:Scene {name: $scene_name})
        MERGE (a)-[:PART_OF_SCENE]->(s)
        """,
        album_discogs_id=album_discogs_id,
        scene_name=scene_name,
    )


def link_album_to_pressing(tx, *, album_discogs_id: int, pressing_discogs_id: int):
    tx.run(
        """
        MATCH (a:Album {discogs_id: $album_discogs_id})
        MATCH (p:Pressing {discogs_id: $pressing_discogs_id})
        MERGE (a)-[:HAS_PRESSING]->(p)
        """,
        album_discogs_id=album_discogs_id,
        pressing_discogs_id=pressing_discogs_id,
    )


def link_artist_to_instrument(tx, *, artist_name: str, instrument_name: str):
    tx.run(
        """
        MATCH (a:Artist {name: $artist_name})
        MATCH (i:Instrument {name: $instrument_name})
        MERGE (a)-[:PLAYS]->(i)
        """,
        artist_name=artist_name,
        instrument_name=instrument_name,
    )


def link_artist_to_city(tx, *, artist_name: str, city_name: str):
    tx.run(
        """
        MATCH (a:Artist {name: $artist_name})
        MATCH (c:City {name: $city_name})
        MERGE (a)-[:FROM]->(c)
        """,
        artist_name=artist_name,
        city_name=city_name,
    )


def link_studio_to_city(tx, *, studio_name: str, city_name: str):
    tx.run(
        """
        MATCH (s:Studio {name: $studio_name})
        MATCH (c:City {name: $city_name})
        MERGE (s)-[:LOCATED_IN]->(c)
        """,
        studio_name=studio_name,
        city_name=city_name,
    )


def link_scene_to_city(tx, *, scene_name: str, city_name: str):
    tx.run(
        """
        MATCH (s:Scene {name: $scene_name})
        MATCH (c:City {name: $city_name})
        MERGE (s)-[:LOCATED_IN]->(c)
        """,
        scene_name=scene_name,
        city_name=city_name,
    )


def link_user_owns_pressing(tx, *, user_id: str, pressing_discogs_id: int, **props):
    tx.run(
        """
        MATCH (u:User {id: $user_id})
        MATCH (p:Pressing {discogs_id: $pressing_discogs_id})
        MERGE (u)-[r:OWNS]->(p)
        SET r += $props
        """,
        user_id=user_id,
        pressing_discogs_id=pressing_discogs_id,
        props=props,
    )


# --- Query helpers ---


def get_album_connections(tx, *, album_discogs_id: int):
    """Get all nodes connected to an album within 2 hops."""
    result = tx.run(
        """
        MATCH (a:Album {discogs_id: $album_discogs_id})-[r]-(connected)
        RETURN type(r) AS rel_type, labels(connected) AS labels,
               properties(connected) AS props, properties(r) AS rel_props
        """,
        album_discogs_id=album_discogs_id,
    )
    return [record.data() for record in result]


def find_connections_between(tx, *, album_id_1: int, album_id_2: int, max_depth: int = 5):
    """Find shortest path between two albums."""
    result = tx.run(
        """
        MATCH (a1:Album {discogs_id: $id1}), (a2:Album {discogs_id: $id2})
        MATCH path = shortestPath((a1)-[*..{max_depth}]-(a2))
        RETURN [n IN nodes(path) | {labels: labels(n), props: properties(n)}] AS nodes,
               [r IN relationships(path) | {type: type(r), props: properties(r)}] AS rels
        """.replace("{max_depth}", str(max_depth)),
        id1=album_id_1,
        id2=album_id_2,
    )
    return [record.data() for record in result]


def get_user_collection(tx, *, user_id: str):
    """Get all albums owned by a user."""
    result = tx.run(
        """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        OPTIONAL MATCH (a)<-[:PERFORMED_ON]-(artist:Artist)
        RETURN a.discogs_id AS discogs_id, a.title AS title, a.year AS year,
               collect(DISTINCT artist.name) AS artists
        ORDER BY a.year
        """,
        user_id=user_id,
    )
    return [record.data() for record in result]
