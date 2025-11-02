"""
Fusion Builder - Unified Evaluation Context Assembly

This module implements the core fusion logic that combines rubric, question,
and submission data into a single structured FusionContext object for LLM evaluation.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List

from app.core.models.schemas import Rubric, Question, Submission
from app.core.fusion.schema import FusionContext, FusionVisual
from app.core.fusion.utils import estimate_tokens, clean_text, validate_fusion_completeness
from app.core.store import repo

logger = logging.getLogger(__name__)


def build_multimodal_context(rubric: Rubric, question: Question, submission: Submission) -> Dict[str, Any]:
    """
    Build multimodal context from rubric, question, and submission.
    
    This function extracts and formats content from the three core entities
    into a structured dictionary for fusion context creation.
    
    Args:
        rubric: Rubric entity with evaluation criteria
        question: Question entity with assignment prompt
        submission: Submission entity with student work
        
    Returns:
        Dictionary with structured context data
    """
    logger.debug(f"Building multimodal context for submission {submission.id}")
    
    # Extract rubric items
    rubric_items = []
    for item in rubric.items:
        rubric_items.append({
            "id": item.id,
            "title": item.title,
            "desc": item.description,
            "weight": item.weight,
            "criterion": item.criterion.value
        })
    
    # Extract question text
    question_text = ""
    if question.canonical and question.canonical.blocks:
        question_blocks = [block.text for block in question.canonical.blocks if block.kind == "text" and block.text]
        question_text = "\n".join(question_blocks)
    
    # Extract submission text and visuals
    submission_text = ""
    submission_visuals = []
    
    if submission.canonical and submission.canonical.blocks:
        text_blocks = []
        
        for block in submission.canonical.blocks:
            if block.kind == "text" and block.text:
                text_blocks.append(clean_text(block.text))
            elif block.kind == "visual" and block.visual:
                visual_data = {
                    "id": block.visual.id,
                    "type": block.visual.type,
                    "caption": block.visual.caption_text or "Visual content (no caption available)",
                    "ocr_text": block.visual.ocr_text,
                }
                submission_visuals.append(visual_data)
        
        submission_text = "\n".join(text_blocks)
    
    return {
        "rubric": rubric_items,
        "question": clean_text(question_text),
        "submission_text": clean_text(submission_text),
        "submission_visuals": submission_visuals
    }


def build_fusion_context(rubric_id: str, question_id: str, submission_id: str) -> FusionContext:
    """
    Build a FusionContext by fetching entities from repo and merging their content.
    
    This is the main entry point for fusion context creation. It validates that
    the rubric, question, and submission are properly linked, assembles their content,
    computes metadata, and saves the result to persistent storage.
    
    Args:
        rubric_id: ID of the rubric containing evaluation criteria
        question_id: ID of the question/assignment prompt
        submission_id: ID of the student submission
        
    Returns:
        FusionContext object with all assembled data
        
    Raises:
        KeyError: If any of the required entities are not found
        ValueError: If entities are not properly linked
        RuntimeError: If fusion context creation fails
    """
    logger.info(f"Building fusion context for rubric={rubric_id}, question={question_id}, submission={submission_id}")
    
    try:
        # Fetch entities from repository
        rubric = repo.get_rubric(rubric_id)
        question = repo.get_question(question_id)
        submission = repo.get_submission(submission_id)
        
        # Validate entity relationships
        if question.rubric_id != rubric_id:
            raise ValueError(f"Question {question_id} is not linked to rubric {rubric_id}")
        
        if submission.rubric_id != rubric_id:
            raise ValueError(f"Submission {submission_id} is not linked to rubric {rubric_id}")
        
        if submission.question_id != question_id:
            raise ValueError(f"Submission {submission_id} is not linked to question {question_id}")
        
        logger.debug("Entity relationships validated successfully")
        
        # Build multimodal context from entities
        context_dict = build_multimodal_context(rubric, question, submission)
        
        # Validate context completeness
        validation_errors = validate_fusion_completeness(context_dict)
        if validation_errors:
            logger.warning(f"Fusion context validation warnings: {validation_errors}")
        
        # Compute token estimate for the combined content
        combined_text_parts = [
            context_dict["question"],
            context_dict["submission_text"],
        ]
        
        # Add visual captions to token estimate
        for visual in context_dict["submission_visuals"]:
            combined_text_parts.append(visual["caption"])
            if visual.get("ocr_text"):
                combined_text_parts.append(visual["ocr_text"])
        
        # Add rubric content to token estimate
        for item in context_dict["rubric"]:
            if item.get("title"):
                combined_text_parts.append(item["title"])
            if item.get("desc"):
                combined_text_parts.append(item["desc"])
        
        combined_text = "\n".join(filter(None, combined_text_parts))
        token_estimate = estimate_tokens(combined_text)
        
        # Create fusion ID
        fusion_id = f"FUSION-{submission_id}"
        
        # Build FusionContext object
        fusion = FusionContext(
            id=fusion_id,
            rubric_id=rubric_id,
            question_id=question_id,
            submission_id=submission_id,
            rubric_items=context_dict["rubric"],
            question_text=context_dict["question"],
            submission_text=context_dict["submission_text"],
            submission_visuals=[
                FusionVisual(**visual_data) for visual_data in context_dict["submission_visuals"]
            ],
            created_at=datetime.utcnow(),
            token_estimate=token_estimate,
            visual_count=len(context_dict["submission_visuals"]),
            text_block_count=len([block for block in context_dict["submission_text"].split("\n") if block.strip()]),
            metadata={
                "rubric_version": getattr(rubric, "version", "unknown"),
                "student": getattr(submission, "student_handle", "unknown"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
                "fusion_builder_version": "1.0",
                "created_by": "fusion_builder",
            },
        )
        
        # Save to persistent storage
        fusion_dir = "data/fusion"
        os.makedirs(fusion_dir, exist_ok=True)
        save_path = os.path.join(fusion_dir, f"{fusion_id}.json")
        
        fusion.save_json(save_path)
        logger.info(f"Fusion context saved to {save_path}")
        
        # Log summary statistics
        logger.info(
            f"Fusion context created successfully: "
            f"token_estimate={fusion.token_estimate}, "
            f"visual_count={fusion.visual_count}, "
            f"text_blocks={fusion.text_block_count}, "
            f"rubric_items={len(fusion.rubric_items)}"
        )
        
        return fusion
        
    except KeyError as e:
        logger.error(f"Entity not found during fusion context creation: {e}")
        raise
    except ValueError as e:
        logger.error(f"Entity relationship validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to build fusion context: {e}")
        raise RuntimeError(f"Fusion context creation failed: {e}")


def load_fusion_context(fusion_id: str) -> FusionContext:
    """
    Load a previously saved fusion context from storage.
    
    Args:
        fusion_id: ID of the fusion context to load
        
    Returns:
        FusionContext object
        
    Raises:
        FileNotFoundError: If fusion context file doesn't exist
        ValueError: If fusion context data is invalid
    """
    fusion_path = f"data/fusion/{fusion_id}.json"
    
    if not os.path.exists(fusion_path):
        raise FileNotFoundError(f"Fusion context not found: {fusion_id}")
    
    try:
        fusion = FusionContext.load_json(fusion_path)
        logger.debug(f"Loaded fusion context from {fusion_path}")
        return fusion
    except Exception as e:
        logger.error(f"Failed to load fusion context {fusion_id}: {e}")
        raise ValueError(f"Invalid fusion context data: {e}")


def list_fusion_contexts() -> List[Dict[str, Any]]:
    """
    List all available fusion contexts with summary information.
    
    Returns:
        List of dictionaries with fusion context summaries
    """
    fusion_dir = "data/fusion"
    
    if not os.path.exists(fusion_dir):
        return []
    
    contexts = []
    for filename in os.listdir(fusion_dir):
        if filename.endswith(".json"):
            fusion_id = filename[:-5]  # Remove .json extension
            try:
                fusion = load_fusion_context(fusion_id)
                contexts.append(fusion.get_summary())
            except Exception as e:
                logger.warning(f"Failed to load fusion context {fusion_id}: {e}")
                # Add error entry
                contexts.append({
                    "id": fusion_id,
                    "error": str(e),
                    "created_at": "unknown"
                })
    
    # Sort by creation date (newest first)
    contexts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return contexts


def validate_fusion_context(fusion_id: str) -> Dict[str, Any]:
    """
    Validate a fusion context and return validation results.
    
    Args:
        fusion_id: ID of the fusion context to validate
        
    Returns:
        Dictionary with validation results
    """
    try:
        fusion = load_fusion_context(fusion_id)
        
        # Basic validation
        errors = []
        warnings = []
        
        # Check required fields
        if not fusion.question_text.strip():
            errors.append("Empty question text")
        
        if not fusion.submission_text.strip() and not fusion.submission_visuals:
            errors.append("Empty submission (no text or visuals)")
        
        if not fusion.rubric_items:
            errors.append("No rubric items")
        
        # Check token limits (warning if very large)
        if fusion.token_estimate > 100000:
            warnings.append(f"Very large token estimate: {fusion.token_estimate}")
        
        # Check visual captions
        visual_without_captions = [
            v.id for v in fusion.submission_visuals 
            if not v.caption or v.caption.strip() == "Visual content (no caption available)"
        ]
        if visual_without_captions:
            warnings.append(f"Visuals without proper captions: {visual_without_captions}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "summary": fusion.get_summary()
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to load/validate fusion context: {e}"],
            "warnings": [],
            "summary": None
        }