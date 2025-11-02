"""
Cross-model validation utilities for EvalMate.

Provides independent, reusable validators that enforce business rules
and data integrity across multiple model types.
"""

from typing import Set
from .schemas import Rubric, EvalResult, CanonicalDoc, Submission, DocBlock


def validate_weights_sum(rubric: Rubric, *, tol: float = 0.01) -> None:
    """
    Validate that rubric item weights sum to approximately 1.0.
    
    Args:
        rubric: Rubric instance to validate
        tol: Tolerance for floating point comparison (default: 0.01)
        
    Raises:
        ValueError: If weights don't sum to 1.0 within tolerance
        
    Examples:
        >>> from core.models.schemas import Rubric, RubricItem, CanonicalDoc, RubricCriterion
        >>> from core.models.ids import new_rubric_id, new_doc_id
        >>> items = [
        ...     RubricItem(title="Content", description="Content quality", 
        ...                weight=0.5, criterion=RubricCriterion.CONTENT),
        ...     RubricItem(title="Structure", description="Document structure", 
        ...                weight=0.5, criterion=RubricCriterion.STRUCTURE)
        ... ]
        >>> doc = CanonicalDoc(source_files=["rubric.pdf"], blocks=[])
        >>> rubric = Rubric(course="CS101", assignment="A1", version="v1", 
        ...                 items=items, canonical=doc)
        >>> validate_weights_sum(rubric)  # Should not raise
    """
    if not rubric.items:
        raise ValueError("Rubric has no items to validate")
    
    total_weight = sum(item.weight for item in rubric.items)
    
    if abs(total_weight - 1.0) > tol:
        raise ValueError(
            f"Rubric weights sum to {total_weight:.6f}, expected 1.0 ± {tol}. "
            f"Difference: {abs(total_weight - 1.0):.6f}"
        )


def validate_evidence_blocks_exist(result: EvalResult, submission: Submission) -> None:
    """
    Validate that all evidence block IDs in evaluation results exist in the submission.
    
    Args:
        result: Evaluation result to validate
        submission: Associated submission containing blocks
        
    Raises:
        ValueError: If any evidence block ID doesn't exist in submission
        
    Examples:
        >>> # This would pass if all evidence_block_ids exist in submission.canonical.blocks
        >>> validate_evidence_blocks_exist(eval_result, submission)
    """
    # Get all block IDs from the submission's canonical document
    submission_block_ids = {block.id for block in submission.canonical.blocks}
    
    # Check each score item's evidence block IDs
    invalid_refs = []
    
    for i, score_item in enumerate(result.items):
        for block_id in score_item.evidence_block_ids:
            if block_id not in submission_block_ids:
                invalid_refs.append(f"Score item {i}: block ID '{block_id}'")
    
    if invalid_refs:
        raise ValueError(
            f"Invalid evidence block references found:\n" + 
            "\n".join(f"  - {ref}" for ref in invalid_refs) +
            f"\nAvailable block IDs: {sorted(submission_block_ids)}"
        )


def validate_block_integrity(doc: CanonicalDoc) -> None:
    """
    Validate the integrity of blocks within a canonical document.
    
    Checks for:
    - Unique block IDs
    - Proper content for each block kind
    - Visual block integrity
    
    Args:
        doc: Canonical document to validate
        
    Raises:
        ValueError: If any integrity checks fail
        
    Examples:
        >>> from core.models.schemas import CanonicalDoc, DocBlock
        >>> blocks = [
        ...     DocBlock(kind="text", text="Sample text content"),
        ...     DocBlock(kind="visual", visual=VisualBlock(type="figure", source_path="fig1.png"))
        ... ]
        >>> doc = CanonicalDoc(source_files=["test.pdf"], blocks=blocks)
        >>> validate_block_integrity(doc)  # Should not raise
    """
    if not doc.blocks:
        return  # Empty documents are valid
    
    # Check for unique block IDs
    block_ids = [block.id for block in doc.blocks]
    unique_ids = set(block_ids)
    
    if len(unique_ids) != len(block_ids):
        duplicates = []
        seen = set()
        for block_id in block_ids:
            if block_id in seen:
                duplicates.append(block_id)
            seen.add(block_id)
        raise ValueError(f"Duplicate block IDs found: {duplicates}")
    
    # Validate each block's content requirements
    for i, block in enumerate(doc.blocks):
        try:
            if block.kind == "text":
                if not block.text or not block.text.strip():
                    raise ValueError(f"Text block {i} (ID: {block.id}) has empty text content")
                if block.visual is not None:
                    raise ValueError(f"Text block {i} (ID: {block.id}) cannot have visual content")
            
            elif block.kind == "visual":
                if block.visual is None:
                    raise ValueError(f"Visual block {i} (ID: {block.id}) missing visual content")
                if block.text is not None:
                    raise ValueError(f"Visual block {i} (ID: {block.id}) cannot have text content")
                
                # Validate visual block structure
                if not block.visual.source_path.strip():
                    raise ValueError(f"Visual block {i} (ID: {block.id}) has empty source_path")
            
        except Exception as e:
            raise ValueError(f"Block integrity error in block {i}: {e}")


def validate_ids(*models) -> None:
    """
    Validate ID formats for one or more model instances.
    
    Recursively checks all .id fields in the provided models using
    the is_valid_id function from the ids module.
    
    Args:
        *models: Variable number of model instances to validate
        
    Raises:
        ValueError: If any ID has invalid format
        
    Examples:
        >>> validate_ids(rubric, question, submission)  # Check multiple models
        >>> validate_ids(doc)  # Check single model
    """
    from .ids import is_valid_id
    
    invalid_ids = []
    
    def _check_model(obj, path=""):
        """Recursively check IDs in a model and its nested objects."""
        if hasattr(obj, 'id') and hasattr(obj, '__class__'):
            if hasattr(obj.__class__, '__annotations__') and 'id' in obj.__class__.__annotations__:
                if not is_valid_id(obj.id):
                    invalid_ids.append(f"{path}.id: '{obj.id}'")
        
        # Check nested objects
        if hasattr(obj, '__dict__'):
            for attr_name, attr_value in obj.__dict__.items():
                current_path = f"{path}.{attr_name}" if path else attr_name
                
                if hasattr(attr_value, 'id') and hasattr(attr_value, '__class__'):
                    _check_model(attr_value, current_path)
                elif isinstance(attr_value, (list, tuple)):
                    for i, item in enumerate(attr_value):
                        if hasattr(item, 'id') and hasattr(item, '__class__'):
                            _check_model(item, f"{current_path}[{i}]")
    
    # Check each provided model
    for i, model in enumerate(models):
        model_name = f"model_{i}" if not hasattr(model, '__class__') else model.__class__.__name__
        _check_model(model, model_name)
    
    if invalid_ids:
        raise ValueError(
            f"Invalid ID formats found:\n" + 
            "\n".join(f"  - {invalid_id}" for invalid_id in invalid_ids)
        )


def validate_rubric_item_references(result: EvalResult, rubric: Rubric) -> None:
    """
    Validate that all rubric item IDs in evaluation results exist in the rubric.
    
    Args:
        result: Evaluation result to validate  
        rubric: Associated rubric containing items
        
    Raises:
        ValueError: If any rubric item ID doesn't exist in rubric
    """
    rubric_item_ids = {item.id for item in rubric.items}
    
    invalid_refs = []
    for i, score_item in enumerate(result.items):
        if score_item.rubric_item_id not in rubric_item_ids:
            invalid_refs.append(f"Score item {i}: rubric item ID '{score_item.rubric_item_id}'")
    
    if invalid_refs:
        raise ValueError(
            f"Invalid rubric item references found:\n" + 
            "\n".join(f"  - {ref}" for ref in invalid_refs) +
            f"\nAvailable rubric item IDs: {sorted(rubric_item_ids)}"
        )


def validate_submission_consistency(submission: Submission, question=None, rubric=None) -> None:
    """
    Validate consistency between submission and associated question/rubric.
    
    Args:
        submission: Submission to validate
        question: Optional associated question for additional validation
        rubric: Optional associated rubric for additional validation
        
    Raises:
        ValueError: If consistency checks fail
    """
    from .ids import is_id_type
    
    # Basic ID format validation
    if not is_id_type(submission.rubric_id, "rubric"):
        raise ValueError(f"Submission rubric_id should reference a rubric: {submission.rubric_id}")
    
    if not is_id_type(submission.question_id, "question"):
        raise ValueError(f"Submission question_id should reference a question: {submission.question_id}")
    
    # Cross-reference validation if objects provided
    if question and submission.question_id != question.id:
        raise ValueError(
            f"Submission question_id '{submission.question_id}' doesn't match "
            f"provided question ID '{question.id}'"
        )
    
    if rubric and submission.rubric_id != rubric.id:
        raise ValueError(
            f"Submission rubric_id '{submission.rubric_id}' doesn't match "
            f"provided rubric ID '{rubric.id}'"
        )
    
    if question and rubric and question.rubric_id != rubric.id:
        raise ValueError(
            f"Question rubric_id '{question.rubric_id}' doesn't match "
            f"rubric ID '{rubric.id}'"
        )