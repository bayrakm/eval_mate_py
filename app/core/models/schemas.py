"""
Comprehensive Pydantic data schemas for EvalMate.

Contains all core domain models with strict validation, serialization,
and JSON round-trip utilities for the intelligent assignment feedback system.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from enum import Enum

from .ids import (
    new_doc_id, new_block_id, new_rubric_id, new_question_id, 
    new_submission_id, new_eval_id, new_rubric_item_id, new_visual_id,
    is_valid_id
)


# ============================================================================
# Enumerations and Literals
# ============================================================================

class VisualType(str, Enum):
    """Types of visual content that can be extracted from documents."""
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    CHART = "chart"
    DIAGRAM = "diagram"
    MAP = "map"
    SCREENSHOT = "screenshot"


class RubricCriterion(str, Enum):
    """Standard rubric criteria for evaluation."""
    CONTENT = "content"
    ACCURACY = "accuracy"
    STRUCTURE = "structure"
    VISUALS = "visuals"
    CITATIONS = "citations"
    ORIGINALITY = "originality"


BlockKind = Literal["text", "visual"]


# ============================================================================
# Core Block Models
# ============================================================================

class VisualBlock(BaseModel):
    """
    Represents a visual element extracted from a document.
    
    Contains metadata about images, charts, tables, and other visual content
    including OCR text, structured data, and detected labels.
    """
    model_config = ConfigDict(strict=True, frozen=False, extra="forbid")
    
    id: str = Field(default_factory=new_visual_id, description="Unique visual block identifier")
    type: VisualType = Field(description="Type of visual content")
    source_path: str = Field(description="Relative path to extracted visual asset")
    caption_text: Optional[str] = Field(default=None, description="Caption or title text")
    ocr_text: Optional[str] = Field(default=None, description="Text extracted via OCR")
    structured_table: Optional[List[List[str]]] = Field(
        default=None, 
        description="Structured table data as rows of cells"
    )
    detected_labels: Optional[List[str]] = Field(
        default=None,
        description="Machine-detected labels or tags"
    )
    
    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Source path cannot be empty")
        return v.strip()


class DocBlock(BaseModel):
    """
    Represents a single block of content within a canonical document.
    
    Can contain either text content or a visual element, with optional
    positioning and page information.
    """
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    
    id: str = Field(default_factory=new_block_id, description="Unique block identifier")
    kind: BlockKind = Field(description="Type of block content")
    text: Optional[str] = Field(default=None, description="Text content (required for text blocks)")
    visual: Optional[VisualBlock] = Field(default=None, description="Visual content (required for visual blocks)")
    page: Optional[int] = Field(default=None, ge=1, description="1-based page number")
    bbox: Optional[List[float]] = Field(
        default=None,
        description="Normalized bounding box [x1, y1, x2, y2]"
    )
    
    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 4:
                raise ValueError("Bounding box must have exactly 4 coordinates")
            if not all(0.0 <= coord <= 1.0 for coord in v):
                raise ValueError("Bounding box coordinates must be normalized (0.0-1.0)")
            if v[0] >= v[2] or v[1] >= v[3]:
                raise ValueError("Invalid bounding box: x1 < x2 and y1 < y3 required")
        return v
    
    @model_validator(mode="after")
    def validate_content_requirements(self) -> "DocBlock":
        """Ensure content matches the block kind."""
        if self.kind == "text":
            if not self.text or not self.text.strip():
                raise ValueError("Text blocks must have non-empty text content")
            if self.visual is not None:
                raise ValueError("Text blocks cannot have visual content")
        elif self.kind == "visual":
            if self.visual is None:
                raise ValueError("Visual blocks must have visual content")
            if self.text is not None:
                raise ValueError("Visual blocks cannot have text content")
        return self


# ============================================================================
# Document Models
# ============================================================================

class CanonicalDoc(BaseModel):
    """
    Represents a processed document in canonical format.
    
    Contains structured blocks of text and visual content extracted from
    original source files with metadata and timestamps.
    """
    model_config = ConfigDict(strict=True, extra="forbid")
    
    id: str = Field(default_factory=new_doc_id, description="Unique document identifier")
    title: Optional[str] = Field(default=None, description="Document title")
    source_files: List[str] = Field(description="Paths to original uploaded files")
    blocks: List[DocBlock] = Field(description="Ordered content blocks")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional processing metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one source file must be specified")
        cleaned = [f.strip() for f in v if f.strip()]
        if not cleaned:
            raise ValueError("Source files cannot be empty")
        return cleaned
    
    @field_validator("blocks")
    @classmethod
    def validate_blocks_unique_ids(cls, v: List[DocBlock]) -> List[DocBlock]:
        """Ensure all block IDs are unique within the document."""
        if not v:
            return v
        
        block_ids = [block.id for block in v]
        if len(set(block_ids)) != len(block_ids):
            raise ValueError("All block IDs must be unique within a document")
        return v


# ============================================================================
# Rubric Models
# ============================================================================

class RubricItem(BaseModel):
    """
    Represents a single criterion within a rubric.
    
    Contains evaluation criteria with weights, descriptions, and
    standardized criterion types.
    """
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    
    id: str = Field(default_factory=new_rubric_item_id, description="Unique rubric item identifier")
    title: str = Field(description="Short title for the criterion")
    description: str = Field(description="Detailed description of the criterion")
    weight: float = Field(ge=0.0, le=1.0, description="Weight of this criterion (0.0-1.0)")
    criterion: RubricCriterion = Field(description="Type of evaluation criterion")
    
    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("title", "description")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title and description cannot be empty")
        return v.strip()


class Rubric(BaseModel):
    """
    Represents a complete grading rubric for an assignment.
    
    Contains multiple evaluation criteria with weights and references
    to the source canonical document.
    """
    model_config = ConfigDict(strict=True, extra="forbid")
    
    id: str = Field(default_factory=new_rubric_id, description="Unique rubric identifier")
    course: str = Field(description="Course identifier")
    assignment: str = Field(description="Assignment identifier")
    version: str = Field(description="Rubric version")
    items: List[RubricItem] = Field(description="List of rubric criteria")
    canonical: CanonicalDoc = Field(description="Source document for this rubric")
    
    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("course", "assignment", "version")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Course, assignment, and version cannot be empty")
        return v.strip()
    
    @field_validator("items")
    @classmethod
    def validate_items_exist(cls, v: List[RubricItem]) -> List[RubricItem]:
        if not v:
            raise ValueError("Rubric must have at least one item")
        return v


# ============================================================================
# Question and Submission Models
# ============================================================================

class Question(BaseModel):
    """
    Represents an assignment question.
    
    Links to a specific rubric and contains the canonical document
    representing the question content.
    """
    model_config = ConfigDict(strict=True, extra="forbid")
    
    id: str = Field(default_factory=new_question_id, description="Unique question identifier")
    title: str = Field(description="Question title")
    canonical: CanonicalDoc = Field(description="Question content as canonical document")
    rubric_id: str = Field(description="Associated rubric identifier")
    
    @field_validator("id", "rubric_id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question title cannot be empty")
        return v.strip()


class Submission(BaseModel):
    """
    Represents a student's submission for an assignment.
    
    Contains the student identifier, canonical document content,
    and references to the associated question and rubric.
    """
    model_config = ConfigDict(strict=True, extra="forbid")
    
    id: str = Field(default_factory=new_submission_id, description="Unique submission identifier")
    student_handle: str = Field(description="Student identifier")
    canonical: CanonicalDoc = Field(description="Submission content as canonical document")
    rubric_id: str = Field(description="Associated rubric identifier")
    question_id: str = Field(description="Associated question identifier")
    
    @field_validator("id", "rubric_id", "question_id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("student_handle")
    @classmethod
    def validate_student_handle(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Student handle cannot be empty")
        return v.strip()


# ============================================================================
# Evaluation Models
# ============================================================================

class ScoreItem(BaseModel):
    """
    Represents a score for a single rubric criterion with comprehensive  feedback.
    
    Contains the score, comprehensive feedback, and references to evidence
    blocks within the submission document.
    """
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    
    rubric_item_id: str = Field(description="Associated rubric item identifier")
    score: float = Field(ge=0.0, le=100.0, description="Score for this criterion (0-100)")
    
    # Legacy field - kept for backward compatibility
    justification: Optional[str] = Field(
        default=None, 
        description="Legacy justification field (deprecated, use comprehensive feedback fields instead)"
    )
    
    # 7-dimensional comprehensive feedback
    # Using empty string as default instead of None to ensure fields are always present in JSON
    evidence: str = Field(
        default="",
        description="Quoted or paraphrased text from student relevant to this criterion"
    )
    evaluation: str = Field(
        default="",
        description="Critical analysis of accuracy, depth, and completeness"
    )
    completeness_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Estimated completeness percentage (0-100%)"
    )
    strengths: str = Field(
        default="",
        description="What the student did well in this criterion"
    )
    gaps: str = Field(
        default="",
        description="What is missing, unclear, oversimplified, or incorrect"
    )
    guidance: str = Field(
        default="",
        description="Actionable expert-level advice for improvement"
    )
    significance: str = Field(
        default="",
        description="Why the missing elements matter for learning outcomes"
    )
    
    evidence_block_ids: List[str] = Field(description="Block IDs supporting this score")
    
    @field_validator("rubric_item_id")
    @classmethod
    def validate_rubric_item_id(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid rubric item ID format: {v}")
        return v
    
    @field_validator("justification")
    @classmethod
    def validate_justification(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None
    
    @field_validator("evidence_block_ids")
    @classmethod
    def validate_evidence_block_ids(cls, v: List[str]) -> List[str]:
        for block_id in v:
            if not is_valid_id(block_id):
                raise ValueError(f"Invalid evidence block ID format: {block_id}")
        return v
    
    def has_comprehensive_feedback(self) -> bool:
        """Check if comprehensive 7-dimensional feedback is available."""
        return any([
            self.evidence.strip() if self.evidence else False,
            self.evaluation.strip() if self.evaluation else False,
            self.completeness_percentage is not None and self.completeness_percentage > 0,
            self.strengths.strip() if self.strengths else False,
            self.gaps.strip() if self.gaps else False,
            self.guidance.strip() if self.guidance else False,
            self.significance.strip() if self.significance else False
        ])


class EvalResult(BaseModel):
    """
    Represents the complete evaluation result for a submission.
    
    Contains overall score, individual criterion scores, feedback,
    and metadata about the evaluation process.
    """
    model_config = ConfigDict(strict=True, extra="forbid")
    
    submission_id: str = Field(description="Associated submission identifier")
    rubric_id: str = Field(description="Associated rubric identifier")
    total: float = Field(ge=0.0, le=100.0, description="Weighted total score (0-100)")
    items: List[ScoreItem] = Field(description="Individual criterion scores")
    overall_feedback: str = Field(description="General feedback for the submission")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional evaluation metadata")
    
    @field_validator("submission_id", "rubric_id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not is_valid_id(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator("overall_feedback")
    @classmethod
    def validate_feedback(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Overall feedback cannot be empty")
        return v.strip()
    
    @field_validator("items")
    @classmethod
    def validate_items_exist(cls, v: List[ScoreItem]) -> List[ScoreItem]:
        if not v:
            raise ValueError("Evaluation must have at least one score item")
        return v


# ============================================================================
# JSON Serialization Utilities
# ============================================================================

def to_json(model: BaseModel) -> str:
    """
    Convert a Pydantic model to canonical JSON string.
    
    Args:
        model: Pydantic model instance
        
    Returns:
        JSON string with sorted keys and None values excluded
        
    Examples:
        >>> doc = CanonicalDoc(source_files=["test.pdf"], blocks=[])
        >>> json_str = to_json(doc)
        >>> "source_files" in json_str
        True
    """
    return model.model_dump_json(
        exclude_none=True,
        by_alias=False
    )


def from_json(model_cls: type[BaseModel], s: str) -> BaseModel:
    """
    Parse JSON string into a Pydantic model instance.
    
    Args:
        model_cls: Pydantic model class
        s: JSON string to parse
        
    Returns:
        Model instance
        
    Examples:
        >>> json_str = '{"source_files": ["test.pdf"], "blocks": []}'
        >>> doc = from_json(CanonicalDoc, json_str)
        >>> len(doc.source_files)
        1
    """
    return model_cls.model_validate_json(s)


def to_dict(model: BaseModel) -> dict:
    """
    Convert a Pydantic model to a dictionary.
    
    Args:
        model: Pydantic model instance
        
    Returns:
        Dictionary with None values excluded
        
    Examples:
        >>> doc = CanonicalDoc(source_files=["test.pdf"], blocks=[])
        >>> data = to_dict(doc)
        >>> isinstance(data, dict)
        True
    """
    return model.model_dump(
        exclude_none=True,
        by_alias=False
    )


def round_trip_test(model: BaseModel) -> BaseModel:
    """
    Perform a round-trip test: model -> JSON -> model.
    
    Args:
        model: Original model instance
        
    Returns:
        New model instance from round-trip
        
    Raises:
        ValueError: If round-trip fails or models don't match
    """
    json_str = to_json(model)
    reconstructed = from_json(type(model), json_str)
    
    # Compare the essential data (excluding auto-generated timestamps)
    original_dict = to_dict(model)
    reconstructed_dict = to_dict(reconstructed)
    
    if original_dict != reconstructed_dict:
        raise ValueError("Round-trip test failed: models don't match")
    
    return reconstructed