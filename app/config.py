"""
Configuration module for EvalMate.

Provides centralized configuration management and directory setup utilities.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Data directories
DIRECTORIES = {
    "rubrics": DATA_DIR / "rubrics",
    "questions": DATA_DIR / "questions", 
    "submissions": DATA_DIR / "submissions",
    "evals": DATA_DIR / "evals"
}

# Database configuration
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
    # Create base data directory
    DATA_DIR.mkdir(exist_ok=True)
    
    # Create all subdirectories
    for dir_name, dir_path in DIRECTORIES.items():
        dir_path.mkdir(exist_ok=True)
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
    ensure_directories_exist()
    print("📁 All directories created successfully!")