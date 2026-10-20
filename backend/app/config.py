from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    app_env: str = "development"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr | None = None
    neo4j_database: str = "neo4j"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    enable_writes: bool = False          # secure by default; set true locally
    admin_token: SecretStr | None = None  # if set, writes require X-Admin-Token
    as_of_date: str = "2026-10-18"        # reference date for expiry rules
    max_graph_nodes: int = 300
    query_timeout_s: float = 15.0

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
