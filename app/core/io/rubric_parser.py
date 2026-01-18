"""
Deprecated rubric parser (legacy shim).

This module now delegates rubric parsing to the ADE-based extractor to keep
older call sites working while avoiding duplicate parsing logic.
"""

from dataclasses import dataclass
from typing import Optional, List

from app.core.models.schemas import CanonicalDoc, RubricItem
from app.core.io.rubric_extractor import extract_rubric_structured, rubric_items_from_extraction


@dataclass
class ParseConfig:
    """Legacy config retained for backwards compatibility (unused)."""
    prefer_tables: bool = True


def parse_rubric_to_items(canonical: CanonicalDoc, config: Optional[ParseConfig] = None) -> List[RubricItem]:
    """
    Legacy entry point that now delegates to ADE-based rubric extraction.
    """
    if canonical.source_files:
        extraction = extract_rubric_structured(canonical.source_files[0])
        return rubric_items_from_extraction(extraction)
    return []
