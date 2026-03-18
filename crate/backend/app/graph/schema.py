"""Neo4j schema setup: constraints, indexes, and full-text search indexes."""

CONSTRAINTS = [
    "CREATE CONSTRAINT album_discogs_id IF NOT EXISTS FOR (a:Album) REQUIRE a.discogs_id IS UNIQUE",
    "CREATE CONSTRAINT album_musicbrainz_id IF NOT EXISTS FOR (a:Album) REQUIRE a.musicbrainz_id IS UNIQUE",
    "CREATE CONSTRAINT artist_musicbrainz_id IF NOT EXISTS FOR (a:Artist) REQUIRE a.musicbrainz_id IS UNIQUE",
    "CREATE CONSTRAINT label_discogs_id IF NOT EXISTS FOR (l:Label) REQUIRE l.discogs_id IS UNIQUE",
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT group_id IF NOT EXISTS FOR (g:Group) REQUIRE g.id IS UNIQUE",
    "CREATE CONSTRAINT pressing_discogs_id IF NOT EXISTS FOR (p:Pressing) REQUIRE p.discogs_id IS UNIQUE",
    "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
    "CREATE CONSTRAINT instrument_name IF NOT EXISTS FOR (i:Instrument) REQUIRE i.name IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX album_title IF NOT EXISTS FOR (a:Album) ON (a.title)",
    "CREATE INDEX album_year IF NOT EXISTS FOR (a:Album) ON (a.year)",
    "CREATE INDEX artist_name IF NOT EXISTS FOR (a:Artist) ON (a.name)",
    "CREATE INDEX label_name IF NOT EXISTS FOR (l:Label) ON (l.name)",
    "CREATE INDEX studio_name IF NOT EXISTS FOR (s:Studio) ON (s.name)",
    "CREATE INDEX scene_name IF NOT EXISTS FOR (s:Scene) ON (s.name)",
    "CREATE INDEX city_name IF NOT EXISTS FOR (c:City) ON (c.name)",
    "CREATE INDEX store_name IF NOT EXISTS FOR (s:Store) ON (s.name)",
]

FULLTEXT_INDEXES = [
    (
        "album_fulltext",
        "CREATE FULLTEXT INDEX album_fulltext IF NOT EXISTS FOR (a:Album) ON EACH [a.title]",
    ),
    (
        "artist_fulltext",
        "CREATE FULLTEXT INDEX artist_fulltext IF NOT EXISTS FOR (a:Artist) ON EACH [a.name]",
    ),
]


async def ensure_schema(driver):
    """Create all constraints and indexes. Safe to run multiple times."""
    with driver.session() as session:
        for constraint in CONSTRAINTS:
            session.run(constraint)
        for index in INDEXES:
            session.run(index)
        for _name, index in FULLTEXT_INDEXES:
            session.run(index)
