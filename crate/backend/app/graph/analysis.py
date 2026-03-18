"""Graph analysis algorithms for insights, pattern discovery, and connections."""


def get_hub_nodes(tx, *, label: str = "Artist", limit: int = 10):
    """Find the most connected nodes of a given type."""
    result = tx.run(
        f"""
        MATCH (n:{label})-[r]-()
        RETURN n.name AS name, count(r) AS connections, labels(n) AS labels
        ORDER BY connections DESC
        LIMIT $limit
        """,
        limit=limit,
    )
    return [record.data() for record in result]


def get_collection_stats(tx, *, user_id: str):
    """Get stats about a user's collection."""
    result = tx.run(
        """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        OPTIONAL MATCH (a)-[:HAS_GENRE]->(g:Genre)
        OPTIONAL MATCH (a)-[:RELEASED_ON]->(l:Label)
        OPTIONAL MATCH (a)<-[:PERFORMED_ON]-(ar:Artist)
        RETURN count(DISTINCT a) AS total_albums,
               count(DISTINCT ar) AS total_artists,
               count(DISTINCT l) AS total_labels,
               count(DISTINCT g) AS total_genres,
               collect(DISTINCT g.name) AS genres,
               collect(DISTINCT l.name) AS labels
        """,
        user_id=user_id,
    )
    return result.single().data()


def find_shared_personnel(tx, *, user_id: str):
    """Find artists who appear on multiple albums in a user's collection."""
    result = tx.run(
        """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        MATCH (ar:Artist)-[:PERFORMED_ON]->(a)
        WITH ar, collect(DISTINCT a.title) AS albums, count(DISTINCT a) AS album_count
        WHERE album_count > 1
        RETURN ar.name AS artist, albums, album_count
        ORDER BY album_count DESC
        """,
        user_id=user_id,
    )
    return [record.data() for record in result]


def find_collection_clusters(tx, *, user_id: str):
    """Find clusters of connected albums in a user's collection."""
    result = tx.run(
        """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        MATCH (a)-[:HAS_GENRE]->(g:Genre)
        WITH g.name AS genre, collect(a.title) AS albums, count(a) AS count
        RETURN genre, albums, count
        ORDER BY count DESC
        """,
        user_id=user_id,
    )
    return [record.data() for record in result]


def find_outlier(tx, *, user_id: str):
    """Find the most disconnected album in a user's collection."""
    result = tx.run(
        """
        MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        OPTIONAL MATCH (a)-[r]-()
        WITH a, count(r) AS connections
        RETURN a.title AS title, a.discogs_id AS discogs_id, connections
        ORDER BY connections ASC
        LIMIT 5
        """,
        user_id=user_id,
    )
    return [record.data() for record in result]


def cross_collection_overlap(tx, *, group_id: str):
    """Find albums owned by multiple members of a group."""
    result = tx.run(
        """
        MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
        MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
        WITH a, collect(DISTINCT u.name) AS owners, count(DISTINCT u) AS owner_count
        WHERE owner_count > 1
        RETURN a.title AS title, owners, owner_count
        ORDER BY owner_count DESC
        """,
        group_id=group_id,
    )
    return [record.data() for record in result]
