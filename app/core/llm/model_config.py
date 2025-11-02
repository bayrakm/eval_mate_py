"""
Model Configuration and Fallback Logic

This module defines configuration for OpenAI models with automatic fallback
logic for Phase 7 multimodal captioning.

Phase 7: Visual Captioning (Multimodal LLM Integration)
"""

import os
import logging
from pathlib import Path
from typing import Literal, List, Optional, Dict, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in project root
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        # override=True ensures .env file values take priority over system environment variables
        load_dotenv(env_path, override=True)
        print(f"[OK] Loaded environment variables from {env_path} (overriding system variables)")
    else:
        # Try loading from current directory
        load_dotenv(override=True)
        print("[INFO] No .env file found, using system environment variables")
except ImportError:
    print("[WARNING] python-dotenv not installed, using system environment variables only")

logger = logging.getLogger(__name__)

# Model type definitions
ModelName = Literal["gpt-5-multimodal", "gpt-5", "gpt-4o", "gpt-4o-mini"]

# Default model priority order - GPT-4o is currently most available for multimodal
DEFAULT_MODEL_PRIORITY: List[str] = ["gpt-4o", "gpt-4o-mini", "gpt-5-multimodal", "gpt-5"]

# Default API parameters
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 300
DEFAULT_TIMEOUT = 30

# Environment variable names
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_OPENAI_MODEL = "OPENAI_MODEL"


def get_available_model(preferred_list: List[str] = None) -> str:
    """
    Iterate through preferred_list and return the first accessible model.
    
    In practice, we assume all models exist and allow user override via env var.
    For production use, this could be enhanced to actually check model availability.
    
    Args:
        preferred_list: List of preferred model names in priority order
        
    Returns:
        Model name to use for API calls
        
    Examples:
        >>> get_available_model()
        'gpt-5-multimodal'
        >>> os.environ['OPENAI_MODEL'] = 'gpt-4o'
        >>> get_available_model()
        'gpt-4o'
    """
    if preferred_list is None:
        preferred_list = DEFAULT_MODEL_PRIORITY
    
    # Check for user override via environment variable
    env_model = os.getenv(ENV_OPENAI_MODEL)
    if env_model:
        logger.info(f"Using model from environment variable: {env_model}")
        return env_model
    
    # Return first model from priority list
    selected_model = preferred_list[0]
    logger.info(f"Using default priority model: {selected_model}")
    return selected_model


def get_openai_api_key() -> str:
    """
    Get OpenAI API key from environment variables.
    
    Returns:
        API key string
        
    Raises:
        ValueError: If API key is not found in environment
    """
    api_key = os.getenv(ENV_OPENAI_API_KEY)
    if not api_key:
        raise ValueError(
            f"""
[CRITICAL] OpenAI API key not found!

To use Phase 7 multimodal features, you need to set up your OpenAI API key:

1. Copy the example environment file:
   cp .env.example .env

2. Get your API key from: https://platform.openai.com/api-keys

3. Edit .env file and replace 'sk-your-openai-api-key-here' with your actual key:
   OPENAI_API_KEY=sk-your-actual-api-key-here

4. Restart the application

Current environment variable '{ENV_OPENAI_API_KEY}' is not set.
            """.strip()
        )
    
    # Validate API key format
    if not api_key.startswith('sk-'):
        raise ValueError(
            f"Invalid OpenAI API key format. API keys should start with 'sk-'. "
            f"Current value: {api_key[:10]}..."
        )
    
    return api_key


def get_model_config() -> dict:
    """
    Get complete model configuration for API calls.
    
    Returns:
        Dictionary with model configuration parameters
    """
    return {
        "model": get_available_model(),
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "timeout": DEFAULT_TIMEOUT,
    }


def is_multimodal_model(model_name: str) -> bool:
    """
    Check if a model supports multimodal (vision) capabilities.
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        True if model supports vision, False otherwise
    """
    multimodal_models = {"gpt-5-multimodal", "gpt-5", "gpt-4o", "gpt-4o-mini"}
    return model_name in multimodal_models


def validate_model_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate that the model configuration is valid.
    
    Args:
        config: Optional configuration dict to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    if config is None:
        # Validate current configuration
        try:
            # Check if API key is available
            get_openai_api_key()
            
            # Check if selected model is valid
            model = get_available_model()
            if model not in DEFAULT_MODEL_PRIORITY:
                logger.warning(f"Selected model {model} not in known model list")
            
            return True
            
        except Exception as e:
            logger.error(f"Model configuration validation failed: {e}")
            return False
    
    # Validate provided configuration
    required_fields = ["model"]
    for field in required_fields:
        if field not in config:
            return False
    
    # Validate model name
    valid_models = set(DEFAULT_MODEL_PRIORITY)
    if config["model"] not in valid_models:
        return False
    
    # Validate optional numeric fields
    if "temperature" in config:
        temp = config["temperature"]
        if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
            return False
    
    if "max_tokens" in config:
        tokens = config["max_tokens"]
        if not isinstance(tokens, int) or tokens <= 0:
            return False
    
    return True