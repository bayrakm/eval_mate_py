"""
ID generation and validation utilities for EvalMate.

Provides deterministic, URL-safe ID generation helpers and validation
functions for all model entities.
"""

import re
import time
import secrets
from typing import Optional


def new_id(prefix: str) -> str:
    """
    Generate a deterministic, URL-safe ID with the format:
    {prefix}_{timestamp_ms}_{short_random}
    
    Args:
        prefix: String prefix to identify the entity type
        
    Returns:
        URL-safe ID string
        
    Examples:
        >>> id1 = new_id("doc")
        >>> id1.startswith("doc_")
        True
        >>> len(id1.split("_"))
        3
    """
    timestamp_ms = int(time.time() * 1000)
    # Generate 6 characters of randomness (base62: a-z, A-Z, 0-9)
    short_random = secrets.token_urlsafe(4)[:6].replace("-", "0").replace("_", "1")
    return f"{prefix}_{timestamp_ms}_{short_random}"


def is_valid_id(value: str) -> bool:
    """
    Validate ID format using regex pattern.
    
    Expected format: {prefix}_{timestamp}_{random}
    - prefix: alphanumeric and underscores
    - timestamp: 13 digits (milliseconds since epoch)
    - random: 6 alphanumeric characters
    
    Args:
        value: ID string to validate
        
    Returns:
        True if ID format is valid, False otherwise
        
    Examples:
        >>> is_valid_id("doc_1698768000000_abc123")
        True
        >>> is_valid_id("invalid-id")
        False
        >>> is_valid_id("doc_123_ab")  # too short
        False
    """
    if not isinstance(value, str):
        return False
    
    # Pattern: prefix_timestamp_random
    # prefix: letters, numbers, underscores (1+ chars)
    # timestamp: exactly 13 digits
    # random: exactly 6 alphanumeric chars
    pattern = r"^[a-zA-Z0-9_]+_\d{13}_[a-zA-Z0-9]{6}$"
    return bool(re.match(pattern, value))


# Convenience wrappers for specific entity types

def new_doc_id() -> str:
    """Generate a new document ID."""
    return new_id("doc")


def new_block_id() -> str:
    """Generate a new document block ID."""
    return new_id("block")


def new_rubric_id() -> str:
    """Generate a new rubric ID."""
    return new_id("rubric")


def new_question_id() -> str:
    """Generate a new question ID."""
    return new_id("question")


def new_submission_id() -> str:
    """Generate a new submission ID."""
    return new_id("submission")


def new_eval_id() -> str:
    """Generate a new evaluation result ID."""
    return new_id("eval")


def new_rubric_item_id() -> str:
    """Generate a new rubric item ID."""
    return new_id("rubric_item")


def new_visual_id() -> str:
    """Generate a new visual block ID."""
    return new_id("visual")


def new_score_item_id() -> str:
    """Generate a new score item ID."""
    return new_id("score_item")


def parse_id_components(id_str: str) -> Optional[tuple[str, int, str]]:
    """
    Parse an ID into its components.
    
    Args:
        id_str: ID string to parse
        
    Returns:
        Tuple of (prefix, timestamp_ms, random_suffix) if valid, None otherwise
        
    Examples:
        >>> parse_id_components("doc_1698768000000_abc123")
        ('doc', 1698768000000, 'abc123')
        >>> parse_id_components("invalid") is None
        True
    """
    if not is_valid_id(id_str):
        return None
    
    parts = id_str.split("_")
    if len(parts) < 3:
        return None
    
    # Handle prefixes that might contain underscores
    # Find the last two parts (timestamp and random)
    random_suffix = parts[-1]
    timestamp_str = parts[-2]
    prefix = "_".join(parts[:-2])
    
    try:
        timestamp_ms = int(timestamp_str)
        return (prefix, timestamp_ms, random_suffix)
    except ValueError:
        return None


def get_id_prefix(id_str: str) -> Optional[str]:
    """
    Extract the prefix from an ID.
    
    Args:
        id_str: ID string
        
    Returns:
        Prefix string if valid ID, None otherwise
        
    Examples:
        >>> get_id_prefix("doc_1698768000000_abc123")
        'doc'
        >>> get_id_prefix("rubric_item_1698768000000_def456")
        'rubric_item'
    """
    components = parse_id_components(id_str)
    return components[0] if components else None


def is_id_type(id_str: str, expected_prefix: str) -> bool:
    """
    Check if an ID has the expected prefix.
    
    Args:
        id_str: ID string to check
        expected_prefix: Expected prefix
        
    Returns:
        True if ID has the expected prefix, False otherwise
        
    Examples:
        >>> is_id_type("doc_1698768000000_abc123", "doc")
        True
        >>> is_id_type("rubric_1698768000000_abc123", "doc")
        False
    """
    return get_id_prefix(id_str) == expected_prefix