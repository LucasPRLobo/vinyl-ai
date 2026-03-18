from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    database_url: str = "postgresql+asyncpg://crate:crate_dev@localhost:5433/crate"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "crate_dev_neo4j"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Discogs
    discogs_user_token: str = ""

    # MusicBrainz
    musicbrainz_app_name: str = "Crate"
    musicbrainz_app_version: str = "0.1.0"
    musicbrainz_contact: str = ""

    # Spotify
    spotify_client_id: str = ""
    spotify_client_secret: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Tavily (web search)
    tavily_api_key: str = ""

    # Mapbox
    mapbox_access_token: str = ""

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    model_config = {"env_file": [".env", "../.env"], "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
