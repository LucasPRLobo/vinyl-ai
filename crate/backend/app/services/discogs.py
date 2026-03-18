"""Discogs API client using the official python3-discogs-client library."""

from dataclasses import dataclass, field

import discogs_client

from app.config import settings

_client: discogs_client.Client | None = None


def _get_client() -> discogs_client.Client:
    global _client
    if _client is None:
        if settings.discogs_user_token:
            _client = discogs_client.Client(
                "CrateVinylGraph/0.1.0 +https://github.com/crate-vinyl",
                user_token=settings.discogs_user_token,
            )
        else:
            # Public access with just User-Agent (lower rate limits, no collection access)
            _client = discogs_client.Client("CrateVinylGraph/0.1.0 +https://github.com/crate-vinyl")
    return _client


def _format_str(formats) -> str:
    """Safely convert Discogs formats (list of dicts or strings) to a display string."""
    if not formats:
        return ""
    parts = []
    for f in formats:
        if isinstance(f, dict):
            name = f.get("name", "")
            descs = f.get("descriptions", [])
            parts.append(f"{name} {', '.join(descs)}".strip() if descs else name)
        elif isinstance(f, str):
            parts.append(f)
    return ", ".join(parts)


@dataclass
class DiscogsCredit:
    name: str
    role: str
    tracks: str | None = None


@dataclass
class DiscogsTrack:
    position: str
    title: str
    duration: str | None = None


@dataclass
class DiscogsRelease:
    discogs_id: int
    title: str
    artist: str
    year: int | None = None
    country: str | None = None
    genres: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    labels: list[dict] = field(default_factory=list)
    tracklist: list[DiscogsTrack] = field(default_factory=list)
    credits: list[DiscogsCredit] = field(default_factory=list)
    notes: str | None = None
    cover_url: str | None = None
    format_detail: str | None = None
    master_id: int | None = None


def search_release(artist: str, title: str, limit: int = 5) -> list[dict]:
    """Search for a release by artist and title."""
    client = _get_client()
    results = client.search(artist=artist, release_title=title, type="release")

    output = []
    for i, r in enumerate(results):
        if i >= limit:
            break
        output.append(
            {
                "discogs_id": r.id,
                "title": r.title,
                "year": getattr(r, "year", None),
                "country": getattr(r, "country", None),
                "cover_url": getattr(r, "thumb", None),
                "format": _format_str(getattr(r, "formats", None)),
            }
        )
    return output


def get_release(release_id: int) -> DiscogsRelease:
    """Fetch full release details including credits and tracklist."""
    client = _get_client()
    release = client.release(release_id)

    # Parse credits (extraartists)
    credits = []
    for extra in getattr(release, "extraartists", []) or []:
        credits.append(
            DiscogsCredit(
                name=extra.name,
                role=getattr(extra, "role", ""),
                tracks=getattr(extra, "tracks", ""),
            )
        )

    # Main artists
    for artist_entry in release.artists:
        credits.append(
            DiscogsCredit(name=artist_entry.name, role="Main Artist")
        )

    # Parse tracklist
    tracklist = []
    for t in release.tracklist:
        if getattr(t, "type_", "track") == "track":
            tracklist.append(
                DiscogsTrack(
                    position=t.position,
                    title=t.title,
                    duration=getattr(t, "duration", None),
                )
            )

    # Parse labels
    labels = []
    for label in release.labels:
        labels.append(
            {
                "name": label.name,
                "catno": getattr(label, "catno", ""),
                "id": label.id,
            }
        )

    # Format
    format_detail = None
    formats = getattr(release, "formats", []) or []
    if formats:
        fmt = formats[0]
        descriptions = fmt.get("descriptions", [])
        format_detail = f"{fmt.get('name', '')} {', '.join(descriptions)}".strip()

    # Cover
    images = getattr(release, "images", []) or []
    cover_url = images[0]["uri"] if images else None

    # Main artist string
    main_artist = " / ".join(a.name for a in release.artists)

    return DiscogsRelease(
        discogs_id=release.id,
        title=release.title,
        artist=main_artist,
        year=getattr(release, "year", None),
        country=getattr(release, "country", None),
        genres=getattr(release, "genres", []) or [],
        styles=getattr(release, "styles", []) or [],
        labels=labels,
        tracklist=tracklist,
        credits=credits,
        notes=getattr(release, "notes", None),
        cover_url=cover_url,
        format_detail=format_detail,
        master_id=getattr(release, "master_id", None),
    )


def get_user_collection(username: str) -> list[dict]:
    """Fetch a user's Discogs collection (requires user token with appropriate permissions)."""
    client = _get_client()
    user = client.user(username)
    collection = user.collection_folders[0]  # "All" folder

    records = []
    for item in collection.releases:
        release = item.release
        records.append(
            {
                "discogs_id": release.id,
                "title": release.title,
                "year": getattr(release, "year", None),
            }
        )
    return records
