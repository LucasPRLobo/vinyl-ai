"""Collection management API routes."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.connection import get_neo4j_driver
from app.graph.queries import get_user_collection, get_album_connections
from app.models.database import get_db
from app.services.smart_add import search, research_and_ingest
from app.services.discogs_csv import parse_csv, import_collection_from_csv
from app.services.feed import create_record_added_event, get_user_group_ids
from app.tasks.smart_add_task import smart_add_task
from app.dependencies import get_user_id

router = APIRouter(prefix="/collection", tags=["collection"])


# --- Request/Response models ---


class SearchRequest(BaseModel):
    artist: str
    title: str


class SearchResultResponse(BaseModel):
    discogs_id: int
    title: str
    artist: str
    year: int | None = None
    country: str | None = None
    cover_url: str | None = None
    musicbrainz_id: str | None = None


class AddRequest(BaseModel):
    discogs_id: int
    musicbrainz_id: str | None = None


class AddResponse(BaseModel):
    album_title: str
    discogs_id: int
    artists_added: int
    connections_found: list[dict]
    insights: list[dict] | None = None


class CollectionItem(BaseModel):
    discogs_id: int
    title: str
    year: int | None
    artists: list[str]


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None


class ImportCSVResponse(BaseModel):
    total_in_csv: int
    imported: int
    errors: int
    mode: str


# --- Routes ---


@router.post("/search", response_model=list[SearchResultResponse])
def search_release(req: SearchRequest):
    """Search for a release by artist and title. Returns candidates for confirmation."""
    results = search(req.artist, req.title)
    return [
        SearchResultResponse(
            discogs_id=r.discogs_id,
            title=r.title,
            artist=r.artist,
            year=r.year,
            country=r.country,
            cover_url=r.cover_url,
            musicbrainz_id=r.musicbrainz_id,
        )
        for r in results
    ]


@router.post("/add", response_model=AddResponse)
async def add_record(
    req: AddRequest,
    uid: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Smart Add: research a confirmed release and ingest into the knowledge graph."""
    try:
        result = research_and_ingest(
            discogs_id=req.discogs_id,
            musicbrainz_id=req.musicbrainz_id,
            user_id=uid,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart Add failed: {e}")

    # Create feed events for all groups the user belongs to
    try:
        group_ids = await get_user_group_ids(db, uid)
        # Get user name from Neo4j
        driver = get_neo4j_driver()
        with driver.session() as session:
            user_rec = session.run("MATCH (u:User {id: $uid}) RETURN u.name AS name", uid=uid).single()
        user_name = user_rec["name"] if user_rec else "Someone"

        await create_record_added_event(
            db=db,
            user_id=uid,
            user_name=user_name,
            album_title=result.album_title,
            discogs_id=result.discogs_id,
            artists_added=result.artists_added,
            connections=result.connections_found,
            group_ids=group_ids if group_ids else None,
        )
    except Exception as feed_err:
        import logging
        logging.getLogger(__name__).error(f"Feed event creation failed: {feed_err}", exc_info=True)

    return AddResponse(
        album_title=result.album_title,
        discogs_id=result.discogs_id,
        artists_added=result.artists_added,
        connections_found=result.connections_found,
    )


@router.get("/", response_model=list[CollectionItem])
def list_collection(uid: str = Depends(get_user_id)):
    """List all records in a user's collection."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        albums = session.execute_read(get_user_collection, user_id=uid)
    return [CollectionItem(**a) for a in albums]


@router.get("/record/{discogs_id}")
def get_record(discogs_id: int):
    """Get a single record with all its graph connections and lazily-generated context."""
    from app.services.context import get_or_generate_context

    driver = get_neo4j_driver()
    with driver.session() as session:
        connections = session.execute_read(get_album_connections, album_discogs_id=discogs_id)

    if not connections:
        raise HTTPException(status_code=404, detail="Record not found")

    # Lazy context generation — generated on first view, cached forever
    context = get_or_generate_context(discogs_id)

    return {"discogs_id": discogs_id, "connections": connections, "context": context}


@router.post("/import/csv", response_model=ImportCSVResponse)
async def import_csv(
    file: UploadFile = File(...),
    uid: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
    quick: bool = True,
):
    """Import a Discogs collection from CSV export."""
    content = await file.read()
    csv_text = content.decode("utf-8")

    records = parse_csv(csv_text=csv_text)
    if not records:
        raise HTTPException(status_code=400, detail="No valid records found in CSV")

    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_text)
        tmp_path = tmp.name

    try:
        summary = import_collection_from_csv(
            file_path=tmp_path,
            user_id=uid,
            skip_research=quick,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Create a single feed event summarizing the import
    try:
        group_ids = await get_user_group_ids(db, uid)
        driver = get_neo4j_driver()
        with driver.session() as neo_session:
            user_rec = neo_session.run("MATCH (u:User {id: $uid}) RETURN u.name AS name", uid=uid).single()
        user_name = user_rec["name"] if user_rec else "Someone"

        await create_record_added_event(
            db=db,
            user_id=uid,
            user_name=user_name,
            album_title=f"{summary['imported']} records via CSV import",
            discogs_id=0,
            artists_added=0,
            connections=[],
            group_ids=group_ids if group_ids else None,
        )
    except Exception as feed_err:
        import logging
        logging.getLogger(__name__).error(f"Feed event for CSV import failed: {feed_err}", exc_info=True)

    return ImportCSVResponse(**summary)


@router.post("/add/async", response_model=TaskStatusResponse)
def add_record_async(req: AddRequest, uid: str = Depends(get_user_id)):
    """Smart Add as background task. Returns task ID for polling status."""
    task = smart_add_task.delay(
        discogs_id=req.discogs_id,
        musicbrainz_id=req.musicbrainz_id,
        user_id=uid,
    )
    return TaskStatusResponse(task_id=task.id, status="PENDING")


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """Check the status of an async Smart Add or import task."""
    from app.tasks.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.ready() else result.info,
    )
    return response
