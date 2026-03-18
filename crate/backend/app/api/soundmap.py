"""Sound Map API routes."""

from fastapi import APIRouter, Depends

from app.graph.connection import get_neo4j_driver
from app.graph.geographic import build_sound_map_data, get_scenes_by_city
from app.dependencies import get_user_id

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/sound")
def sound_map(uid: str = Depends(get_user_id), group_id: str | None = None):
    driver = get_neo4j_driver()
    with driver.session() as session:
        return session.execute_read(
            build_sound_map_data, user_id=uid if not group_id else None, group_id=group_id
        )


@router.get("/city/{city_name}")
def city_detail(city_name: str):
    driver = get_neo4j_driver()
    with driver.session() as session:
        scenes = session.execute_read(get_scenes_by_city, city_name=city_name)
        result = session.run(
            """
            MATCH (a:Artist)-[:FROM]->(c:City {name: $city_name})
            OPTIONAL MATCH (a)-[:PERFORMED_ON]->(al:Album)
            RETURN a.name AS artist, collect(DISTINCT al.title)[..5] AS albums
            ORDER BY size(collect(DISTINCT al.title)) DESC
            LIMIT 20
            """,
            city_name=city_name,
        )
        artists = [r.data() for r in result]
    return {"city": city_name, "scenes": scenes, "artists": artists}
