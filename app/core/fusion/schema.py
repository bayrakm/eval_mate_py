"""
Schema definitions for fusion context data structures.

This module defines the FusionContext and related models that represent
the unified evaluation context for LLM-based assessment.
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class FusionVisual(BaseModel):
    """Visual element with caption and metadata for fusion context."""
    
    id: str
    type: str  # figure, table, image, etc.
    caption: str
    ocr_text: Optional[str] = None
    rubric_links: Optional[List[str]] = Field(
        default=None, 
        description="Optional cross-links to relevant rubric items"
    )


class FusionContext(BaseModel):
    """
    Unified context containing all data needed for LLM evaluation.
    
    This model represents the fusion of rubric, question, and submission
    data into a single structured object ready for evaluation.
    """
    
    id: str
    rubric_id: str
    question_id: str
    submission_id: str
    rubric_items: List[Dict[str, Any]]  # title, desc, weight, criterion
    question_text: str
    submission_text: str
    submission_visuals: List[FusionVisual]
    created_at: datetime
    token_estimate: int
    visual_count: int
    text_block_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def save_json(self, path: str) -> None:
        """
        Save fusion context to JSON file.
        
        Args:
            path: File path to save the JSON
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Convert to dict and handle datetime serialization
        data = self.model_dump()
        data['created_at'] = self.created_at.isoformat()
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_json(cls, path: str) -> "FusionContext":
        """
        Load fusion context from JSON file.
        
        Args:
            path: File path to load from
            
        Returns:
            FusionContext instance
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Handle datetime parsing
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)

    def get_text_content(self) -> str:
        """Get all text content as a single string for token estimation."""
        content_parts = [
            self.question_text,
            self.submission_text,
        ]
        
        # Add visual captions
        for visual in self.submission_visuals:
            content_parts.append(visual.caption)
            if visual.ocr_text:
                content_parts.append(visual.ocr_text)
        
        # Add rubric content
        for item in self.rubric_items:
            if 'title' in item:
                content_parts.append(item['title'])
            if 'desc' in item:
                content_parts.append(item['desc'])
        
        return "\n".join(filter(None, content_parts))

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the fusion context for inspection."""
        return {
            "id": self.id,
            "rubric_id": self.rubric_id,
            "question_id": self.question_id,
            "submission_id": self.submission_id,
            "created_at": self.created_at.isoformat(),
            "token_estimate": self.token_estimate,
            "visual_count": self.visual_count,
            "text_block_count": self.text_block_count,
            "rubric_items_count": len(self.rubric_items),
            "question_length": len(self.question_text),
            "submission_length": len(self.submission_text),
            "metadata": self.metadata,
        }