"""
Rubric extraction using LandingAI Agentic Document Extraction (ADE).

Parses rubric documents into a structured JSON format and converts
the extracted grading criteria into RubricItem objects for evaluation.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from landingai_ade import LandingAIADE

from app.core.models.schemas import RubricItem, RubricCriterion
from app.core.models.ids import new_rubric_item_id
from app.core.io.text_utils import parse_inline_weight


DEFAULT_PARSE_MODEL = "dpt-2-latest"
DEFAULT_EXTRACT_MODEL = "extract-latest"


def build_rubric_schema() -> Dict[str, Any]:
    """Return the ADE JSON schema for rubric extraction."""
    return {
        "type": "object",
        "title": "Rubric Extraction Schema",
        "properties": {
            "organisation": {
                "type": "string",
                "description": "Organisation or university name shown on the rubric document."
            },
            "course": {
                "type": "string",
                "description": "Course or module name/code (e.g., COS4015-B)."
            },
            "grading_policy": {
                "type": "string",
                "description": "Any narrative grading policy or notes included in the rubric."
            },
            "grading": {
                "type": "array",
                "description": "List of criteria (and sub-criteria) with weights and scoring bands.",
                "items": {
                    "type": "object",
                    "properties": {
                        "criteria": {
                            "type": "string",
                            "description": "Criterion title. If sub-criteria exist, use 'criteria - sub criteria'."
                        },
                        "weight": {
                            "type": "string",
                            "description": "Weight for the criterion or sub-criterion (e.g., 10%, 0.1, 5 pts)."
                        },
                        "scoring_bands": {
                            "type": "array",
                            "description": "Ordered scoring bands with descriptions (band 1 to band N).",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "band": {
                                        "type": "string",
                                        "description": "Band label (e.g., 1, 2, 3, 4 or Poor/Good/Excellent)."
                                    },
                                    "band_desc": {
                                        "type": "string",
                                        "description": "Description for the band."
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


def extract_rubric_structured(
    file_path: str,
    parse_model: str = DEFAULT_PARSE_MODEL,
    extract_model: str = DEFAULT_EXTRACT_MODEL
) -> Dict[str, Any]:
    """
    Parse and extract rubric content using LandingAI ADE.

    Returns a normalized rubric dictionary according to build_rubric_schema().
    """
    client = LandingAIADE()
    document_path = Path(file_path)

    parse_result = client.parse(document=document_path, model=parse_model)
    schema_json = json.dumps(build_rubric_schema())

    extract_result = client.extract(
        schema=schema_json,
        markdown=parse_result.markdown,
        model=extract_model
    )

    return normalize_extraction(extract_result.extraction or {})


def normalize_extraction(extraction: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize extraction payload to ensure consistent keys and types."""
    organisation = _normalize_text(extraction.get("organisation", ""))
    course = _normalize_text(extraction.get("course", ""))
    grading_policy = _normalize_text(extraction.get("grading_policy", ""))

    grading = extraction.get("grading") or []
    if not isinstance(grading, list):
        grading = []

    normalized_grading = []
    for item in grading:
        if not isinstance(item, dict):
            continue
        criteria = _normalize_text(item.get("criteria", ""))
        weight = _normalize_text(item.get("weight", ""))

        scoring_bands = item.get("scoring_bands") or []
        if not isinstance(scoring_bands, list):
            scoring_bands = []

        normalized_bands = []
        for band in scoring_bands:
            if not isinstance(band, dict):
                continue
            band_label = _normalize_text(band.get("band", ""))
            band_desc = _normalize_text(band.get("band_desc", ""))
            if band_label or band_desc:
                normalized_bands.append({
                    "band": band_label,
                    "band_desc": band_desc
                })

        normalized_grading.append({
            "criteria": criteria,
            "weight": weight,
            "scoring_bands": normalized_bands
        })

    return {
        "organisation": organisation,
        "course": course,
        "grading_policy": grading_policy,
        "grading": normalized_grading
    }


def rubric_items_from_extraction(extraction: Dict[str, Any]) -> List[RubricItem]:
    """Convert extracted rubric grading items into RubricItem objects."""
    items: List[RubricItem] = []
    grading = extraction.get("grading") or []
    if not isinstance(grading, list):
        return items

    for entry in grading:
        if not isinstance(entry, dict):
            continue
        title = _normalize_text(entry.get("criteria", "")) or "Untitled Criterion"
        weight = _parse_weight(entry.get("weight"))
        band_descs = _band_descriptions(entry.get("scoring_bands"))
        description = " | ".join([d for d in band_descs if d]) or "Evaluate this criterion."

        items.append(RubricItem(
            id=new_rubric_item_id(),
            title=title,
            description=description,
            weight=weight,
            criterion=RubricCriterion.CONTENT
        ))

    return items


def save_rubric_json(
    extraction: Dict[str, Any],
    output_dir: str = "data/rubrics_extracted",
    default_name: Optional[str] = None
) -> Path:
    """Save extracted rubric JSON to a timestamped file and return the path."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    org = _safe_slug(extraction.get("organisation") or "")
    course = _safe_slug(extraction.get("course") or "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if default_name:
        filename = f"{_safe_slug(default_name)}_{timestamp}.json"
    else:
        base = "_".join([part for part in [org, course] if part]) or "rubric"
        filename = f"{base}_{timestamp}.json"

    path = output_path / filename
    path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")
    return path


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip()


def _safe_slug(value: str) -> str:
    value = _normalize_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "unknown"


def _parse_weight(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        if value > 1:
            return float(value) / 100.0 if value <= 100 else 0.0
        return float(value)

    text = _normalize_text(str(value))
    if not text:
        return 0.0

    parsed, _ = parse_inline_weight(text)
    if parsed is not None:
        if parsed > 1 and parsed <= 100:
            return parsed / 100.0
        return float(parsed)

    digits = re.findall(r"\d+(?:\.\d+)?", text)
    if digits:
        num = float(digits[0])
        return num / 100.0 if num > 1 and num <= 100 else num
    return 0.0


def _band_descriptions(bands: Any) -> List[str]:
    if not isinstance(bands, list):
        return []

    def band_key(band: Dict[str, Any]) -> Any:
        label = _normalize_text(band.get("band", ""))
        if label.isdigit():
            return int(label)
        return label

    if all(_normalize_text(b.get("band", "")).isdigit() for b in bands if isinstance(b, dict)):
        ordered = sorted(bands, key=band_key)
    else:
        ordered = bands

    descriptions = []
    for band in ordered:
        if not isinstance(band, dict):
            continue
        desc = _normalize_text(band.get("band_desc", ""))
        if desc:
            descriptions.append(desc)
    return descriptions
