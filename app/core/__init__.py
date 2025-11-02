"""
Core modules for EvalMate.

Contains the fundamental components for document processing, storage,
and LLM-based evaluation.
"""

# Import submodules to make them available
from . import io, models, store
try:
    from . import llm
except ImportError:
    # LLM module might not be fully available in all environments
    llm = None

__all__ = ["io", "models", "store", "llm"]