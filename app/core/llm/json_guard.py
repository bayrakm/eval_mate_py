"""
JSON Guard - Phase 9

Strict JSON parsing with one repair attempt for LLM outputs.
"""

import json
import logging

logger = logging.getLogger(__name__)


def parse_strict_json(s: str) -> dict:
    """Parse JSON string with basic preprocessing."""
    s = s.strip()
    if s.startswith("```"):
        # strip fences if the model used them
        s = s.strip("`")
        lines = s.split("\n")
        if len(lines) > 1:
            s = "\n".join(lines[1:])  # Skip first line (language hint)
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    return json.loads(s)


def try_repair_json(s: str) -> dict:
    """Attempt naive repairs: trim prefix/suffix, remove trailing commas, etc."""
    logger.warning(f"Attempting to repair JSON: {s[:200]}...")
    
    s2 = s.strip()
    
    # Remove common trailing comma issues
    if s2.endswith(",}"):
        s2 = s2.replace(",}", "}")
    if s2.endswith(",]"):
        s2 = s2.replace(",]", "]")
        
    # Try to find JSON boundaries if there's extra text
    start = s2.find("{")
    end = s2.rfind("}")
    if start != -1 and end != -1 and end > start:
        s2 = s2[start:end+1]
    
    return parse_strict_json(s2)