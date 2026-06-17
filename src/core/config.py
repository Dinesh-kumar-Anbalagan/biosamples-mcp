from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    biosamples_base_url: str = os.getenv(
        "BIOSAMPLES_BASE_URL",
        "https://www.ebi.ac.uk/biosamples",
    )
    biosamples_timeout_seconds: float = float(
        os.getenv("BIOSAMPLES_TIMEOUT_SECONDS", "30")
    )
    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )
    cache_ttl_seconds: int = int(
        os.getenv("CACHE_TTL_SECONDS", "300")
    )


settings = Settings()