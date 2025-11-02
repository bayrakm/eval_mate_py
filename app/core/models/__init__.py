"""
Data models and schemas for EvalMate.

Contains dataclasses and schemas for all domain objects including
rubrics, questions, submissions, and evaluation results.

Phase 1: Complete Pydantic models with validation and serialization utilities.
"""

# Core schema imports
try:
    from .schemas import (
        # Enums and literals
        VisualType, RubricCriterion, BlockKind,
        
        # Core models
        VisualBlock, DocBlock, CanonicalDoc,
        RubricItem, Rubric, Question, Submission,
        ScoreItem, EvalResult,
        
        # Serialization utilities
        to_json, from_json, to_dict, round_trip_test
    )
    
    # ID utilities
    from .ids import (
        new_id, is_valid_id, parse_id_components, get_id_prefix, is_id_type,
        new_doc_id, new_block_id, new_rubric_id, new_question_id,
        new_submission_id, new_eval_id, new_rubric_item_id, new_visual_id
    )
    
    # Validation utilities
    from .validators import (
        validate_weights_sum, validate_evidence_blocks_exist,
        validate_block_integrity, validate_ids, validate_rubric_item_references,
        validate_submission_consistency
    )
    
    __all__ = [
        # Enums
        "VisualType", "RubricCriterion", "BlockKind",
        
        # Models
        "VisualBlock", "DocBlock", "CanonicalDoc",
        "RubricItem", "Rubric", "Question", "Submission",
        "ScoreItem", "EvalResult",
        
        # Serialization
        "to_json", "from_json", "to_dict", "round_trip_test",
        
        # ID utilities
        "new_id", "is_valid_id", "parse_id_components", "get_id_prefix", "is_id_type",
        "new_doc_id", "new_block_id", "new_rubric_id", "new_question_id",
        "new_submission_id", "new_eval_id", "new_rubric_item_id", "new_visual_id",
        
        # Validators
        "validate_weights_sum", "validate_evidence_blocks_exist",
        "validate_block_integrity", "validate_ids", "validate_rubric_item_references",
        "validate_submission_consistency"
    ]
    
except ImportError:
    # Pydantic not available - provide minimal interface
    __all__ = []
    
    def _pydantic_not_available(*args, **kwargs):
        raise ImportError(
            "Pydantic is required for Phase 1 models. "
            "Install with: pip install -e ."
        )
    
    # Create placeholder functions
    globals().update({
        name: _pydantic_not_available 
        for name in [
            "VisualType", "RubricCriterion", "VisualBlock", "DocBlock", 
            "CanonicalDoc", "RubricItem", "Rubric", "Question", "Submission",
            "ScoreItem", "EvalResult", "to_json", "from_json", "to_dict"
        ]
    })