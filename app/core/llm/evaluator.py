"""
LLM Evaluation Engine

Main evaluation pipeline that consumes FusionContext and produces EvalResult.
Handles per-criterion evaluation, schema validation, and persistence.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

import openai
from openai import OpenAI

from app.core.llm.prompts import EVAL_SYSTEM_PROMPT, EVAL_USER_PREFIX, EVAL_JSON_SCHEMA_TEXT
from app.core.llm.json_guard import parse_strict_json, try_repair_json
from app.core.llm.chunking import slice_submission_for_item
from app.core.llm.rate_limit import retry_llm_with_logging
from app.core.fusion.builder import build_fusion_context
from app.core.models.schemas import EvalResult, ScoreItem
from app.core.models.validators import (
    validate_weights_sum, validate_evidence_blocks_exist, validate_ids
)
from app.core.store import repo
from app.core.fusion.utils import estimate_tokens

logger = logging.getLogger(__name__)

# Default model preference order
DEFAULT_MODEL_ORDER = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _pick_model() -> str:
    """Select the model to use, allowing OPENAI_MODEL override."""
    return os.getenv("OPENAI_MODEL") or DEFAULT_MODEL_ORDER[0]


def _build_messages(rubric_json: str, question_text: str, submission_text: str, visuals_json: str) -> List[Dict[str, str]]:
    """Build OpenAI chat messages for evaluation."""
    return [
        {"role": "system", "content": EVAL_SYSTEM_PROMPT},
        {"role": "user", "content": EVAL_USER_PREFIX.format(
            rubric_json=rubric_json,
            question_text=question_text,
            submission_text=submission_text,
            visuals_json=visuals_json,
            schema_text=EVAL_JSON_SCHEMA_TEXT
        )}
    ]


def _normalize_visuals_for_prompt(sub_visuals: List[dict], allow_ocr: bool = True) -> List[dict]:
    """Keep only fields we want the model to see."""
    normalized = []
    for v in sub_visuals:
        visual_data = {
            "id": v.get("id"),
            "type": v.get("type"),
            "caption": v.get("caption"),
        }
        if allow_ocr and v.get("ocr_text"):
            visual_data["ocr_text"] = v.get("ocr_text")
        normalized.append(visual_data)
    return normalized


def _keywords_for_item(title: str, desc: str) -> List[str]:
    """Extract keywords from rubric item for content slicing."""
    base = (title or "") + " " + (desc or "")
    tokens = [t.strip(".,:;()").lower() for t in base.split() if len(t) > 3]
    # Return unique keywords, limited to reasonable number
    return list(set(tokens))[:12]


@retry_llm_with_logging
def _per_item_evaluate(model: str, item: dict, ctx: dict) -> dict:
    """
    Evaluate a single rubric item using the LLM.
    
    Args:
        model: OpenAI model name
        item: Single rubric item dict
        ctx: Context with question, submission_text, submission_visuals
        
    Returns:
        Parsed JSON response from the model
    """
    # Slice submission text for this item to keep prompt manageable
    item_text = slice_submission_for_item(
        ctx["submission_text"],
        _keywords_for_item(item.get("title", ""), item.get("description", "")),
        max_chars=12000
    )

    visuals = _normalize_visuals_for_prompt(ctx["submission_visuals"], allow_ocr=True)

    messages = _build_messages(
        rubric_json=json.dumps([item], ensure_ascii=False),
        question_text=ctx["question"],
        submission_text=item_text,
        visuals_json=json.dumps(visuals, ensure_ascii=False)
    )

    logger.info(f"Evaluating rubric item {item.get('id')} with model {model}")
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=900
    )
    
    text = response.choices[0].message.content
    logger.debug(f"Model response for item {item.get('id')}: {text[:200]}...")
    
    try:
        return parse_strict_json(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed for item {item.get('id')}: {e}")
        return try_repair_json(text)


def evaluate_submission(rubric_id: str, question_id: str, submission_id: str) -> EvalResult:
    """
    Build fusion context and run the LLM to evaluate per rubric item.
    Returns EvalResult and saves it via repo.
    
    Args:
        rubric_id: ID of the rubric to evaluate against
        question_id: ID of the assignment question
        submission_id: ID of the student submission
        
    Returns:
        Complete EvalResult with scores, justifications, and feedback
    """
    logger.info(f"Starting evaluation: rubric={rubric_id}, question={question_id}, submission={submission_id}")
    
    # Build fusion context (ensures captions exist)
    ctx = build_fusion_context(rubric_id, question_id, submission_id)
    
    # Fetch raw domain objects for validation and metadata
    rubric = repo.get_rubric(rubric_id)
    submission = repo.get_submission(submission_id)

    # Validate rubric weights before evaluation
    validate_weights_sum(rubric)

    model = _pick_model()
    logger.info(f"Using model: {model}")
    
    all_items_output: List[ScoreItem] = []

    # Evaluate each rubric item separately
    for item in ctx.rubric_items:
        logger.info(f"Evaluating rubric item: {item['id']}")
        
        try:
            partial = _per_item_evaluate(model, item, {
                "question": ctx.question_text,
                "submission_text": ctx.submission_text,
                "submission_visuals": [v.model_dump() for v in ctx.submission_visuals],
            })

            # Expect structure with 'items' array. If model returns multiple, take first.
            parsed_items = partial.get("items") or []
            if not isinstance(parsed_items, list) or not parsed_items:
                # Force a minimal fallback record if the model misbehaved
                logger.warning(f"Model returned invalid structure for item {item['id']}, using fallback")
                parsed_items = [{
                    "rubric_item_id": item["id"],
                    "score": 0,
                    "justification": "Model returned no structured item; awarding 0 pending manual review.",
                    "evidence_block_ids": []
                }]

            # Use the FIRST item and ensure it has our rubric_item_id
            first = parsed_items[0]
            first["rubric_item_id"] = item["id"]

            score_item = ScoreItem(
                rubric_item_id=first["rubric_item_id"],
                score=float(first.get("score", 0)),
                justification=first.get("justification", "").strip(),
                evidence_block_ids=first.get("evidence_block_ids", [])
            )
            all_items_output.append(score_item)
            logger.info(f"Item {item['id']} scored: {score_item.score}")
            
        except Exception as e:
            logger.error(f"Error evaluating item {item['id']}: {e}")
            # Create fallback score item
            fallback_item = ScoreItem(
                rubric_item_id=item["id"],
                score=0.0,
                justification=f"Evaluation failed due to error: {str(e)}",
                evidence_block_ids=[]
            )
            all_items_output.append(fallback_item)

    # Compose overall feedback - synthesize from issues with low scores
    top_issues = [s.justification for s in all_items_output if s.score < 70][:3]
    if top_issues:
        overall_feedback = "Areas for improvement: " + " ".join(top_issues)
    else:
        overall_feedback = "Well done. See criterion-specific feedback for details."

    # Compute weighted total score
    weights = {ri.id: ri.weight for ri in rubric.items}
    total = 0.0
    for s in all_items_output:
        weight = float(weights.get(s.rubric_item_id, 0))
        total += weight * float(s.score)
    
    # Normalize to 0–100 range
    total = round(total, 2)

    # Create EvalResult
    result = EvalResult(
        submission_id=submission_id,
        rubric_id=rubric_id,
        total=total,
        items=all_items_output,
        overall_feedback=overall_feedback,
        metadata={
            "model": model,
            "evaluated_at": datetime.utcnow().isoformat(),
            "token_estimate": str(estimate_tokens(ctx.submission_text + " ".join(v.caption for v in ctx.submission_visuals))),
            "student": submission.student_handle,
            "fusion_context_id": ctx.id
        }
    )

    # Run cross-model validations
    validate_evidence_blocks_exist(result, submission)
    validate_ids(result)

    # Persist the result
    repo.save_eval_result(result)
    logger.info(f"Saved EvalResult for submission {submission_id} with total score {total}")
    
    return result