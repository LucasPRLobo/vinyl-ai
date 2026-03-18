"""MusicBrainz API client for detailed credits and artist relationships."""

from dataclasses import dataclass, field

import musicbrainzngs

from app.config import settings

musicbrainzngs.set_useragent(
    settings.musicbrainz_app_name,
    settings.musicbrainz_app_version,
    settings.musicbrainz_contact or None,
)


@dataclass
class MBCredit:
    artist_name: str
    artist_mbid: str
    instrument: str | None = None
    role: str = "performer"  # performer, producer, engineer, etc.
    tracks: list[str] = field(default_factory=list)


@dataclass
class MBRelease:
    mbid: str
    title: str
    artist: str
    date: str | None = None
    country: str | None = None
    label: str | None = None
    catalog_number: str | None = None
    credits: list[MBCredit] = field(default_factory=list)
    recording_mbids: list[str] = field(default_factory=list)


def search_release(artist: str, title: str, limit: int = 5) -> list[dict]:
    """Search MusicBrainz for a release. Returns basic matches."""
    try:
        result = musicbrainzngs.search_releases(
            artist=artist, release=title, limit=limit
        )
    except musicbrainzngs.WebServiceError:
        return []

    releases = []
    for r in result.get("release-list", []):
        artists = " / ".join(
            a.get("artist", {}).get("name", "")
            for a in r.get("artist-credit", [])
            if isinstance(a, dict) and "artist" in a
        )
        releases.append(
            {
                "mbid": r.get("id"),
                "title": r.get("title"),
                "artist": artists,
                "date": r.get("date"),
                "country": r.get("country"),
                "score": r.get("ext:score"),
            }
        )
    return releases


def get_release_details(mbid: str) -> MBRelease | None:
    """Fetch detailed release info including artist relationships."""
    try:
        result = musicbrainzngs.get_release_by_id(
            mbid,
            includes=[
                "artists",
                "recordings",
                "artist-credits",
                "labels",
                "recording-level-rels",
                "artist-rels",
            ],
        )
    except musicbrainzngs.WebServiceError:
        return None

    release = result.get("release", {})

    # Main artist
    artist_credit = release.get("artist-credit", [])
    main_artist = " / ".join(
        a.get("artist", {}).get("name", "")
        for a in artist_credit
        if isinstance(a, dict) and "artist" in a
    )

    # Label
    label_info = release.get("label-info-list", [])
    label = label_info[0].get("label", {}).get("name") if label_info else None
    catno = label_info[0].get("catalog-number") if label_info else None

    # Credits from artist relations
    credits = []
    for rel in release.get("artist-relation-list", []):
        role = rel.get("type", "performer")
        artist = rel.get("artist", {})
        attributes = rel.get("attribute-list", [])
        instrument = attributes[0] if attributes else None

        credits.append(
            MBCredit(
                artist_name=artist.get("name", ""),
                artist_mbid=artist.get("id", ""),
                instrument=instrument,
                role=_normalize_role(role),
            )
        )

    # Also get recording-level credits for per-track detail
    recording_mbids = []
    medium_list = release.get("medium-list", [])
    for medium in medium_list:
        for track in medium.get("track-list", []):
            recording = track.get("recording", {})
            rec_id = recording.get("id")
            if rec_id:
                recording_mbids.append(rec_id)

    return MBRelease(
        mbid=release.get("id", mbid),
        title=release.get("title", ""),
        artist=main_artist,
        date=release.get("date"),
        country=release.get("country"),
        label=label,
        catalog_number=catno,
        credits=credits,
        recording_mbids=recording_mbids,
    )


def get_recording_credits(recording_mbid: str) -> list[MBCredit]:
    """Fetch per-track artist credits for a specific recording."""
    try:
        result = musicbrainzngs.get_recording_by_id(
            recording_mbid, includes=["artist-rels"]
        )
    except musicbrainzngs.WebServiceError:
        return []

    recording = result.get("recording", {})
    credits = []
    for rel in recording.get("artist-relation-list", []):
        artist = rel.get("artist", {})
        attributes = rel.get("attribute-list", [])
        instrument = attributes[0] if attributes else None

        credits.append(
            MBCredit(
                artist_name=artist.get("name", ""),
                artist_mbid=artist.get("id", ""),
                instrument=instrument,
                role=_normalize_role(rel.get("type", "performer")),
            )
        )
    return credits


def get_artist_info(artist_mbid: str) -> dict | None:
    """Fetch artist details: bio, origin, life span."""
    try:
        result = musicbrainzngs.get_artist_by_id(
            artist_mbid, includes=["url-rels", "tags"]
        )
    except musicbrainzngs.WebServiceError:
        return None

    artist = result.get("artist", {})
    area = artist.get("area", {})
    begin_area = artist.get("begin-area", {})
    life_span = artist.get("life-span", {})

    return {
        "mbid": artist.get("id"),
        "name": artist.get("name"),
        "type": artist.get("type"),  # Person, Group, etc.
        "country": artist.get("country"),
        "area": area.get("name"),
        "origin_city": begin_area.get("name"),
        "begin_date": life_span.get("begin"),
        "end_date": life_span.get("end"),
        "tags": [t.get("name") for t in artist.get("tag-list", [])],
    }


def _normalize_role(mb_type: str) -> str:
    """Map MusicBrainz relationship types to our simplified roles."""
    role_map = {
        "instrument": "performer",
        "vocal": "performer",
        "performer": "performer",
        "producer": "producer",
        "engineer": "engineer",
        "mix": "engineer",
        "mastering": "engineer",
        "recording": "engineer",
        "composer": "writer",
        "lyricist": "writer",
        "writer": "writer",
        "arranger": "writer",
    }
    return role_map.get(mb_type.lower(), "performer")
