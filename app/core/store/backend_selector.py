"""
Backend selector module for EvalMate persistence layer.

This module provides a unified interface to select between JSON and SQLite
storage backends based on the current configuration.
"""

import logging
from typing import Any

from app.config import get_storage_mode

logger = logging.getLogger(__name__)


def get_backend() -> Any:
    """
    Return the active backend module (json_store or sqlite_store).
    
    Uses the storage mode from configuration to determine which backend
    to load and return. This allows the repository layer to work
    transparently with either storage system.
    
    Returns:
        The backend module (either json_store or sqlite_store)
        
    Raises:
        ImportError: If the backend module cannot be imported
        ValueError: If the storage mode is invalid
        
    Examples:
        >>> backend = get_backend()
        >>> backend.save_record("rubrics", "test_id", {"data": "test"})
    """
    mode = get_storage_mode()
    logger.debug(f"Selecting backend for storage mode: {mode}")
    
    try:
        if mode == "sqlite":
            from app.core.store import sqlite_store
            logger.debug("Selected SQLite backend")
            return sqlite_store
        elif mode == "json":
            from app.core.store import json_store
            logger.debug("Selected JSON backend")
            return json_store
        else:
            raise ValueError(f"Invalid storage mode: {mode}. Must be 'json' or 'sqlite'.")
            
    except ImportError as e:
        logger.error(f"Failed to import backend for mode '{mode}': {e}")
        raise ImportError(f"Backend '{mode}' is not available: {e}")


def get_backend_name() -> str:
    """
    Get the name of the currently active backend.
    
    Returns:
        str: The name of the backend ('json' or 'sqlite')
    """
    return get_storage_mode()


def is_sqlite_backend() -> bool:
    """
    Check if the current backend is SQLite.
    
    Returns:
        bool: True if using SQLite backend, False otherwise
    """
    return get_storage_mode() == "sqlite"


def is_json_backend() -> bool:
    """
    Check if the current backend is JSON.
    
    Returns:
        bool: True if using JSON backend, False otherwise
    """
    return get_storage_mode() == "json"