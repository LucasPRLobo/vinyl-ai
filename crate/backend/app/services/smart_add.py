"""Smart Add orchestrator: the core pipeline for adding a record to the knowledge graph.

Pipeline:
1. IDENTIFY — search Discogs + MusicBrainz for the release
2. DEEP RESEARCH — fetch full data from all sources
3. AI SYNTHESIS — Claude combines raw data into structured graph entities
4. INGEST — create nodes and edges in Neo4j
5. CONNECTIONS — find new connections in the user's graph
"""

import json
import logging
from dataclasses import dataclass, field

from app.services import discogs as discogs_api
from app.services import musicbrainz as mb
from app.services.research import synthesize_record_data
from app.graph.ingestion import ingest_record, get_new_connections
from app.graph.connection import get_neo4j_driver

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    discogs_id: int
    title: str
    artist: str
    year: int | None = None
    country: str | None = None
    cover_url: str | None = None
    musicbrainz_id: str | None = None


@dataclass
class SmartAddResult:
    album_title: str
    discogs_id: int
    artists_added: int
    connections_found: list[dict] = field(default_factory=list)
    synthesized_data: dict = field(default_factory=dict)


def search(artist: str, title: str) -> list[SearchResult]:
    """Step 1: Search for a release across sources. Returns candidates for user confirmation."""
    discogs_results = discogs_api.search_release(artist, title)

    # Also search MusicBrainz for cross-reference
    mb_results = mb.search_release(artist, title, limit=3)
    mb_by_title = {r["title"].lower(): r for r in mb_results}

    results = []
    for d in discogs_results:
        # Try to match Discogs result to MusicBrainz by title
        discogs_title = d["title"].split(" - ")[-1].strip().lower()
        mb_match = mb_by_title.get(discogs_title)
        results.append(
            SearchResult(
                discogs_id=d["discogs_id"],
                title=d["title"],
                artist=artist,
                year=d.get("year"),
                country=d.get("country"),
                cover_url=d.get("cover_url"),
                musicbrainz_id=mb_match["mbid"] if mb_match else None,
            )
        )

    return results


def research_and_ingest(
    discogs_id: int,
    musicbrainz_id: str | None = None,
    user_id: str | None = None,
) -> SmartAddResult:
    """Steps 2-5: Deep research → AI synthesis → graph ingestion → find connections."""

    # Step 2: Deep research
    logger.info(f"Smart Add: fetching Discogs release {discogs_id}")
    release = discogs_api.get_release(discogs_id)

    mb_data_str = "No MusicBrainz data available."
    if musicbrainz_id:
        logger.info(f"Smart Add: fetching MusicBrainz release {musicbrainz_id}")
        mb_release = mb.get_release_details(musicbrainz_id)
        if mb_release:
            # Fetch per-track credits for richer data
            track_credits = {}
            for i, rec_id in enumerate(mb_release.recording_mbids[:20]):
                credits = mb.get_recording_credits(rec_id)
                if credits:
                    track_credits[f"Track {i + 1}"] = [
                        {"artist": c.artist_name, "instrument": c.instrument, "role": c.role}
                        for c in credits
                    ]
            mb_data_str = json.dumps(
                {
                    "title": mb_release.title,
                    "artist": mb_release.artist,
                    "date": mb_release.date,
                    "label": mb_release.label,
                    "release_credits": [
                        {
                            "artist": c.artist_name,
                            "instrument": c.instrument,
                            "role": c.role,
                        }
                        for c in mb_release.credits
                    ],
                    "track_credits": track_credits,
                },
                indent=2,
            )

    # Format Discogs data for AI
    discogs_data_str = json.dumps(
        {
            "title": release.title,
            "artist": release.artist,
            "year": release.year,
            "country": release.country,
            "genres": release.genres,
            "styles": release.styles,
            "labels": release.labels,
            "tracklist": [
                {"position": t.position, "title": t.title, "duration": t.duration}
                for t in release.tracklist
            ],
            "credits": [
                {"name": c.name, "role": c.role, "tracks": c.tracks}
                for c in release.credits
            ],
            "notes": release.notes,
            "format": release.format_detail,
        },
        indent=2,
    )

    # Step 3: AI synthesis
    logger.info(f"Smart Add: synthesizing data for '{release.artist} - {release.title}'")
    synthesized = synthesize_record_data(
        artist=release.artist,
        title=release.title,
        discogs_data=discogs_data_str,
        musicbrainz_data=mb_data_str,
    )

    # Add cover URL from Discogs
    if release.cover_url:
        synthesized["album"]["cover_url"] = release.cover_url

    # Step 4: Graph ingestion
    logger.info("Smart Add: ingesting into graph")
    driver = get_neo4j_driver()
    ingest_record(
        driver,
        discogs_id=discogs_id,
        synthesized_data=synthesized,
        user_id=user_id,
    )

    # Step 5: Find new connections
    connections = []
    if user_id:
        connections = get_new_connections(driver, discogs_id=discogs_id, user_id=user_id)
        logger.info(f"Smart Add: found {len(connections)} new connections")

    return SmartAddResult(
        album_title=release.title,
        discogs_id=discogs_id,
        artists_added=len(synthesized.get("artists", [])),
        connections_found=connections,
        synthesized_data=synthesized,
    )
