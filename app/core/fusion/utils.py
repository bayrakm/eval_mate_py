"""
Utility functions for fusion context processing.

This module provides helper functions for text normalization,
token estimation, and other fusion-related operations.
"""

import re
from typing import Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


def clean_text(text: str) -> str:
    """
    Normalize whitespace and remove excessive newlines.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with normalized whitespace
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text.strip()


def estimate_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Approximate token count using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for tokenizer selection
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    if not TIKTOKEN_AVAILABLE:
        # Fallback estimation: roughly 4 characters per token
        return len(text) // 4
    
    try:
        enc = tiktoken.encoding_for_model(model)
    except (KeyError, ValueError):
        # Fall back to base encoding if model not found
        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Ultimate fallback
            return len(text) // 4
    
    try:
        return len(enc.encode(text))
    except Exception:
        # Fallback if encoding fails
        return len(text) // 4


def truncate_text(text: str, max_tokens: int, model: str = "gpt-4o") -> str:
    """
    Truncate text to fit within token limit.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        model: Model name for tokenizer
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    current_tokens = estimate_tokens(text, model)
    if current_tokens <= max_tokens:
        return text
    
    # Rough estimation for truncation
    char_ratio = max_tokens / current_tokens
    target_chars = int(len(text) * char_ratio * 0.9)  # 90% safety margin
    
    if target_chars >= len(text):
        return text
    
    # Truncate and try to end at word boundary
    truncated = text[:target_chars]
    last_space = truncated.rfind(' ')
    if last_space > target_chars * 0.8:  # Don't cut too much
        truncated = truncated[:last_space]
    
    return truncated + "..."


def format_rubric_items(rubric_items: list) -> str:
    """
    Format rubric items into readable text.
    
    Args:
        rubric_items: List of rubric item dictionaries
        
    Returns:
        Formatted rubric text
    """
    if not rubric_items:
        return ""
    
    formatted_items = []
    for item in rubric_items:
        title = item.get('title', 'Untitled')
        desc = item.get('desc', '')
        weight = item.get('weight', 0)
        
        item_text = f"• {title}"
        if weight:
            item_text += f" (Weight: {weight})"
        if desc:
            item_text += f": {desc}"
        
        formatted_items.append(item_text)
    
    return "\n".join(formatted_items)


def validate_fusion_completeness(fusion_data: dict) -> list:
    """
    Validate that fusion context has all required data.
    
    Args:
        fusion_data: Dictionary with fusion context data
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    required_fields = [
        'rubric_id', 'question_id', 'submission_id',
        'rubric_items', 'question_text', 'submission_text'
    ]
    
    for field in required_fields:
        if not fusion_data.get(field):
            errors.append(f"Missing or empty required field: {field}")
    
    # Check rubric items structure
    rubric_items = fusion_data.get('rubric_items', [])
    if not isinstance(rubric_items, list):
        errors.append("rubric_items must be a list")
    elif rubric_items:
        for i, item in enumerate(rubric_items):
            if not isinstance(item, dict):
                errors.append(f"rubric_items[{i}] must be a dictionary")
                continue
            if not item.get('title'):
                errors.append(f"rubric_items[{i}] missing title")
    
    # Check visual items structure
    visuals = fusion_data.get('submission_visuals', [])
    if not isinstance(visuals, list):
        errors.append("submission_visuals must be a list")
    elif visuals:
        for i, visual in enumerate(visuals):
            if not isinstance(visual, dict):
                errors.append(f"submission_visuals[{i}] must be a dictionary")
                continue
            required_visual_fields = ['id', 'type', 'caption']
            for field in required_visual_fields:
                if not visual.get(field):
                    errors.append(f"submission_visuals[{i}] missing {field}")
    
    return errors