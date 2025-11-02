"""
OpenAI API Wrapper with Robust Error Handling

This module provides a robust interface to OpenAI's multimodal API
with retry logic, fallback handling, and comprehensive error management.

Supports multimodal LLM integration for visual content captioning and evaluation.
"""

import os
import logging
import base64
from pathlib import Path
from typing import Optional, Dict, Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI
from openai._exceptions import RateLimitError, APITimeoutError, APIConnectionError

from app.core.llm.model_config import (
    get_available_model, 
    get_openai_api_key, 
    DEFAULT_TEMPERATURE, 
    DEFAULT_MAX_TOKENS,
    is_multimodal_model
)

logger = logging.getLogger(__name__)

# Initialize OpenAI client - will be set when first API call is made
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """
    Get or initialize the OpenAI client.
    
    Returns:
        Configured OpenAI client instance
        
    Raises:
        ValueError: If API key is not configured properly
    """
    global _openai_client
    
    if _openai_client is None:
        try:
            api_key = get_openai_api_key()
            _openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    return _openai_client


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 for OpenAI API.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded image string
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If file cannot be encoded
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
        # Detect image format from file extension
        image_format = image_path.suffix.lower().lstrip('.')
        if image_format in ['jpg', 'jpeg']:
            image_format = 'jpeg'
        elif image_format == 'png':
            image_format = 'png'
        else:
            # Default to png for unknown formats
            image_format = 'png'
            
        return f"data:image/{image_format};base64,{base64_image}"
        
    except Exception as e:
        raise ValueError(f"Failed to encode image {image_path}: {e}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError))
)
def generate_caption_with_openai(
    image_path: str, 
    ocr_text: Optional[str] = None, 
    visual_type: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> str:
    """
    Use GPT-5 (or fallback) multimodal endpoint to describe an image.
    
    Fallback to GPT-4o if GPT-5 not accessible.
    Attach OCR text and type hints in prompt for better accuracy.
    
    Args:
        image_path: Path to the image file
        ocr_text: Optional OCR text extracted from the image
        visual_type: Type of visual (figure, table, equation, etc.)
        model: Specific model to use (if None, uses configured default)
        temperature: Sampling temperature for generation
        max_tokens: Maximum tokens in response
        
    Returns:
        Generated caption text
        
    Raises:
        Exception: If all retry attempts fail
    """
    if model is None:
        model = get_available_model()
    
    logger.info(f"Generating caption for {image_path} using model {model}")
    
    # Verify model supports multimodal
    if not is_multimodal_model(model):
        logger.warning(f"Model {model} may not support vision - attempting anyway")
    
    # Build system prompt
    system_prompt = (
        "You are a concise image captioning assistant for academic documents. "
        "Given an image and optional OCR text, describe the content in 1-3 sentences. "
        "Focus on semantic meaning (e.g., diagram steps, chart axes, table purpose). "
        "Be descriptive but concise, suitable for academic evaluation."
    )
    
    # Build user prompt with context
    context_parts = []
    if visual_type:
        context_parts.append(f"Type: {visual_type}")
    if ocr_text and ocr_text.strip():
        # Truncate very long OCR text
        ocr_preview = ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text
        context_parts.append(f"OCR text: {ocr_preview}")
    else:
        context_parts.append("OCR text: (none)")
    
    context_str = "\\n".join(context_parts)
    user_prompt = f"{context_str}\\n\\nProvide a descriptive caption for this image."
    
    try:
        # Encode image for API
        base64_image = encode_image_to_base64(image_path)
        
        # Get OpenAI client
        client = get_openai_client()
        
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": base64_image}}
                    ]
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Extract caption from response
        caption = response.choices[0].message.content.strip()
        
        if not caption:
            logger.warning(f"Empty caption received from API for {image_path}")
            return fallback_caption_from_ocr(ocr_text, visual_type)
        
        logger.info(f"Successfully generated caption for {image_path}: {caption[:50]}...")
        return caption
        
    except Exception as e:
        logger.warning(f"OpenAI API captioning failed for {image_path}: {e}")
        # Return fallback caption
        return fallback_caption_from_ocr(ocr_text, visual_type)


def fallback_caption_from_ocr(ocr_text: Optional[str], visual_type: Optional[str]) -> str:
    """
    Generate a fallback caption when the model or image upload fails.
    
    Args:
        ocr_text: OCR text extracted from the image
        visual_type: Type of visual content
        
    Returns:
        Fallback caption text
    """
    base_type = visual_type or "figure"
    
    if ocr_text and ocr_text.strip():
        # Create caption from OCR text
        short_text = (ocr_text[:150] + "...") if len(ocr_text) > 150 else ocr_text
        return f"A {base_type} containing text: {short_text}"
    
    # Generic fallback based on type
    type_descriptions = {
        "table": "A table with structured data related to the assignment",
        "equation": "A mathematical equation or formula",
        "chart": "A chart or graph showing data relationships", 
        "diagram": "A diagram illustrating concepts or processes",
        "figure": "A figure related to the assignment topic"
    }
    
    description = type_descriptions.get(base_type, f"A {base_type} related to the assignment topic")
    return description


def batch_generate_captions(
    image_paths: list[str],
    ocr_texts: list[Optional[str]] = None,
    visual_types: list[Optional[str]] = None
) -> list[str]:
    """
    Generate captions for multiple images.
    
    Note: This processes images sequentially. For true batch processing,
    the OpenAI API would need to support batch multimodal requests.
    
    Args:
        image_paths: List of paths to image files
        ocr_texts: List of OCR texts (same length as image_paths)
        visual_types: List of visual types (same length as image_paths)
        
    Returns:
        List of generated captions
    """
    if ocr_texts is None:
        ocr_texts = [None] * len(image_paths)
    if visual_types is None:
        visual_types = [None] * len(image_paths)
    
    if len(image_paths) != len(ocr_texts) or len(image_paths) != len(visual_types):
        raise ValueError("All input lists must have the same length")
    
    captions = []
    for i, image_path in enumerate(image_paths):
        try:
            caption = generate_caption_with_openai(
                image_path=image_path,
                ocr_text=ocr_texts[i],
                visual_type=visual_types[i]
            )
            captions.append(caption)
        except Exception as e:
            logger.error(f"Failed to caption image {image_path}: {e}")
            # Add fallback caption
            fallback = fallback_caption_from_ocr(ocr_texts[i], visual_types[i])
            captions.append(fallback)
    
    return captions


def test_api_connection() -> bool:
    """
    Test if the OpenAI API is accessible with current configuration.
    
    Returns:
        True if API is accessible, False otherwise
    """
    try:
        client = get_openai_client()
        
        # Make a simple API call to test connectivity
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a lightweight model for testing
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        logger.info("OpenAI API connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"OpenAI API connection test failed: {e}")
        return False