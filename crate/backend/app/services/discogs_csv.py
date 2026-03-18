"""Import a Discogs collection from CSV export.

Discogs lets you export your collection as CSV from:
Settings > Collection > Export (bottom of page)

CSV columns:
Catalog#, Artist, Title, Label, Format, Rating, Released, release_id,
CollectionFolder, Date Added, Collection Media Condition,
Collection Sleeve Condition, Collection Notes
"""

import csv
import logging
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DiscogsCSVRecord:
    catalog_number: str
    artist: str
    title: str
    label: str
    format: str
    rating: int | None
    released: str | None
    release_id: int
    folder: str
    date_added: str | None
    media_condition: str | None
    sleeve_condition: str | None
    notes: str | None


def parse_csv(file_path: str | Path | None = None, csv_text: str | None = None) -> list[DiscogsCSVRecord]:
    """Parse a Discogs collection CSV export.

    Args:
        file_path: Path to CSV file
        csv_text: Raw CSV string (alternative to file_path)

    Returns:
        List of parsed records with Discogs release IDs
    """
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    elif csv_text:
        content = csv_text
    else:
        raise ValueError("Provide either file_path or csv_text")

    reader = csv.DictReader(StringIO(content))
    records = []

    for row in reader:
        try:
            release_id = int(row.get("release_id", 0))
            if release_id == 0:
                logger.warning(f"Skipping row with no release_id: {row.get('Title', '?')}")
                continue

            rating_str = row.get("Rating", "")
            rating = int(rating_str) if rating_str and rating_str.isdigit() else None

            records.append(
                DiscogsCSVRecord(
                    catalog_number=row.get("Catalog#", ""),
                    artist=row.get("Artist", ""),
                    title=row.get("Title", ""),
                    label=row.get("Label", ""),
                    format=row.get("Format", ""),
                    rating=rating,
                    released=row.get("Released", None),
                    release_id=release_id,
                    folder=row.get("CollectionFolder", ""),
                    date_added=row.get("Date Added", None),
                    media_condition=row.get("Collection Media Condition", None),
                    sleeve_condition=row.get("Collection Sleeve Condition", None),
                    notes=row.get("Collection Notes", None),
                )
            )
        except Exception as e:
            logger.warning(f"Skipping malformed row: {e}")
            continue

    logger.info(f"Parsed {len(records)} records from Discogs CSV")
    return records


def import_collection_from_csv(
    file_path: str | Path,
    user_id: str,
    skip_research: bool = False,
) -> dict:
    """Import a full Discogs collection from CSV export.

    Args:
        file_path: Path to the Discogs CSV export
        user_id: User ID to assign ownership
        skip_research: If True, only create basic nodes from CSV data
                       (fast import, enrich later). If False, run full
                       Smart Add pipeline for each record (slow but thorough).

    Returns:
        Summary dict with counts
    """
    from app.services.smart_add import research_and_ingest
    from app.services import musicbrainz as mb
    from app.graph.connection import get_neo4j_driver
    from app.graph.ingestion import ingest_record

    records = parse_csv(file_path=file_path)

    imported = 0
    skipped = 0
    errors = 0

    if skip_research:
        # Fast import: create basic graph nodes from CSV data only, no API calls
        driver = get_neo4j_driver()
        for i, record in enumerate(records):
            try:
                logger.info(
                    f"[{i + 1}/{len(records)}] Quick import: "
                    f"{record.artist} - {record.title}"
                )
                basic_data = {
                    "album": {
                        "title": record.title,
                        "year": int(record.released) if record.released and record.released.isdigit() else None,
                        "country": None,
                        "notes": "",
                    },
                    "artists": [
                        {"name": record.artist, "role": "performer", "instrument": None}
                    ],
                    "labels": [{"name": record.label}] if record.label else [],
                    "genres": [],
                    "studios": [],
                    "scenes": [],
                    "pressing": {
                        "country": None,
                        "year": int(record.released) if record.released and record.released.isdigit() else None,
                        "format_detail": record.format,
                    },
                    "context": {},
                }
                ingest_record(
                    driver,
                    discogs_id=record.release_id,
                    synthesized_data=basic_data,
                    user_id=user_id,
                )
                imported += 1
            except Exception as e:
                logger.error(f"Error importing {record.title}: {e}")
                errors += 1
    else:
        # Full import: run Smart Add pipeline for each record
        for i, record in enumerate(records):
            try:
                logger.info(
                    f"[{i + 1}/{len(records)}] Smart Add: "
                    f"{record.artist} - {record.title}"
                )
                # Try to find MusicBrainz match
                mb_results = mb.search_release(record.artist, record.title, limit=1)
                mb_id = mb_results[0]["mbid"] if mb_results else None

                research_and_ingest(
                    discogs_id=record.release_id,
                    musicbrainz_id=mb_id,
                    user_id=user_id,
                )
                imported += 1
            except Exception as e:
                logger.error(f"Error importing {record.title}: {e}")
                errors += 1

    summary = {
        "total_in_csv": len(records),
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "mode": "quick" if skip_research else "full",
    }
    logger.info(f"Import complete: {summary}")
    return summary
