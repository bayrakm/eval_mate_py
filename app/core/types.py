"""
Core Type Definitions for EvalMate

This module provides shared type definitions used across the codebase,
particularly for Phase 6 and Phase 7 visual processing.
"""

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass


@dataclass
class DocBlock:
    """
    Represents a text content block from documents.
    
    Used for compatibility with existing document processing code.
    """
    
    block_id: str
    content: str
    page_number: int = 1
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VisualBlock:
    """
    Represents a visual content block extracted from documents.
    
    Used by the visual extraction (Phase 6) and captioning (Phase 7) systems.
    This is a simplified working type, distinct from the Pydantic schema models.
    """
    
    block_id: str
    source_path: Optional[str] = None
    caption_text: Optional[str] = None
    page_number: int = 1
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Position:
    """
    Represents position information for content blocks.
    """
    
    page: int = 0
    bbox_norm: Optional[tuple] = None
    
    def get(self, key: str, default=None):
        """Dictionary-like access for backward compatibility."""
        if key == "page":
            return self.page
        elif key == "bbox_norm":
            return self.bbox_norm
        return default


@dataclass
class VisualExtractionResult:
    """
    Result from visual extraction process (Phase 6).
    
    Used for compatibility with existing visual extraction code.
    """
    
    visual_type: str
    asset_path: Optional[str] = None
    caption: Optional[str] = None
    position: Optional[Position] = None
    content: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.position is None:
            self.position = Position()
        if self.content is None:
            self.content = {}


# Legacy type aliases for backward compatibility
class MockDocBlock:
    """Mock DocBlock for testing when schema models aren't available."""
    
    def __init__(self, content: str = "", block_id: str = "", page_number: int = 1, metadata: Optional[Dict] = None):
        self.content = content
        self.block_id = block_id
        self.page_number = page_number
        self.metadata = metadata or {}


class MockVisualBlock:
    """Mock VisualBlock for testing when schema models aren't available."""
    
    def __init__(self, caption_text: str = "", source_path: str = "", block_id: str = "", page_number: int = 1, metadata: Optional[Dict] = None):
        self.caption_text = caption_text
        self.source_path = source_path
        self.block_id = block_id
        self.page_number = page_number
        self.metadata = metadata or {}


# Export commonly used types
__all__ = [
    "DocBlock",
    "VisualBlock",
    "Position", 
    "VisualExtractionResult",
    "MockDocBlock",
    "MockVisualBlock"
]