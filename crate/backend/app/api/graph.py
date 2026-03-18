"""Graph exploration API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.graph.connection import get_neo4j_driver
from app.graph.analysis import (
    get_collection_stats,
    find_shared_personnel,
    get_hub_nodes,
    find_collection_clusters,
    find_outlier,
)
from app.graph.queries import find_connections_between
from app.dependencies import get_user_id

router = APIRouter(prefix="/graph", tags=["graph"])


class ExploreRequest(BaseModel):
    node_label: str
    node_name: str
    depth: int = 1


class PathRequest(BaseModel):
    album_id_1: int
    album_id_2: int
    max_depth: int = 5


@router.get("/stats")
def collection_stats(uid: str = Depends(get_user_id)):
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(get_collection_stats, user_id=uid)


@router.get("/shared-personnel")
def shared_personnel(uid: str = Depends(get_user_id)):
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(find_shared_personnel, user_id=uid)


@router.get("/hubs")
def hub_nodes(label: str = "Artist", limit: int = 15):
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(get_hub_nodes, label=label, limit=limit)


@router.get("/clusters")
def clusters(uid: str = Depends(get_user_id)):
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(find_collection_clusters, user_id=uid)


@router.get("/outliers")
def outliers(uid: str = Depends(get_user_id)):
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(find_outlier, user_id=uid)


@router.post("/explore")
def explore(req: ExploreRequest):
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            f"""
            MATCH (n:{req.node_label} {{name: $name}})-[r]-(connected)
            RETURN n.name AS source,
                   type(r) AS relationship,
                   labels(connected) AS target_labels,
                   coalesce(connected.name, connected.title) AS target_name,
                   properties(connected) AS target_props,
                   properties(r) AS rel_props
            """,
            name=req.node_name,
        )
        connections = [record.data() for record in result]
    return {"node": req.node_name, "label": req.node_label, "connections": connections}


@router.post("/path")
def find_path(req: PathRequest):
    driver = get_neo4j_driver()
    with driver.session() as session:
        paths = session.execute_read(
            find_connections_between,
            album_id_1=req.album_id_1,
            album_id_2=req.album_id_2,
            max_depth=req.max_depth,
        )
    return {"paths": paths}


@router.get("/full")
def full_graph(uid: str = Depends(get_user_id), limit: int = 200):
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            MATCH (a)-[r]-(connected)
            WITH collect(DISTINCT {
                id: elementId(a),
                label: 'Album',
                name: a.title,
                props: properties(a)
            }) AS album_nodes,
            collect(DISTINCT {
                id: elementId(connected),
                label: head(labels(connected)),
                name: coalesce(connected.name, connected.title),
                props: properties(connected)
            }) AS connected_nodes,
            collect(DISTINCT {
                source: elementId(a),
                target: elementId(connected),
                type: type(r),
                props: properties(r)
            }) AS edges
            RETURN album_nodes, connected_nodes, edges
            """,
            user_id=uid,
        )
        record = result.single()
        if not record:
            return {"nodes": [], "edges": []}

        album_nodes = record["album_nodes"]
        connected_nodes = record["connected_nodes"]
        edges = record["edges"]

        seen = set()
        nodes = []
        for n in album_nodes + connected_nodes:
            if n["id"] not in seen:
                seen.add(n["id"])
                nodes.append(n)

        return {"nodes": nodes[:limit], "edges": edges}


@router.get("/group/{group_id}")
def group_graph(group_id: str, limit: int = 500):
    """Get the combined graph for a group.
    Albums with the same title are merged (different pressings = same music).
    Each merged album node includes all owners across pressings."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Step 1: Get all albums with their owners (per album node)
        album_result = session.run(
            """
            MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
            MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            RETURN elementId(a) AS eid, a.title AS title, a.discogs_id AS discogs_id,
                   a.year AS year, u.name AS owner_name, u.id AS owner_id
            """,
            group_id=group_id,
        )
        album_rows = [r.data() for r in album_result]

        if not album_rows:
            return {"nodes": [], "edges": [], "members": []}

        # Step 2: Get connections for all albums in the group
        conn_result = session.run(
            """
            MATCH (u:User)-[:MEMBER_OF_GROUP]->(g:Group {id: $group_id})
            MATCH (u)-[:OWNS]->(p:Pressing)<-[:HAS_PRESSING]-(a:Album)
            MATCH (a)-[r]-(connected)
            WHERE NOT connected:Pressing AND NOT connected:User
            RETURN elementId(a) AS album_eid, a.title AS album_title,
                   elementId(connected) AS conn_eid,
                   head(labels(connected)) AS conn_label,
                   coalesce(connected.name, connected.title) AS conn_name,
                   properties(connected) AS conn_props,
                   type(r) AS rel_type, properties(r) AS rel_props
            """,
            group_id=group_id,
        )
        conn_rows = [r.data() for r in conn_result]

    # Step 3: Merge albums by title in Python
    # Group by title → merge owners, pick representative eid
    from collections import defaultdict

    title_map = defaultdict(lambda: {"eids": set(), "owners": {}, "discogs_ids": [], "year": None, "rep_eid": None})
    for row in album_rows:
        t = row["title"]
        entry = title_map[t]
        entry["eids"].add(row["eid"])
        entry["owners"][row["owner_id"]] = row["owner_name"]
        entry["discogs_ids"].append(row["discogs_id"])
        if entry["year"] is None:
            entry["year"] = row["year"]
        if entry["rep_eid"] is None:
            entry["rep_eid"] = row["eid"]

    # Map old album eids → merged title key
    eid_to_title = {}
    for title, entry in title_map.items():
        for eid in entry["eids"]:
            eid_to_title[eid] = title

    all_members = {}
    nodes = []
    seen_nodes = set()
    edges = []

    # Add merged album nodes
    for title, entry in title_map.items():
        rep_eid = entry["rep_eid"]
        owner_ids = list(entry["owners"].keys())
        owner_names = list(entry["owners"].values())

        for oid, oname in entry["owners"].items():
            all_members[oid] = oname

        # Use title as the stable node ID (since we're merging)
        node_id = f"album:{title}"
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append({
                "id": node_id,
                "label": "Album",
                "name": title,
                "props": {
                    "discogs_id": entry["discogs_ids"][0],
                    "year": entry["year"],
                },
                "owners": owner_names,
                "owner_ids": owner_ids,
                "shared": len(owner_ids) > 1,
            })

    # Add connected nodes and edges (remapping album eids to merged title IDs)
    for row in conn_rows:
        album_title = row["album_title"]
        merged_album_id = f"album:{album_title}"
        conn_eid = row["conn_eid"]

        # Add connected node
        if conn_eid not in seen_nodes:
            seen_nodes.add(conn_eid)
            nodes.append({
                "id": conn_eid,
                "label": row["conn_label"],
                "name": row["conn_name"],
                "props": row["conn_props"],
                "owners": [],
                "owner_ids": [],
                "shared": False,
            })

        edges.append({
            "source": merged_album_id,
            "target": conn_eid,
            "type": row["rel_type"],
            "props": row["rel_props"],
        })

    # Deduplicate edges
    seen_edges = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"], e["type"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    member_colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ec4899", "#a855f7",
                     "#06b6d4", "#f97316", "#84cc16", "#ef4444", "#8b5cf6"]
    members = [
        {"id": mid, "name": mname, "color": member_colors[i % len(member_colors)]}
        for i, (mid, mname) in enumerate(all_members.items())
    ]

    return {
        "nodes": nodes[:limit],
        "edges": unique_edges,
        "members": members,
    }
