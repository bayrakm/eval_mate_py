"""
Configuration module for EvalMate.

Provides centralized configuration management and directory setup utilities.
"""

import errno
import os
from pathlib import Path
from typing import Dict, Any

# Base configuration
BASE_DIR = Path(__file__).parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
FUNCTIONS_TEMP_DIR = Path("/tmp/evalmate-data")


def _initial_data_dir() -> Path:
    """
    Determine the initial data directory, allowing overrides via DATA_DIR.
    Falls back to /tmp when running in Azure Functions (read-only filesystem).
    """
    configured = os.getenv("DATA_DIR")
    if configured:
        return Path(configured)
    # WEBSITE_INSTANCE_ID is set in Azure Functions
    if os.getenv("WEBSITE_INSTANCE_ID"):
        return FUNCTIONS_TEMP_DIR
    return DEFAULT_DATA_DIR


def _build_directories(base: Path) -> Dict[str, Path]:
    return {
        "rubrics": base / "rubrics",
        "questions": base / "questions",
        "submissions": base / "submissions",
        "evals": base / "evals",
    }


DATA_DIR = _initial_data_dir()
DIRECTORIES: Dict[str, Path] = _build_directories(DATA_DIR)
DATABASE_PATH = DATA_DIR / "db.sqlite3"


def _reset_data_dir(new_base: Path) -> None:
    """
    Update global path references to a new data directory.
    """
    global DATA_DIR, DIRECTORIES, DATABASE_PATH
    DATA_DIR = new_base
    DIRECTORIES = _build_directories(DATA_DIR)
    DATABASE_PATH = DATA_DIR / "db.sqlite3"

# Storage mode: "json" or "sqlite"
STORAGE_MODE = os.getenv("EVALMATE_STORAGE_MODE", "sqlite")


def get_storage_mode() -> str:
    """
    Return the current storage backend mode.
    
    Returns:
        str: The storage mode - either 'json' or 'sqlite'
    """
    return STORAGE_MODE.lower()


def ensure_directories_exist() -> None:
    """
    Create all required data directories if they don't exist.
    
    This function ensures that the base data directory and all subdirectories
    for rubrics, questions, submissions, and evaluations are created.
    """
    try:
        DATA_DIR.mkdir(exist_ok=True, parents=True)
    except OSError as exc:
        if exc.errno == errno.EROFS and DATA_DIR != FUNCTIONS_TEMP_DIR:
            _reset_data_dir(FUNCTIONS_TEMP_DIR)
            DATA_DIR.mkdir(exist_ok=True, parents=True)
        elif exc.errno != errno.EEXIST:
            raise
    
    # Create all subdirectories
    for dir_name, dir_path in DIRECTORIES.items():
        dir_path.mkdir(exist_ok=True, parents=True)
        print(f"✅ Directory '{dir_name}' ready at: {dir_path}")


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration as a dictionary.
    
    Returns:
        Dict containing all configuration values including paths and settings.
    """
    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "database_path": str(DATABASE_PATH),
        "storage_mode": STORAGE_MODE,
        "directories": {k: str(v) for k, v in DIRECTORIES.items()}
    }


if __name__ == "__main__":
    # For testing - create directories when run directly

    print(f"Using data dir: {DATA_DIR}")

    ensure_directories_exist()
    print("📁 All directories created successfully!")
