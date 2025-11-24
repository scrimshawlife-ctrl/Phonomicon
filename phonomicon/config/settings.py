"""
Configuration settings for Phonomicon.

ABX-Core principle: Centralized configuration reduces ambiguity (entropy).
All settings come from environment variables with safe defaults.
No secrets are hard-coded.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Implements SEED principle: deterministic configuration with explicit provenance.
    """

    model_config = SettingsConfigDict(
        env_prefix="PHONOMICON_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application metadata
    app_name: str = "Phonomicon"
    version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"

    # Paths (ABX-Core: explicit path configuration reduces filesystem ambiguity)
    corpus_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "corpus"
    )

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # AAL-Core integration
    aal_core_url: str = "http://localhost:9000"
    aal_message_bus_url: str = "http://localhost:9000/bus"

    # ERS Scheduler settings
    scheduler_queue_size: int = 1000
    scheduler_worker_threads: int = 4
    scheduler_gpu_enabled: bool = False

    # Provenance settings (SEED: all artifacts must be traceable)
    provenance_hash_algorithm: str = "sha256"
    provenance_include_timestamps: bool = True

    # Analysis settings (deterministic behavior)
    audio_analysis_seed: int = 42
    visual_rendering_seed: int = 42

    # Debug and logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    debug_mode: bool = False

    def get_corpus_path(self, *parts: str) -> Path:
        """
        Get path within corpus directory.

        ABX-Core: Centralized path resolution reduces IO ambiguity.
        """
        path = self.corpus_root.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    ABX-Core: Singleton pattern reduces redundant config parsing (compute cost).
    """
    return Settings()
