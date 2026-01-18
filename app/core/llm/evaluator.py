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


def _build_messages(rubric_json: str, question_text: str, submission_text: str, visuals_json: str, available_block_ids: List[str] = None) -> List[Dict[str, str]]:
    """Build OpenAI chat messages for evaluation."""
    block_ids_info = ""
    if available_block_ids:
        block_ids_info = f"\n\n<AVAILABLE_BLOCK_IDS>\nAvailable block IDs for evidence_block_ids (use only these exact IDs):\n" + "\n".join(f"- {bid}" for bid in available_block_ids) + "\n</AVAILABLE_BLOCK_IDS>"
    
    return [
        {"role": "system", "content": EVAL_SYSTEM_PROMPT},
        {"role": "user", "content": EVAL_USER_PREFIX.format(
            rubric_json=rubric_json,
            question_text=question_text,
            submission_text=submission_text,
            visuals_json=visuals_json,
            schema_text=EVAL_JSON_SCHEMA_TEXT,
            available_block_ids=block_ids_info
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


def _generate_comprehensive_overall_feedback(score_items: List[ScoreItem]) -> str:
    """
    Generate comprehensive overall feedback from score items.
    
    Synthesizes feedback from multiple dimensions: strengths, gaps, and guidance
    to create a holistic summary for the student.
    """
    feedback_parts = []
    
    # Collect strengths from high-scoring items
    strengths_list = []
    for item in score_items:
        if item.score >= 70 and item.strengths:
            strengths_list.append(item.strengths)
    
    if strengths_list:
        # Limit to top 3 strengths
        strengths_summary = " ".join(strengths_list[:3])
        feedback_parts.append(f"**Strengths:** {strengths_summary}")
    
    # Collect improvement areas from low-scoring items
    improvement_areas = []
    for item in score_items:
        if item.score < 70:
            if item.gaps:
                improvement_areas.append(item.gaps)
            elif item.guidance:
                improvement_areas.append(item.guidance)
    
    if improvement_areas:
        # Limit to top 3 improvement areas
        improvements_summary = " ".join(improvement_areas[:3])
        feedback_parts.append(f"**Areas for Improvement:** {improvements_summary}")
    
    # Add overall assessment context
    avg_score = sum(item.score for item in score_items) / len(score_items) if score_items else 0.0
    
    if avg_score >= 80:
        assessment = f"**Overall Assessment:** Excellent work with a score of {avg_score:.1f}/100. "
        assessment += "You demonstrate strong understanding across most criteria. Continue building on your strengths."
    elif avg_score >= 70:
        assessment = f"**Overall Assessment:** Good work with a score of {avg_score:.1f}/100. "
        assessment += "You show solid understanding, with room for improvement in specific areas."
    elif avg_score >= 60:
        assessment = f"**Overall Assessment:** Satisfactory performance with a score of {avg_score:.1f}/100. "
        assessment += "Focus on the improvement areas identified above to enhance your work."
    else:
        assessment = f"**Overall Assessment:** Score of {avg_score:.1f}/100 indicates significant areas need attention. "
        assessment += "Review the detailed feedback for each criterion and work on the specific gaps identified."
    
    feedback_parts.append(assessment)
    
    # If no specific feedback was collected, provide a generic message
    if not feedback_parts:
        feedback_parts.append("See criterion-specific feedback for detailed evaluation of your work.")
    
    return "\n\n".join(feedback_parts)


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
    
    # Get available block IDs for evidence references
    available_block_ids = ctx.get("available_block_ids", [])

    messages = _build_messages(
        rubric_json=json.dumps([item], ensure_ascii=False),
        question_text=ctx["question"],
        submission_text=item_text,
        visuals_json=json.dumps(visuals, ensure_ascii=False),
        available_block_ids=available_block_ids
    )

    logger.info(f"Evaluating rubric item {item.get('id')} with model {model}")
    
    # Use JSON mode for structured output (ensures JSON format)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=2500,  # Increased for 7-dimensional feedback output
        response_format={"type": "json_object"}  # Force JSON output
    )
    
    text = response.choices[0].message.content
    logger.debug(f"Model response for item {item.get('id')}: {text[:500]}...")
    
    try:
        parsed = parse_strict_json(text)
        # Log if 7-dimensional fields are missing
        if parsed.get("items"):
            first_item = parsed["items"][0]
            missing_fields = []
            required_fields = ["evidence", "evaluation", "completeness_percentage", "strengths", "gaps", "guidance", "significance"]
            for field in required_fields:
                if field not in first_item or (isinstance(first_item.get(field), str) and not first_item[field].strip()):
                    missing_fields.append(field)
            if missing_fields:
                logger.warning(f"Item {item.get('id')} missing 7-dimensional fields: {missing_fields}")
        return parsed
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed for item {item.get('id')}: {e}")
        logger.debug(f"Raw response: {text}")
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

    # Get valid block IDs from submission for evidence_block_ids validation
    valid_block_ids = {block.id for block in submission.canonical.blocks}
    logger.debug(f"Valid block IDs for evidence references: {sorted(valid_block_ids)}")

    # Evaluate each rubric item separately
    for item in ctx.rubric_items:
        logger.info(f"Evaluating rubric item: {item['id']}")
        
        try:
            partial = _per_item_evaluate(model, item, {
                "question": ctx.question_text,
                "submission_text": ctx.submission_text,
                "submission_visuals": [v.model_dump() for v in ctx.submission_visuals],
                "available_block_ids": list(valid_block_ids),
            })

            # Expect structure with 'items' array. If model returns multiple, take first.
            parsed_items = partial.get("items") or []
            if not isinstance(parsed_items, list) or not parsed_items:
                # Force a minimal fallback record if the model misbehaved
                logger.warning(f"Model returned invalid structure for item {item['id']}, using fallback")
                error_msg = "Model returned no structured item; awarding 0 pending manual review."
                parsed_items = [{
                    "rubric_item_id": item["id"],
                    "score": 0,
                    "justification": error_msg,
                    "evidence": error_msg[:200],
                    "evaluation": "Model response was invalid; manual review required.",
                    "completeness_percentage": 0.0,
                    "strengths": "Evaluation could not be completed.",
                    "gaps": "Unable to evaluate due to model response error.",
                    "guidance": "Please review this item manually. Check the evaluation logs for details.",
                    "significance": "Manual review is required to ensure proper evaluation.",
                    "evidence_block_ids": []
                }]

            # Use the FIRST item and ensure it has our rubric_item_id
            first = parsed_items[0]
            first["rubric_item_id"] = item["id"]

            # Sanitize evidence_block_ids - only keep valid block IDs from submission
            raw_evidence_ids = first.get("evidence_block_ids", [])
            sanitized_evidence_ids = [
                block_id for block_id in raw_evidence_ids 
                if isinstance(block_id, str) and block_id in valid_block_ids
            ]
            
            # Log if we filtered out invalid IDs
            if raw_evidence_ids and len(sanitized_evidence_ids) < len(raw_evidence_ids):
                invalid_ids = set(raw_evidence_ids) - set(sanitized_evidence_ids)
                logger.warning(
                    f"Filtered out invalid evidence_block_ids for item {item['id']}: {invalid_ids}. "
                    f"Valid block IDs: {sorted(valid_block_ids)}"
                )

            # Extract 7-dimensional feedback or generate from justification if missing
            score = float(first.get("score", 0))
            justification = first.get("justification", "").strip() if first.get("justification") else None
            
            # Check if 7-dimensional feedback is present
            has_7d = any([
                first.get("evidence"),
                first.get("evaluation"),
                first.get("completeness_percentage") is not None,
                first.get("strengths"),
                first.get("gaps"),
                first.get("guidance"),
                first.get("significance")
            ])
            
            if not has_7d and justification:
                # Fallback: Generate 7-dimensional feedback from justification
                logger.warning(
                    f"Item {item['id']} missing 7-dimensional feedback. "
                    f"Generating from justification field. This is a fallback - LLM should provide 7-dimensional feedback."
                )
                # Use justification to populate the 7 dimensions intelligently
                # Extract key parts from justification
                justification_lower = justification.lower()
                
                # Evidence: Use first part of justification as evidence reference
                evidence = justification[:300] + "..." if len(justification) > 300 else justification
                if not evidence:
                    evidence = "See evaluation for details."
                
                # Evaluation: Use full justification
                evaluation = justification if justification else "Evaluation not available."
                
                # Completeness percentage: Use score as estimate
                completeness_percentage = max(0.0, min(100.0, float(score)))
                
                # Strengths: Look for positive indicators in justification
                if score >= 70:
                    strengths = "The submission demonstrates adequate understanding and addresses key requirements."
                elif score >= 50:
                    strengths = "Some understanding is evident, though significant improvements are needed."
                else:
                    strengths = "Limited evidence of understanding. Review the evaluation for specific details."
                
                # Gaps: Extract gap information from justification
                if score < 70:
                    gaps = justification if justification else "Significant areas need improvement."
                else:
                    gaps = "Minor areas for improvement identified in the evaluation."
                
                # Guidance: Generate actionable advice based on score
                if score < 50:
                    guidance = "1. Review the assignment requirements carefully. 2. Ensure all required components are included. 3. Seek clarification if needed."
                elif score < 70:
                    guidance = "1. Address the gaps identified in the evaluation. 2. Strengthen areas with limited coverage. 3. Provide more detailed explanations."
                else:
                    guidance = "Continue building on current strengths. Minor refinements can further enhance the work."
                
                # Significance: Explain why improvements matter
                significance = "Addressing these areas will improve overall performance and demonstrate deeper understanding of the subject matter."
            else:
                # Use 7-dimensional feedback from LLM, but ensure all fields are populated
                evidence = first.get("evidence", "").strip() if first.get("evidence") else ""
                evaluation = first.get("evaluation", "").strip() if first.get("evaluation") else ""
                completeness_percentage = float(first.get("completeness_percentage")) if first.get("completeness_percentage") is not None else max(0.0, min(100.0, float(score)))
                strengths = first.get("strengths", "").strip() if first.get("strengths") else ""
                gaps = first.get("gaps", "").strip() if first.get("gaps") else ""
                guidance = first.get("guidance", "").strip() if first.get("guidance") else ""
                significance = first.get("significance", "").strip() if first.get("significance") else ""
                
                # Fill any missing fields with defaults based on available data
                if not evidence and justification:
                    evidence = justification[:200] + "..." if len(justification) > 200 else justification
                if not evaluation and justification:
                    evaluation = justification
                if not strengths:
                    strengths = "See evaluation for details." if score >= 50 else "Limited evidence of understanding."
                if not gaps:
                    gaps = justification if score < 70 else "Minor areas for improvement."
                if not guidance:
                    guidance = "Review the requirements and improve based on the feedback provided." if score < 70 else "Continue building on current strengths."
                if not significance:
                    significance = "Addressing these areas will improve overall performance and understanding."
                
                # Log if we had to fill missing fields
                missing_count = sum([
                    not first.get("evidence"),
                    not first.get("evaluation"),
                    first.get("completeness_percentage") is None,
                    not first.get("strengths"),
                    not first.get("gaps"),
                    not first.get("guidance"),
                    not first.get("significance")
                ])
                if missing_count > 0:
                    logger.warning(
                        f"Item {item['id']} missing {missing_count} out of 7 dimensional fields. "
                        f"Filled with defaults."
                    )

            # Ensure all 7-dimensional fields are non-empty (use defaults if empty)
            # This ensures fields always appear in JSON output
            if not evidence.strip():
                evidence = "See evaluation for details."
            if not evaluation.strip():
                evaluation = justification if justification else "Evaluation not available."
            if not strengths.strip():
                strengths = "See evaluation for details." if score >= 50 else "Limited evidence of understanding."
            if not gaps.strip():
                gaps = justification if justification and score < 70 else "Review evaluation for specific areas."
            if not guidance.strip():
                guidance = "Review requirements and improve based on feedback." if score < 70 else "Continue building on strengths."
            if not significance.strip():
                significance = "Addressing these areas will improve overall performance and understanding."

            # Create ScoreItem with 7-dimensional feedback support
            score_item = ScoreItem(
                rubric_item_id=first["rubric_item_id"],
                score=score,
                # Legacy justification (backward compatibility)
                justification=justification,
                # 7-dimensional comprehensive feedback (always populated)
                evidence=evidence,
                evaluation=evaluation,
                completeness_percentage=completeness_percentage,
                strengths=strengths,
                gaps=gaps,
                guidance=guidance,
                significance=significance,
                evidence_block_ids=sanitized_evidence_ids
            )
            all_items_output.append(score_item)
            logger.info(f"Item {item['id']} scored: {score_item.score} (comprehensive feedback: {score_item.has_comprehensive_feedback()})")
            
        except Exception as e:
            logger.error(f"Error evaluating item {item['id']}: {e}")
            # Create fallback score item with comprehensive structure
            error_msg = f"Evaluation failed due to error: {str(e)}"
            fallback_item = ScoreItem(
                rubric_item_id=item["id"],
                score=0.0,
                justification=error_msg,
                evidence=error_msg[:200] + "..." if len(error_msg) > 200 else error_msg,
                evaluation=error_msg,
                completeness_percentage=0.0,
                strengths="Evaluation could not be completed.",
                gaps=error_msg,
                guidance="Please review this item manually after fixing the error. Check the evaluation logs for details.",
                significance="Manual review is required to ensure proper evaluation of this criterion.",
                evidence_block_ids=[]
            )
            all_items_output.append(fallback_item)

    # Compose comprehensive overall feedback
    overall_feedback = _generate_comprehensive_overall_feedback(all_items_output)

    # Compute weighted total score
    weights = {ri.id: ri.weight for ri in rubric.items}
    total = 0.0
    for s in all_items_output:
        weight = float(weights.get(s.rubric_item_id, 0))
        total += weight * float(s.score)
    
    # Normalize to 0-100 range
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


def evaluate_submission_narrative(rubric_id: str, question_id: str, submission_id: str) -> EvalResult:
    """
    Build fusion context and run LLM to evaluate using narrative feedback format.
    Returns EvalResult with comprehensive paragraph-style feedback (no scores).
    
    Args:
        rubric_id: ID of the rubric to evaluate against
        question_id: ID of the assignment question
        submission_id: ID of the student submission
        
    Returns:
        EvalResult with narrative_evaluation, narrative_strengths, narrative_gaps, narrative_guidance fields
    """
    logger.info(f"Starting narrative evaluation: rubric={rubric_id}, question={question_id}, submission={submission_id}")
    
    # Build fusion context (ensures captions exist)
    ctx = build_fusion_context(rubric_id, question_id, submission_id)
    
    # Fetch raw domain objects for validation and metadata
    rubric = repo.get_rubric(rubric_id)
    submission = repo.get_submission(submission_id)

    # Validate rubric weights before evaluation
    validate_weights_sum(rubric)

    model = _pick_model()
    logger.info(f"Using model: {model} for narrative evaluation")
    
    # Prepare all rubric items as JSON for the LLM
    rubric_json = json.dumps(ctx.rubric_items, indent=2)
    
    # Prepare visuals
    normalized_visuals = _normalize_visuals_for_prompt(
        [v.model_dump() for v in ctx.submission_visuals],
        allow_ocr=True
    )
    visuals_json = ""
    if normalized_visuals:
        visuals_json = f"<SUBMISSION_VISUALS>\n{json.dumps(normalized_visuals, indent=2)}\n</SUBMISSION_VISUALS>"
    
    # Get valid block IDs from submission
    valid_block_ids = {block.id for block in submission.canonical.blocks}
    
    # Build messages with narrative schema
    messages = [
        {"role": "system", "content": EVAL_SYSTEM_PROMPT},
        {"role": "user", "content": EVAL_USER_PREFIX.format(
            rubric_json=rubric_json,
            question_text=ctx.question_text,
            submission_text=ctx.submission_text,
            visuals_json=visuals_json,
            available_block_ids=""  # Not needed for narrative format
        )}
    ]
    
    # Call OpenAI API
    try:
        logger.info("Calling OpenAI API for narrative evaluation...")
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,  # Longer for narrative paragraphs
            response_format={"type": "json_object"}
        )
        
        raw_text = response.choices[0].message.content
        logger.debug(f"Raw LLM response: {raw_text[:500]}...")
        
        # Parse JSON response
        parsed = json.loads(raw_text)
        
        # Extract narrative fields
        narrative_evaluation = parsed.get("evaluation", "")
        narrative_strengths = parsed.get("strengths", "")
        narrative_gaps = parsed.get("gaps", "")
        narrative_guidance = parsed.get("guidance", "")
        
        # Validate we got content
        if not any([narrative_evaluation, narrative_strengths, narrative_gaps, narrative_guidance]):
            logger.error("LLM returned empty narrative feedback")
            raise ValueError("LLM returned no narrative content")
        
        logger.info("Successfully parsed narrative feedback from LLM")
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API or parsing response: {e}")
        # Provide fallback narrative feedback
        narrative_evaluation = "Evaluation could not be completed due to a technical error. Please review manually."
        narrative_strengths = "Unable to assess strengths at this time."
        narrative_gaps = f"Evaluation error: {str(e)}"
        narrative_guidance = "Please retry the evaluation or contact support for assistance."
    
    # Create EvalResult with narrative format (no scores, empty items list)
    result = EvalResult(
        submission_id=submission_id,
        rubric_id=rubric_id,
        total=0.0,  # No scoring in narrative mode
        items=[],  # No per-criterion items in narrative mode
        overall_feedback="",  # Replaced by narrative fields
        narrative_evaluation=narrative_evaluation,
        narrative_strengths=narrative_strengths,
        narrative_gaps=narrative_gaps,
        narrative_guidance=narrative_guidance,
        metadata={
            "model": model,
            "evaluated_at": datetime.utcnow().isoformat(),
            "evaluation_mode": "narrative",
            "token_estimate": str(estimate_tokens(ctx.submission_text + " ".join(v.caption for v in ctx.submission_visuals))),
            "student": submission.student_handle,
            "fusion_context_id": ctx.id
        }
    )

    # Validate IDs
    validate_ids(result)

    # Persist the result
    repo.save_eval_result(result)
    logger.info(f"Saved narrative EvalResult for submission {submission_id}")
    
    return result