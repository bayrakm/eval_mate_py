"""
FastAPI routes for fusion context management.

This module provides HTTP endpoints for creating, retrieving, and managing
fusion contexts that unify rubric, question, and submission data.
"""

import logging
import os
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.fusion.builder import (
    build_fusion_context, 
    load_fusion_context, 
    list_fusion_contexts,
    validate_fusion_context
)
from app.core.fusion.schema import FusionContext

logger = logging.getLogger(__name__)


# Request/Response models
class BuildFusionRequest(BaseModel):
    """Request model for building fusion context."""
    rubric_id: str
    question_id: str
    submission_id: str


class FusionSummary(BaseModel):
    """Summary information about a fusion context."""
    id: str
    rubric_id: str
    question_id: str
    submission_id: str
    created_at: str
    token_estimate: int
    visual_count: int
    text_block_count: int
    metadata: Dict[str, Any]


class ValidationResult(BaseModel):
    """Validation result for a fusion context."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, Any] = None


# Router setup
router = APIRouter(prefix="/fusion", tags=["Fusion Context"])


@router.post("/build", response_model=FusionContext)
async def create_fusion_context(request: BuildFusionRequest):
    """
    Build a new fusion context from rubric, question, and submission.
    
    This endpoint creates a unified evaluation context by merging the specified
    rubric, question, and submission into a single structured object.
    
    Args:
        request: Request containing the IDs of entities to merge
        
    Returns:
        Complete FusionContext object
        
    Raises:
        HTTPException: If any required entity is not found or validation fails
    """
    try:
        logger.info(f"Building fusion context for request: {request}")
        
        fusion = build_fusion_context(
            rubric_id=request.rubric_id,
            question_id=request.question_id,
            submission_id=request.submission_id
        )
        
        logger.info(f"Successfully created fusion context: {fusion.id}")
        return fusion
        
    except KeyError as e:
        logger.error(f"Entity not found: {e}")
        raise HTTPException(status_code=404, detail=f"Entity not found: {e}")
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Failed to create fusion context: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/build", response_model=FusionContext)
async def create_fusion_context_get(
    rubric_id: str = Query(..., description="ID of the rubric"),
    question_id: str = Query(..., description="ID of the question"),
    submission_id: str = Query(..., description="ID of the submission")
):
    """
    Build fusion context using GET parameters (for easier testing).
    
    Alternative endpoint for creating fusion contexts using query parameters
    instead of request body.
    """
    request = BuildFusionRequest(
        rubric_id=rubric_id,
        question_id=question_id,
        submission_id=submission_id
    )
    return await create_fusion_context(request)


@router.get("/{fusion_id}", response_model=FusionContext)
async def get_fusion_context(fusion_id: str):
    """
    Retrieve a specific fusion context by ID.
    
    Args:
        fusion_id: Unique identifier for the fusion context
        
    Returns:
        Complete FusionContext object
        
    Raises:
        HTTPException: If fusion context is not found
    """
    try:
        fusion = load_fusion_context(fusion_id)
        logger.debug(f"Retrieved fusion context: {fusion_id}")
        return fusion
        
    except FileNotFoundError:
        logger.warning(f"Fusion context not found: {fusion_id}")
        raise HTTPException(status_code=404, detail=f"Fusion context not found: {fusion_id}")
    except ValueError as e:
        logger.error(f"Invalid fusion context data: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid fusion context: {e}")
    except Exception as e:
        logger.error(f"Failed to retrieve fusion context: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/", response_model=List[FusionSummary])
async def list_all_fusion_contexts():
    """
    List all available fusion contexts with summary information.
    
    Returns:
        List of fusion context summaries ordered by creation date (newest first)
    """
    try:
        contexts = list_fusion_contexts()
        logger.debug(f"Retrieved {len(contexts)} fusion contexts")
        
        # Convert to response model
        summaries = []
        for context in contexts:
            if "error" not in context:
                summaries.append(FusionSummary(**context))
            else:
                # Include error contexts with minimal info
                summaries.append(FusionSummary(
                    id=context["id"],
                    rubric_id="error",
                    question_id="error",
                    submission_id="error",
                    created_at=context.get("created_at", "unknown"),
                    token_estimate=0,
                    visual_count=0,
                    text_block_count=0,
                    metadata={"error": context["error"]}
                ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Failed to list fusion contexts: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/{fusion_id}/summary", response_model=FusionSummary)
async def get_fusion_summary(fusion_id: str):
    """
    Get summary information for a specific fusion context.
    
    Args:
        fusion_id: Unique identifier for the fusion context
        
    Returns:
        Summary information about the fusion context
    """
    try:
        fusion = load_fusion_context(fusion_id)
        summary = fusion.get_summary()
        return FusionSummary(**summary)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Fusion context not found: {fusion_id}")
    except Exception as e:
        logger.error(f"Failed to get fusion summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/{fusion_id}/validate", response_model=ValidationResult)
async def validate_fusion(fusion_id: str):
    """
    Validate a fusion context and return validation results.
    
    Args:
        fusion_id: Unique identifier for the fusion context
        
    Returns:
        Validation results including errors and warnings
    """
    try:
        result = validate_fusion_context(fusion_id)
        return ValidationResult(**result)
        
    except Exception as e:
        logger.error(f"Failed to validate fusion context: {e}")
        return ValidationResult(
            valid=False,
            errors=[f"Validation failed: {e}"],
            warnings=[],
            summary={}
        )


@router.get("/{fusion_id}/text", response_model=Dict[str, str])
async def get_fusion_text_content(fusion_id: str):
    """
    Get the text content of a fusion context for inspection.
    
    Args:
        fusion_id: Unique identifier for the fusion context
        
    Returns:
        Dictionary with different text representations
    """
    try:
        fusion = load_fusion_context(fusion_id)
        
        return {
            "fusion_id": fusion.id,
            "question_text": fusion.question_text,
            "submission_text": fusion.submission_text,
            "full_text_content": fusion.get_text_content(),
            "visual_captions": "\n".join([v.caption for v in fusion.submission_visuals]),
            "rubric_summary": "\n".join([
                f"• {item.get('title', 'Untitled')}: {item.get('desc', 'No description')}"
                for item in fusion.rubric_items
            ])
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Fusion context not found: {fusion_id}")
    except Exception as e:
        logger.error(f"Failed to get fusion text content: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.delete("/{fusion_id}")
async def delete_fusion_context(fusion_id: str):
    """
    Delete a fusion context from storage.
    
    Args:
        fusion_id: Unique identifier for the fusion context
        
    Returns:
        Success message
    """
    try:
        fusion_path = f"data/fusion/{fusion_id}.json"
        
        if not os.path.exists(fusion_path):
            raise HTTPException(status_code=404, detail=f"Fusion context not found: {fusion_id}")
        
        os.remove(fusion_path)
        logger.info(f"Deleted fusion context: {fusion_id}")
        
        return {"message": f"Fusion context {fusion_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete fusion context: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/stats/overview")
async def get_fusion_stats():
    """
    Get overview statistics about all fusion contexts.
    
    Returns:
        Dictionary with aggregate statistics
    """
    try:
        contexts = list_fusion_contexts()
        
        total_contexts = len(contexts)
        total_tokens = sum(ctx.get("token_estimate", 0) for ctx in contexts if "error" not in ctx)
        total_visuals = sum(ctx.get("visual_count", 0) for ctx in contexts if "error" not in ctx)
        
        # Group by rubric
        rubric_counts = {}
        for ctx in contexts:
            if "error" not in ctx:
                rubric_id = ctx.get("rubric_id", "unknown")
                rubric_counts[rubric_id] = rubric_counts.get(rubric_id, 0) + 1
        
        return {
            "total_fusion_contexts": total_contexts,
            "total_estimated_tokens": total_tokens,
            "total_visuals": total_visuals,
            "average_tokens_per_context": total_tokens / max(total_contexts, 1),
            "contexts_by_rubric": rubric_counts,
            "error_contexts": len([ctx for ctx in contexts if "error" in ctx])
        }
        
    except Exception as e:
        logger.error(f"Failed to get fusion stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")