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
