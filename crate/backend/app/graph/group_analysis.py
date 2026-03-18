"""Cross-collection group analysis: overlap, bridges, blind spots, taste distance."""


def group_collection_overlap(tx, *, group_id: str):
    """Albums owned by multiple members. Merges different pressings by title."""
    result = tx.run(
        """
        MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
        MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        WITH a.title AS title, collect(DISTINCT a.discogs_id) AS discogs_ids,
             collect(DISTINCT u.name) AS owners, count(DISTINCT u) AS owner_count
        WHERE owner_count > 1
        RETURN title, discogs_ids[0] AS discogs_id, owners, owner_count
        ORDER BY owner_count DESC
        LIMIT 50
        """,
        group_id=group_id,
    )
    return [r.data() for r in result]


def group_unique_to_member(tx, *, group_id: str, user_id: str):
    """Albums that only this member owns (their unique contribution to the group)."""
    result = tx.run(
        """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        WHERE NOT EXISTS {
            MATCH (other:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
            WHERE other.id <> $user_id
            MATCH (other)-[:OWNS]->(:Pressing)<-[:HAS_PRESSING]-(a)
        }
        RETURN a.title AS title, a.discogs_id AS discogs_id
        LIMIT 50
        """,
        group_id=group_id,
        user_id=user_id,
    )
    return [r.data() for r in result]


def group_bridges(tx, *, group_id: str):
    """Find members who are the sole connection between different areas of the group graph.
    A 'bridge' member connects genres/scenes that no other member covers."""
    result = tx.run(
        """
        MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
        MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)-[:HAS_GENRE]->(genre:Genre)
        WITH u, collect(DISTINCT genre.name) AS genres
        RETURN u.name AS member, u.id AS user_id, genres, size(genres) AS genre_count
        ORDER BY genre_count DESC
        """,
        group_id=group_id,
    )
    members = [r.data() for r in result]

    # Find genres only one person covers
    genre_owners = {}
    for m in members:
        for g in m["genres"]:
            if g not in genre_owners:
                genre_owners[g] = []
            genre_owners[g].append(m["member"])

    bridges = []
    for m in members:
        unique_genres = [g for g in m["genres"] if len(genre_owners.get(g, [])) == 1]
        if unique_genres:
            bridges.append({
                "member": m["member"],
                "user_id": m["user_id"],
                "unique_genres": unique_genres,
                "total_genres": m["genre_count"],
            })

    return bridges


def group_blind_spots(tx, *, group_id: str):
    """Find scenes/genres adjacent to the group's collection but not covered.
    Looks at what the group's artists have done outside the group's collection."""
    result = tx.run(
        """
        MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
        MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(owned:Album)
        MATCH (owned)<-[:PERFORMED_ON]-(artist:Artist)-[:PERFORMED_ON]->(unowned:Album)
        WHERE NOT EXISTS {
            MATCH (any_user:User)-[:MEMBER_OF_GROUP]->(g)
            MATCH (any_user)-[:OWNS]->(:Pressing)<-[:HAS_PRESSING]-(unowned)
        }
        MATCH (unowned)-[:HAS_GENRE]->(genre:Genre)
        WITH genre.name AS genre, count(DISTINCT unowned) AS available_albums,
             collect(DISTINCT artist.name)[..3] AS via_artists
        WHERE available_albums >= 2
        RETURN genre, available_albums, via_artists
        ORDER BY available_albums DESC
        LIMIT 20
        """,
        group_id=group_id,
    )
    return [r.data() for r in result]


def group_taste_distance(tx, *, group_id: str):
    """Calculate taste similarity between group members based on genre overlap."""
    result = tx.run(
        """
        MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
        MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)-[:HAS_GENRE]->(genre:Genre)
        WITH u.name AS member, u.id AS user_id, collect(DISTINCT genre.name) AS genres
        RETURN member, user_id, genres
        """,
        group_id=group_id,
    )
    members = [r.data() for r in result]

    # Calculate Jaccard similarity between each pair
    distances = []
    for i, m1 in enumerate(members):
        for m2 in members[i + 1:]:
            s1 = set(m1["genres"])
            s2 = set(m2["genres"])
            intersection = len(s1 & s2)
            union = len(s1 | s2)
            similarity = intersection / union if union > 0 else 0
            distances.append({
                "member_1": m1["member"],
                "member_2": m2["member"],
                "similarity": round(similarity, 2),
                "shared_genres": sorted(s1 & s2),
                "unique_to_1": sorted(s1 - s2),
                "unique_to_2": sorted(s2 - s1),
            })

    return sorted(distances, key=lambda d: d["similarity"], reverse=True)


def group_stats(tx, *, group_id: str):
    """Aggregate stats for the group's combined collection."""
    result = tx.run(
        """
        MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
        MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        OPTIONAL MATCH (a)-[:HAS_GENRE]->(genre:Genre)
        OPTIONAL MATCH (a)-[:RELEASED_ON]->(l:Label)
        OPTIONAL MATCH (a)<-[:PERFORMED_ON]-(ar:Artist)
        RETURN count(DISTINCT a) AS total_albums,
               count(DISTINCT ar) AS total_artists,
               count(DISTINCT l) AS total_labels,
               count(DISTINCT genre) AS total_genres,
               count(DISTINCT u) AS total_members,
               collect(DISTINCT genre.name) AS genres
        """,
        group_id=group_id,
    )
    return result.single().data()
