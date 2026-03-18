from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.graph.connection import get_neo4j_driver, close_neo4j_driver
from app.graph.schema import ensure_schema
from app.models.database import engine, Base
from app.api.collection import router as collection_router
from app.api.query import router as query_router
from app.api.graph import router as graph_router
from app.api.insights import router as insights_router
from app.api.auth import router as auth_router
from app.api.groups import router as groups_router
from app.api.feed import router as feed_router
from app.api.annotations import router as annotations_router
from app.api.group_insights import router as group_insights_router
from app.api.soundmap import router as soundmap_router
from app.api.stores import router as stores_router
from app.api.deep_insights import router as deep_insights_router
from app.api.sessions import router as sessions_router
from app.api.historian import router as historian_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    driver = get_neo4j_driver()
    await ensure_schema(driver)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    close_neo4j_driver()
    await engine.dispose()


app = FastAPI(
    title="Crate",
    description="A collectively-built map of music history — one record at a time.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for tunnel access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(collection_router)
app.include_router(query_router)
app.include_router(graph_router)
app.include_router(insights_router)
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(feed_router)
app.include_router(annotations_router)
app.include_router(group_insights_router)
app.include_router(soundmap_router)
app.include_router(stores_router)
app.include_router(deep_insights_router)
app.include_router(sessions_router)
app.include_router(historian_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
