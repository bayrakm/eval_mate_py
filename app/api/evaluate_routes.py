"""
Evaluation API Routes - Phase 9

FastAPI endpoints for LLM-based evaluation.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.core.llm.evaluator import evaluate_submission_narrative
from app.core.models.schemas import EvalResult
from app.core.store import repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


@router.post("/", response_model=EvalResult)
def evaluate(
    rubric_id: str = Query(..., description="ID of the rubric to evaluate against"),
    question_id: str = Query(..., description="ID of the assignment question"),
    submission_id: str = Query(..., description="ID of the student submission")
) -> EvalResult:
    """
    Evaluate a student submission against a rubric using LLM (Narrative Format).
    
    This endpoint triggers the evaluation pipeline using narrative feedback:
    1. Builds fusion context from rubric, question, and submission
    2. Runs LLM evaluation with narrative format (no per-item scores)
    3. Returns comprehensive paragraph-style feedback
    
    Returns EvalResult with narrative_evaluation, narrative_strengths, narrative_gaps, and narrative_guidance.
    """
    try:
        logger.info(f"API evaluation request: rubric={rubric_id}, question={question_id}, submission={submission_id}")
        result = evaluate_submission_narrative(rubric_id, question_id, submission_id)
        return result
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/result/{submission_id}", response_model=Optional[EvalResult])
def get_evaluation_result(submission_id: str) -> Optional[EvalResult]:
    """
    Retrieve the evaluation result for a submission if it exists.
    
    Args:
        submission_id: ID of the submission to get results for
        
    Returns:
        EvalResult if found, None otherwise
    """
    try:
        result = repo.get_eval_result(submission_id)
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve evaluation result for {submission_id}: {e}")
        return None


@router.get("/status/{submission_id}")
def get_evaluation_status(submission_id: str) -> dict:
    """
    Check if a submission has been evaluated.
    
    Args:
        submission_id: ID of the submission to check
        
    Returns:
        Status information including whether evaluation exists
    """
    try:
        result = repo.get_eval_result(submission_id)
        if result:
            return {
                "evaluated": True,
                "total_score": result.total,
                "evaluated_at": result.metadata.get("evaluated_at"),
                "model": result.metadata.get("model")
            }
        else:
            return {"evaluated": False}
    except Exception as e:
        logger.error(f"Failed to check evaluation status for {submission_id}: {e}")
        return {"evaluated": False, "error": str(e)}