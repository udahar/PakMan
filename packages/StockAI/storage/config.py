"""StockAI Configuration Module.

Load settings from .env file or environment variables.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    from dotenv import load_dotenv

    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


# Find .env file - look in project root and parent dirs
def _find_env_file() -> Optional[Path]:
    """Find .env file in project hierarchy."""
    current = Path(__file__).parent.parent

    for _ in range(5):  # Check up to 5 levels up
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        current = current.parent

    return None


# Load .env if exists
if HAS_DOTENV:
    env_path = _find_env_file()
    if env_path:
        load_dotenv(env_path)


@dataclass
class Config:
    """StockAI configuration."""

    # Database
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "zolapress"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    # Qdrant
    qdrant_host: str = field(
        default_factory=lambda: os.getenv("QDRANT_HOST", "localhost")
    )
    qdrant_port: int = field(
        default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333"))
    )

    # Data
    data_dir: str = field(default_factory=lambda: os.getenv("DATA_DIR", "data"))

    # Analysis
    default_period: str = field(
        default_factory=lambda: os.getenv("DEFAULT_PERIOD", "10y")
    )

    @property
    def db_url(self) -> str:
        """Get PostgreSQL connection URL."""
        if self.db_password:
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return (
            f"postgresql://{self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


# Global config instance
config = Config()


def get_config() -> Config:
    """Get global config instance."""
    return config


def reload_config() -> Config:
    """Reload config from environment."""
    global config
    config = Config()
    return config
