"""Environment and path configuration for the volatility project.

Real secrets belong in a local ``.env`` file, which is ignored by Git. The
committed ``.env.example`` documents supported settings without credentials.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


def load_project_env(env_file: Path = ENV_FILE) -> bool:
    """Load local environment values without overriding shell variables."""

    return load_dotenv(dotenv_path=env_file, override=False)


def get_config(name: str, default: str | None = None) -> str | None:
    """Return an environment setting after loading the project ``.env``."""

    load_project_env()
    return os.getenv(name, default)


def get_project_path(name: str, default: str) -> Path:
    """Resolve a configured project path and create it when it is missing."""

    configured = get_config(name, default) or default
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = get_project_path("DATA_DIR", "data")
RAW_DATA_DIR = get_project_path("RAW_DATA_DIR", "data/raw")
PROCESSED_DATA_DIR = get_project_path("PROCESSED_DATA_DIR", "data/processed")
REPORTS_DIR = get_project_path("REPORTS_DIR", "reports")
MODEL_DIR = get_project_path("MODEL_DIR", "model")
DOCS_DIR = get_project_path("DOCS_DIR", "docs")

DEFAULT_START_DATE = get_config("START_DATE", "2018-01-01") or "2018-01-01"
DEFAULT_END_DATE = get_config("END_DATE", "") or ""


def masked_config_status() -> dict[str, str]:
    """Return non-sensitive configuration diagnostics for setup checks."""

    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "raw_data_dir": str(RAW_DATA_DIR),
        "processed_data_dir": str(PROCESSED_DATA_DIR),
        "reports_dir": str(REPORTS_DIR),
        "model_dir": str(MODEL_DIR),
        "docs_dir": str(DOCS_DIR),
        "env_file_present": str(ENV_FILE.exists()),
    }
