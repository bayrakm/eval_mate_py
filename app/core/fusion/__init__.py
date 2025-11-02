"""
Fusion module for building unified evaluation contexts.

This module provides functionality to merge rubric, question, and submission
data into a single structured FusionContext object for LLM evaluation.
"""

from .schema import FusionContext, FusionVisual
from .builder import build_fusion_context
from .utils import estimate_tokens, clean_text

__all__ = [
    "FusionContext",
    "FusionVisual", 
    "build_fusion_context",
    "estimate_tokens",
    "clean_text",
]