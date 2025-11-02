"""
Chunking - Phase 9

Budget tokens per rubric item and slice submission content intelligently.
"""

from typing import List
from app.core.fusion.utils import clean_text


def slice_submission_for_item(submission_text: str, item_keywords: List[str], max_chars: int = 8000) -> str:
    """
    Simple heuristic: prioritize paragraphs containing item keywords, then fill up to max_chars.
    
    Args:
        submission_text: Full text content from submission
        item_keywords: Keywords extracted from rubric item title/description
        max_chars: Maximum characters to include in slice
        
    Returns:
        Sliced and cleaned text optimized for the rubric item
    """
    if not submission_text or not submission_text.strip():
        return ""
        
    # Split into paragraphs and score by keyword relevance
    paragraphs = [p.strip() for p in submission_text.split("\n") if p.strip()]
    if not paragraphs:
        return clean_text(submission_text)[:max_chars]
    
    scored = []
    for p in paragraphs:
        # Score paragraph by keyword matches (case insensitive)
        score = sum(1 for k in item_keywords if k.lower() in p.lower())
        scored.append((score, p))
    
    # Sort by relevance score (descending), then by length (ascending for tie-breaking)
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    
    # Accumulate paragraphs up to max_chars
    acc, total = [], 0
    for score, p in scored:
        if total + len(p) + 1 > max_chars:  # +1 for newline
            break
        acc.append(p)
        total += len(p) + 1
    
    if not acc:
        # Fallback: take the first N chars if no paragraphs fit
        return clean_text(submission_text)[:max_chars]
    
    return "\n".join(acc)