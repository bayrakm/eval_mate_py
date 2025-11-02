"""
Rubric structuring engine for intelligent evaluation criteria parsing.

Converts CanonicalDoc (from document ingestion) into normalized Rubric.items list.
Handles rubrics authored as bullet/numbered lists and tables with weight normalization.
"""

import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from app.core.models.schemas import CanonicalDoc, RubricItem, RubricCriterion
from app.core.models.ids import new_rubric_item_id
from app.core.io.table_extraction import extract_tables_from_canonical, TableFrame
from app.core.io.text_utils import (
    detect_bulleted_items, 
    detect_numbered_items,
    split_heading_and_body,
    parse_inline_weight,
    clean_text
)

logger = logging.getLogger(__name__)


# Default keyword mapping for criterion classification
DEFAULT_CRITERION_KEYWORDS = {
    "content": ["content", "relevance", "coverage", "understanding", "insight", "depth"],
    "accuracy": ["accuracy", "correctness", "precision", "validity", "factual", "correct"],
    "structure": ["structure", "organization", "coherence", "flow", "formatting", "layout", "format"],
    "visuals": ["diagram", "figure", "chart", "table", "visual", "graph", "map", "image"],
    "citations": ["citation", "reference", "sources", "apa", "mla", "harvard", "bibliography", "cite"],
    "originality": ["originality", "novelty", "creativity", "creative", "plagiarism", "authenticity", "original", "innovative"]
}


@dataclass
class ParseConfig:
    """Configuration for rubric parsing behavior."""
    criterion_keywords: Optional[Dict[str, List[str]]] = None
    default_criterion: str = "content"
    weight_tolerance: float = 0.01  # for ~1.0 sum check
    normalize_missing_weights: bool = True  # distribute equally if missing
    prefer_tables: bool = True  # if both table and bullets detected, prefer table


def parse_rubric_to_items(canonical: CanonicalDoc, config: Optional[ParseConfig] = None) -> List[RubricItem]:
    """
    Main entry point. Given a CanonicalDoc of a rubric, return a list of RubricItem.
    
    Steps:
      1) Attempt table extraction (if enabled).
      2) If no usable table, attempt bullets/numbered-list parsing from text blocks.
      3) Map fields: title, description, weight, criterion.
      4) Normalize/validate weights; infer defaults if missing.
      5) If nothing found, return a single default item with weight 1.0.
    
    Args:
        canonical: CanonicalDoc containing rubric content
        config: Optional ParseConfig for customization
        
    Returns:
        List of RubricItem objects
    """
    if config is None:
        config = ParseConfig()
    
    if config.criterion_keywords is None:
        config.criterion_keywords = DEFAULT_CRITERION_KEYWORDS
    
    logger.info(f"Starting rubric parsing for document with {len(canonical.blocks)} blocks")
    
    items = []
    
    # Strategy 1: Table extraction (if preferred)
    if config.prefer_tables:
        logger.info("Attempting table-based parsing...")
        items = _parse_from_tables(canonical, config)
        
        if items:
            logger.info(f"Successfully parsed {len(items)} items from tables")
            return _finalize_items(items, config)
    
    # Strategy 2: List-based parsing (bullets/numbered)
    logger.info("Attempting list-based parsing...")
    items = _parse_from_lists(canonical, config)
    
    if items:
        logger.info(f"Successfully parsed {len(items)} items from lists")
        return _finalize_items(items, config)
    
    # Strategy 3: Table parsing as fallback (if not already tried)
    if not config.prefer_tables:
        logger.info("Attempting table-based parsing as fallback...")
        items = _parse_from_tables(canonical, config)
        
        if items:
            logger.info(f"Successfully parsed {len(items)} items from tables (fallback)")
            return _finalize_items(items, config)
    
    # Strategy 4: Default fallback
    logger.warning("No structured content detected, creating default fallback item")
    return _create_fallback_item(canonical, config)


def _parse_from_tables(canonical: CanonicalDoc, config: ParseConfig) -> List[RubricItem]:
    """Parse rubric items from table structures."""
    tables = extract_tables_from_canonical(canonical)
    
    if not tables:
        logger.debug("No tables found in canonical document")
        return []
    
    all_items_data = []
    all_raw_weights = []
    
    for table_idx, table in enumerate(tables):
        logger.debug(f"Processing table {table_idx + 1} with {len(table.rows)} rows")
        
        if not table.rows:
            continue
            
        # Map table columns to our fields
        column_mapping = _map_table_columns(table.headers)
        logger.debug(f"Column mapping: {column_mapping}")
        
        # Process each row
        for row_idx, row in enumerate(table.rows):
            try:
                item_data, raw_weight = _parse_table_row(row, column_mapping, config)
                if item_data:
                    all_items_data.append(item_data)
                    all_raw_weights.append(raw_weight)
                    logger.debug(f"Parsed item from row {row_idx + 1}: {item_data['title']}")
            except Exception as e:
                logger.warning(f"Error parsing table row {row_idx + 1}: {e}")
                continue
    
    if not all_items_data:
        return []
    
    # Normalize weights
    normalized_weights = _normalize_weights(all_raw_weights, config)
    
    # Create final RubricItem objects
    final_items = []
    for i, item_data in enumerate(all_items_data):
        try:
            item = RubricItem(
                id=new_rubric_item_id(),
                title=item_data['title'],
                description=item_data['description'],
                weight=normalized_weights[i],
                criterion=item_data['criterion']
            )
            final_items.append(item)
        except Exception as e:
            logger.error(f"Error creating RubricItem for '{item_data['title']}': {e}")
            continue
    
    return final_items


def _parse_from_lists(canonical: CanonicalDoc, config: ParseConfig) -> List[RubricItem]:
    """Parse rubric items from bullet/numbered lists."""
    items = []
    
    # Combine all text blocks
    full_text = ""
    for block in canonical.blocks:
        if block.kind == "text" and block.text:
            full_text += block.text + "\n"
    
    if not full_text.strip():
        logger.debug("No text content found in canonical document")
        return []
    
    logger.debug(f"Processing {len(full_text)} characters of text content")
    
    # Try both bullet points and numbered lists, prefer the one with more items
    bullet_items = detect_bulleted_items(full_text)
    numbered_items = detect_numbered_items(full_text)
    
    # Prefer numbered lists if they have more items, or if bullets have <= 1 item
    if len(numbered_items) > len(bullet_items) or (len(numbered_items) >= 1 and len(bullet_items) <= 1):
        if len(numbered_items) >= 1:
            logger.info(f"Detected {len(numbered_items)} numbered items")
            return _parse_list_items(numbered_items, config)
    
    # Otherwise use bullets if available
    if len(bullet_items) >= 1:
        logger.info(f"Detected {len(bullet_items)} bullet items")
        return _parse_list_items(bullet_items, config)
    
    logger.debug("No list structure detected in text content")
    return []


def _normalize_weights(raw_weights: List[float], config: ParseConfig) -> List[float]:
    """Normalize a list of raw weights to sum to 1.0."""
    if not raw_weights:
        return []
    
    # Check if we have any non-zero weights
    has_weights = any(w > 0 for w in raw_weights)
    
    if not has_weights and config.normalize_missing_weights:
        # Distribute equally
        equal_weight = 1.0 / len(raw_weights)
        logger.debug(f"No weights found, distributing equally: {equal_weight:.3f} each")
        return [equal_weight] * len(raw_weights)
    
    elif has_weights:
        total_weight = sum(raw_weights)
        
        if total_weight == 0:
            # All weights are 0, distribute equally
            equal_weight = 1.0 / len(raw_weights)
            return [equal_weight] * len(raw_weights)
        else:
            # Normalize to sum to 1.0
            normalized = [w / total_weight for w in raw_weights]
            logger.debug(f"Normalized weights from sum {total_weight:.3f} to 1.0")
            return normalized
    
    # Fallback: equal distribution
    equal_weight = 1.0 / len(raw_weights)
    return [equal_weight] * len(raw_weights)


def _parse_list_items(list_items: List[str], config: ParseConfig) -> List[RubricItem]:
    """Convert list items to RubricItem objects."""
    items = []
    raw_weights = []
    
    # First pass: collect all items and weights
    for item_text in list_items:
        try:
            # Parse weight from text
            weight, cleaned_text = parse_inline_weight(item_text)
            
            # Split into title and description
            title, description = split_heading_and_body(cleaned_text)
            
            if not title:
                logger.warning(f"No title found for item: {item_text[:50]}...")
                continue
            
            # Map criterion
            criterion = _map_criterion(title + " " + description, config)
            
            # Store raw weight for normalization
            raw_weights.append(weight or 0.0)
            
            # Create item with temporary weight (will be normalized)
            item_data = {
                'title': title,
                'description': description or "Evaluate this aspect of the submission.",
                'criterion': criterion,
                'raw_weight': weight or 0.0
            }
            
            items.append(item_data)
            logger.debug(f"Parsed item: {title} (raw weight: {weight}, criterion: {criterion.value})")
            
        except Exception as e:
            logger.warning(f"Error parsing list item '{item_text[:50]}...': {e}")
            continue
    
    if not items:
        return []
    
    # Normalize weights
    normalized_weights = _normalize_weights(raw_weights, config)
    
    # Create final RubricItem objects with normalized weights
    final_items = []
    for i, item_data in enumerate(items):
        try:
            item = RubricItem(
                id=new_rubric_item_id(),
                title=item_data['title'],
                description=item_data['description'],
                weight=normalized_weights[i],
                criterion=item_data['criterion']
            )
            final_items.append(item)
        except Exception as e:
            logger.error(f"Error creating RubricItem for '{item_data['title']}': {e}")
            continue
    
    return final_items


def _map_table_columns(headers: List[str]) -> Dict[str, int]:
    """Map table headers to field indices."""
    mapping = {}
    
    # Column synonym mappings
    column_synonyms = {
        'title': ['criterion', 'criteria', 'dimension', 'aspect', 'category', 'component'],
        'description': ['description', 'descriptor', 'details', 'standard', 'exemplar'],
        'weight': ['weight', '%', 'percent', 'percentage', 'points', 'marks', 'score', 'scoring', 'pts'],
        'criterion_type': ['criterion_type', 'dimension_type', 'category_type', 'aspect_type', 'type']
    }
    
    # Try to match headers to fields
    for field, synonyms in column_synonyms.items():
        for idx, header in enumerate(headers):
            header_lower = header.lower().strip()
            for synonym in synonyms:
                if synonym in header_lower:
                    if field not in mapping:  # Take first match
                        mapping[field] = idx
                        logger.debug(f"Mapped '{header}' -> {field}")
                        break
    
    # Fallback: infer by position if no headers matched or headers are empty
    if not mapping:
        # Use headers length if available, otherwise we'll rely on row length
        num_cols = len(headers) if headers else None
        
        # We'll apply positional mapping in _parse_table_row if needed
        if num_cols is not None and num_cols >= 2:
            mapping['title'] = 0
            mapping['description'] = 1
            
            if num_cols >= 3:
                mapping['weight'] = 2
                
            if num_cols >= 4:
                mapping['criterion_type'] = 3
                
            logger.debug(f"Applied positional mapping for {num_cols} columns")
        else:
            logger.debug("No headers provided, will use positional mapping based on row length")
    
    return mapping


def _parse_table_row(row: List[str], column_mapping: Dict[str, int], config: ParseConfig) -> Tuple[Optional[Dict], float]:
    """Parse a single table row into item data and raw weight."""
    if not row:
        return None, 0.0
    
    # If no column mapping, apply positional mapping based on row length
    if not column_mapping and len(row) >= 2:
        column_mapping = {'title': 0, 'description': 1}
        if len(row) >= 3:
            column_mapping['weight'] = 2
        if len(row) >= 4:
            column_mapping['criterion_type'] = 3
        logger.debug(f"Applied positional mapping for row with {len(row)} columns")
    
    # Extract fields based on mapping
    title = ""
    description = ""
    weight = 0.0
    criterion_hint = ""
    
    if 'title' in column_mapping and column_mapping['title'] < len(row):
        title = clean_text(row[column_mapping['title']])
    
    if 'description' in column_mapping and column_mapping['description'] < len(row):
        description = clean_text(row[column_mapping['description']])
    
    if 'weight' in column_mapping and column_mapping['weight'] < len(row):
        weight_text = row[column_mapping['weight']].strip()
        if weight_text:
            weight, _ = parse_inline_weight(weight_text + "%")  # Add % if missing
            if weight is None:
                weight = 0.0
    
    if 'criterion_type' in column_mapping and column_mapping['criterion_type'] < len(row):
        criterion_hint = clean_text(row[column_mapping['criterion_type']])
    
    # Validate required fields
    if not title:
        return None, 0.0
    
    # Map criterion
    criterion_text = title + " " + description + " " + criterion_hint
    criterion = _map_criterion(criterion_text, config)
    
    # Return item data and raw weight
    item_data = {
        'title': title,
        'description': description or "Evaluate this aspect of the submission.",
        'criterion': criterion
    }
    
    return item_data, weight


def _map_criterion(text: str, config: ParseConfig) -> RubricCriterion:
    """Map text content to a RubricCriterion enum value."""
    text_lower = text.lower()
    
    # Score each criterion based on keyword matches
    criterion_scores = {}
    
    for criterion_name, keywords in config.criterion_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 1
        criterion_scores[criterion_name] = score
    
    # Find the criterion with the highest score
    if criterion_scores:
        best_criterion = max(criterion_scores.items(), key=lambda x: x[1])
        if best_criterion[1] > 0:  # At least one keyword matched
            criterion_name = best_criterion[0]
            try:
                return RubricCriterion(criterion_name)
            except ValueError:
                pass  # Fall through to default
    
    # Default fallback
    try:
        return RubricCriterion(config.default_criterion)
    except ValueError:
        return RubricCriterion.CONTENT  # Ultimate fallback


def _finalize_items(items: List[RubricItem], config: ParseConfig) -> List[RubricItem]:
    """Normalize weights and finalize the item list."""
    if not items:
        return items
    
    logger.info(f"Finalizing {len(items)} rubric items")
    
    # Collect weights
    weights = [item.weight for item in items]
    has_weights = any(w > 0 for w in weights)
    
    if not has_weights and config.normalize_missing_weights:
        # Distribute equally
        equal_weight = 1.0 / len(items)
        logger.info(f"No weights found, distributing equally: {equal_weight:.3f} each")
        
        for item in items:
            item.weight = equal_weight
            
    elif has_weights:
        # Normalize existing weights
        total_weight = sum(weights)
        
        if total_weight == 0:
            # All weights are 0, distribute equally
            equal_weight = 1.0 / len(items)
            for item in items:
                item.weight = equal_weight
        else:
            # Check if weights look like points (> 1.0) or percentages > 1
            max_weight = max(weights)
            if max_weight > 1.0:
                logger.info(f"Detected points-based weights (max: {max_weight}), normalizing to fractions")
                
                # Normalize to sum to 1.0
                for item in items:
                    item.weight = item.weight / total_weight
            else:
                # Check if sum is close to 1.0
                if abs(total_weight - 1.0) > config.weight_tolerance:
                    logger.info(f"Weight sum {total_weight:.3f} != 1.0, normalizing")
                    
                    for item in items:
                        item.weight = item.weight / total_weight
    
    # Final validation
    final_sum = sum(item.weight for item in items)
    logger.info(f"Final weight sum: {final_sum:.3f}")
    
    # Ensure all items have non-empty descriptions
    for item in items:
        if not item.description:
            item.description = f"Evaluate the {item.title.lower()} aspect of the submission."
    
    return items


def _create_fallback_item(canonical: CanonicalDoc, config: ParseConfig) -> List[RubricItem]:
    """Create a single fallback item when no structure is detected."""
    # Use first text block for description, or generic text
    description = "Evaluate the submission holistically according to the provided rubric text."
    
    if canonical.blocks:
        for block in canonical.blocks:
            if block.kind == "text" and block.text and len(block.text.strip()) > 20:
                description = clean_text(block.text)[:200] + "..."
                break
    
    item = RubricItem(
        id=new_rubric_item_id(),
        title="Overall Quality",
        description=description,
        weight=1.0,
        criterion=_map_criterion("overall quality", config)
    )
    
    logger.info("Created fallback item for unstructured rubric")
    return [item]