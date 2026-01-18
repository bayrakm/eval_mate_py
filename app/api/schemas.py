"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# Core metadata models for lightweight responses
class RubricMeta(BaseModel):
    """Lightweight rubric metadata for lists and references."""
    id: str
    course: str
    assignment: str
    version: str


class RubricCreateParams(BaseModel):
    """Parameters for rubric creation from uploaded file."""
    # Optional metadata; if missing, infer from filename
    course: Optional[str] = None
    assignment: Optional[str] = None
    version: Optional[str] = "v1"
    prefer_tables: bool = True  # Legacy flag (ignored by ADE extraction)


class RubricResponse(BaseModel):
    """Response for rubric creation/retrieval."""
    meta: RubricMeta
    item_count: int


class QuestionCreateParams(BaseModel):
    """Parameters for question creation from uploaded file."""
    rubric_id: str
    title: Optional[str] = None


class QuestionMeta(BaseModel):
    """Lightweight question metadata for lists and references."""
    id: str
    title: str
    rubric_id: str


class QuestionResponse(BaseModel):
    """Response for question creation/retrieval."""
    meta: QuestionMeta
    created_at: datetime


class SubmissionCreateParams(BaseModel):
    """Parameters for submission creation from uploaded file."""
    rubric_id: str
    question_id: str
    student_handle: str


class SubmissionMeta(BaseModel):
    """Lightweight submission metadata for lists and references."""
    id: str
    rubric_id: str
    question_id: str
    student_handle: str


class SubmissionResponse(BaseModel):
    """Response for submission creation/retrieval."""
    meta: SubmissionMeta
    created_at: datetime


# List response models
class ListRubricsResponse(BaseModel):
    """Response for listing rubrics."""
    items: List[RubricMeta]


class ListQuestionsResponse(BaseModel):
    """Response for listing questions."""
    items: List[QuestionMeta]


class ListSubmissionsResponse(BaseModel):
    """Response for listing submissions."""
    items: List[SubmissionMeta]


# Error response model
class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
