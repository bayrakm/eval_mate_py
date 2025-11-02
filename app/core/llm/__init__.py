"""
LLM Integration Module

Handles integration with Large Language Models for various EvalMate features.
This module provides abstractions for model selection, API calls, and response processing.

Phase 7: Visual Captioning (Multimodal LLM Integration)
"""

from .model_config import (
    ModelName, 
    get_available_model, 
    get_openai_api_key,
    is_multimodal_model,
    validate_model_config
)

from .model_api import (
    generate_caption_with_openai,
    batch_generate_captions,
    fallback_caption_from_ocr,
    test_api_connection
)

from .multimodal_context import (
    MultimodalContext,
    MultimodalContextBuilder,
    create_evaluation_context
)

__all__ = [
    # Model Configuration
    "ModelName",
    "get_available_model", 
    "get_openai_api_key",
    "is_multimodal_model",
    "validate_model_config",
    
    # API Functions
    "generate_caption_with_openai",
    "batch_generate_captions", 
    "fallback_caption_from_ocr",
    "test_api_connection",
    
    # Context Building
    "MultimodalContext",
    "MultimodalContextBuilder",
    "create_evaluation_context"
]