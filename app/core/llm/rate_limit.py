"""
Rate Limiting - Phase 9

Backoff and retry helpers for OpenAI API calls.
"""

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai
import logging

logger = logging.getLogger(__name__)

# Retry decorator for LLM calls with exponential backoff
retry_llm = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=15),
    retry=retry_if_exception_type((
        openai.RateLimitError, 
        openai.APIError,
        openai.InternalServerError,
        openai.APITimeoutError
    ))
)


def log_retry_attempt(retry_state):
    """Log retry attempts for debugging."""
    logger.warning(f"Retrying LLM call, attempt {retry_state.attempt_number} after {retry_state.seconds_since_start:.1f}s")


# Enhanced retry decorator with logging
retry_llm_with_logging = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=15),
    retry=retry_if_exception_type((
        openai.RateLimitError, 
        openai.APIError,
        openai.InternalServerError,
        openai.APITimeoutError
    )),
    after=log_retry_attempt
)