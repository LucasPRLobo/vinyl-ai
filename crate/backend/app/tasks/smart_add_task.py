"""Async Celery tasks for Smart Add and CSV import."""

import logging

from app.tasks.celery_app import celery_app
from app.services.smart_add import research_and_ingest
from app.services.discogs_csv import import_collection_from_csv

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="smart_add")
def smart_add_task(self, discogs_id: int, musicbrainz_id: str | None = None, user_id: str = "default-user"):
    """Run Smart Add pipeline as a background task."""
    self.update_state(state="RESEARCHING", meta={"discogs_id": discogs_id})

    try:
        result = research_and_ingest(
            discogs_id=discogs_id,
            musicbrainz_id=musicbrainz_id,
            user_id=user_id,
        )
        return {
            "status": "completed",
            "album_title": result.album_title,
            "discogs_id": result.discogs_id,
            "artists_added": result.artists_added,
            "connections_found": result.connections_found,
        }
    except Exception as e:
        logger.error(f"Smart Add task failed for {discogs_id}: {e}")
        raise


@celery_app.task(bind=True, name="csv_import")
def csv_import_task(self, file_path: str, user_id: str, skip_research: bool = True):
    """Run CSV import as a background task."""
    self.update_state(state="IMPORTING", meta={"file_path": file_path})

    try:
        summary = import_collection_from_csv(
            file_path=file_path,
            user_id=user_id,
            skip_research=skip_research,
        )
        return summary
    except Exception as e:
        logger.error(f"CSV import task failed: {e}")
        raise


@celery_app.task(bind=True, name="enrich_record")
def enrich_record_task(self, discogs_id: int, user_id: str = "default-user"):
    """Enrich an already-imported record with full AI research.
    Used to upgrade quick-imported CSV records."""
    from app.services import musicbrainz as mb

    self.update_state(state="ENRICHING", meta={"discogs_id": discogs_id})

    try:
        mb_results = mb.search_release("", "", limit=1)  # Will be refined
        # For enrichment, we re-run the full pipeline which merges into existing nodes
        result = research_and_ingest(
            discogs_id=discogs_id,
            musicbrainz_id=None,
            user_id=user_id,
        )
        return {
            "status": "enriched",
            "album_title": result.album_title,
            "artists_added": result.artists_added,
        }
    except Exception as e:
        logger.error(f"Enrich task failed for {discogs_id}: {e}")
        raise
