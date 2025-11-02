"""
Caption Detection Heuristics

This module provides heuristic methods for inferring captions from nearby text,
alt text, and other contextual information in documents.

Supports intelligent caption detection for visual content processing.
"""

import logging
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CaptionCandidate:
    """
    Represents a potential caption with confidence score.
    
    Attributes:
        text: The caption text
        confidence: Confidence score (0.0 to 1.0)
        source: Source of the caption (e.g., 'alt_text', 'nearby_text', 'pattern_match')
        distance: Distance metric (for nearby text captions)
    """
    text: str
    confidence: float
    source: str
    distance: Optional[float] = None


def infer_caption_for_pdf(pdf_path: str, page: int, image_bbox_norm: Optional[Tuple[float, float, float, float]]) -> Optional[str]:
    """
    Heuristic caption detection for PDF images.
    
    Uses pdfplumber text lines on the page to find the nearest line below the bbox
    that matches figure/table patterns: 'Figure', 'Fig.', 'Table'.
    
    Args:
        pdf_path: Path to PDF file
        page: 0-based page number
        image_bbox_norm: Normalized bounding box (x1, y1, x2, y2) in range [0, 1], or None
        
    Returns:
        Caption text if found within distance threshold, None otherwise
    """
    try:
        from app.core.io.pdf_utils import extract_pdf_text_blocks_for_captions, get_pdf_page_dimensions
        
        # Get text blocks with position information
        text_blocks = extract_pdf_text_blocks_for_captions(pdf_path, page)
        
        if not text_blocks:
            return None
        
        # If no bbox available, just look for caption patterns in all text
        if not image_bbox_norm:
            return find_caption_patterns_in_text_blocks(text_blocks)
        
        # Get page dimensions for coordinate conversion
        page_dims = get_pdf_page_dimensions(pdf_path, page)
        if not page_dims:
            return find_caption_patterns_in_text_blocks(text_blocks)
        
        page_width, page_height = page_dims
        
        # Convert normalized bbox to absolute coordinates
        x1_norm, y1_norm, x2_norm, y2_norm = image_bbox_norm
        image_x1 = x1_norm * page_width
        image_y1 = y1_norm * page_height
        image_x2 = x2_norm * page_width
        image_y2 = y2_norm * page_height
        
        # Find caption candidates near the image
        candidates = []
        
        for block in text_blocks:
            text = block['text'].strip()
            if not text:
                continue
            
            block_bbox = block['bbox']
            block_x1, block_y1, block_x2, block_y2 = block_bbox
            
            # Calculate distance from image to text block
            distance = calculate_text_image_distance(
                (image_x1, image_y1, image_x2, image_y2),
                (block_x1, block_y1, block_x2, block_y2)
            )
            
            # Check if text matches caption patterns
            caption_match = extract_caption_from_text(text)
            if caption_match:
                confidence = calculate_caption_confidence(caption_match, distance, block.get('fontsize', 12))
                
                candidate = CaptionCandidate(
                    text=caption_match,
                    confidence=confidence,
                    source='nearby_text',
                    distance=distance
                )
                candidates.append(candidate)
        
        # Return the best candidate
        if candidates:
            best_candidate = max(candidates, key=lambda c: c.confidence)
            if best_candidate.confidence > 0.3:  # Minimum confidence threshold
                return best_candidate.text
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to infer caption for PDF {pdf_path}, page {page}: {e}")
        return None


def infer_caption_for_docx(docx_path: str, image_alt_text: Optional[str], paragraph_index: Optional[int] = None) -> Optional[str]:
    """
    Heuristic caption detection for DOCX images.
    
    Prefers image alt text if present; otherwise, inspects paragraph immediately after
    the image run for 'Figure/Table' prefixes.
    
    Args:
        docx_path: Path to DOCX file
        image_alt_text: Alt text from the image, if available
        paragraph_index: Index of paragraph containing the image
        
    Returns:
        Caption text if found, None otherwise
    """
    # Prefer alt text if available and meaningful
    if image_alt_text and len(image_alt_text.strip()) > 3:
        # Clean up alt text
        cleaned_alt = image_alt_text.strip()
        if not is_generic_alt_text(cleaned_alt):
            return cleaned_alt
    
    # If no useful alt text, look for captions in nearby paragraphs
    if paragraph_index is not None:
        try:
            from app.core.io.docx_utils import extract_docx_paragraphs_with_context, detect_figure_captions_in_docx
            
            paragraphs = extract_docx_paragraphs_with_context(docx_path)
            captions = detect_figure_captions_in_docx(paragraphs)
            
            # Look for captions near this paragraph
            for caption_idx, caption_text in captions:
                # Check if caption is close to our image paragraph
                distance = abs(caption_idx - paragraph_index)
                if distance <= 2:  # Within 2 paragraphs
                    return caption_text
                    
        except Exception as e:
            logger.warning(f"Failed to search for nearby captions in DOCX {docx_path}: {e}")
    
    return None


def find_caption_patterns_in_text_blocks(text_blocks: List[dict]) -> Optional[str]:
    """
    Search for caption patterns in a list of text blocks.
    
    Args:
        text_blocks: List of text block dicts with 'text' key
        
    Returns:
        First caption found, or None
    """
    for block in text_blocks:
        text = block.get('text', '').strip()
        if text:
            caption = extract_caption_from_text(text)
            if caption:
                return caption
    
    return None


def extract_caption_from_text(text: str) -> Optional[str]:
    """
    Extract caption text using pattern matching.
    
    Args:
        text: Text to analyze
        
    Returns:
        Caption text if pattern matches, None otherwise
    """
    # Caption patterns with capturing groups
    patterns = [
        r'^Figure\s+(\d+)[:\.\-]\s*(.+)$',
        r'^Fig\.\s*(\d+)[:\.\-]\s*(.+)$',
        r'^Table\s+(\d+)[:\.\-]\s*(.+)$',
        r'^Image\s+(\d+)[:\.\-]\s*(.+)$',
        r'^Diagram\s+(\d+)[:\.\-]\s*(.+)$',
        r'^Chart\s+(\d+)[:\.\-]\s*(.+)$',
        r'^Graph\s+(\d+)[:\.\-]\s*(.+)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        if match:
            # Return the full text as caption
            return text.strip()
    
    # Also check for standalone figure/table references
    standalone_patterns = [
        r'^(Figure\s+\d+)$',
        r'^(Fig\.\s*\d+)$',
        r'^(Table\s+\d+)$',
    ]
    
    for pattern in standalone_patterns:
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def calculate_text_image_distance(image_bbox: Tuple[float, float, float, float], text_bbox: Tuple[float, float, float, float]) -> float:
    """
    Calculate distance between image and text bounding boxes.
    
    Prioritizes text below the image (typical caption placement).
    
    Args:
        image_bbox: Image bounding box (x1, y1, x2, y2)
        text_bbox: Text bounding box (x1, y1, x2, y2)
        
    Returns:
        Distance score (lower is closer/better)
    """
    img_x1, img_y1, img_x2, img_y2 = image_bbox
    text_x1, text_y1, text_x2, text_y2 = text_bbox
    
    # Calculate center points
    img_center_x = (img_x1 + img_x2) / 2
    img_center_y = (img_y1 + img_y2) / 2
    text_center_x = (text_x1 + text_x2) / 2
    text_center_y = (text_y1 + text_y2) / 2
    
    # Euclidean distance
    euclidean_dist = ((img_center_x - text_center_x) ** 2 + (img_center_y - text_center_y) ** 2) ** 0.5
    
    # Bonus for text below image (typical caption placement)
    if text_center_y > img_y2:  # Text is below image
        euclidean_dist *= 0.7  # Reduce distance (prefer captions below)
    elif text_center_y < img_y1:  # Text is above image
        euclidean_dist *= 1.3  # Increase distance (less likely to be caption)
    
    return euclidean_dist


def calculate_caption_confidence(caption_text: str, distance: float, font_size: float = 12) -> float:
    """
    Calculate confidence score for a caption candidate.
    
    Args:
        caption_text: The caption text
        distance: Distance from image to text
        font_size: Font size of the text
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    confidence = 1.0
    
    # Distance penalty (closer is better)
    max_distance = 200  # Maximum reasonable distance in points
    distance_factor = max(0, 1 - (distance / max_distance))
    confidence *= distance_factor
    
    # Text quality bonus
    if len(caption_text) > 20:  # Detailed captions are better
        confidence *= 1.1
    elif len(caption_text) < 10:  # Very short captions are suspicious
        confidence *= 0.8
    
    # Font size consideration (captions are often smaller)
    if 8 <= font_size <= 11:  # Typical caption font size
        confidence *= 1.1
    elif font_size > 14:  # Large text less likely to be caption
        confidence *= 0.9
    
    # Pattern strength bonus
    strong_patterns = ['Figure', 'Table', 'Diagram']
    for pattern in strong_patterns:
        if pattern in caption_text:
            confidence *= 1.2
            break
    
    return min(confidence, 1.0)  # Cap at 1.0


def is_generic_alt_text(alt_text: str) -> bool:
    """
    Check if alt text is generic/unhelpful.
    
    Args:
        alt_text: Alt text to evaluate
        
    Returns:
        True if alt text appears to be generic
    """
    generic_phrases = [
        'image', 'picture', 'photo', 'figure', 'untitled', 'image1', 'image2',
        'img', 'pic', 'screenshot', 'unknown', 'default', 'placeholder'
    ]
    
    alt_lower = alt_text.lower().strip()
    
    # Check for exact matches or very short text
    if len(alt_lower) <= 3:
        return True
    
    for phrase in generic_phrases:
        if phrase == alt_lower or alt_lower.startswith(phrase):
            return True
    
    # Check for patterns like "Image1", "Figure_1", etc.
    if re.match(r'^(image|figure|pic|img)\d*$', alt_lower):
        return True
    
    return False


def clean_caption_text(text: str) -> str:
    """
    Clean and normalize caption text.
    
    Args:
        text: Raw caption text
        
    Returns:
        Cleaned caption text
    """
    # Remove extra whitespace
    cleaned = ' '.join(text.split())
    
    # Remove trailing punctuation if it's just a period
    if cleaned.endswith('.') and not cleaned.endswith('..'):
        cleaned = cleaned[:-1]
    
    # Capitalize first letter if needed
    if cleaned and not cleaned[0].isupper():
        cleaned = cleaned[0].upper() + cleaned[1:]
    
    return cleaned


def extract_visual_type_from_caption(caption: str) -> Optional[str]:
    """
    Infer visual type from caption text.
    
    Args:
        caption: Caption text
        
    Returns:
        Visual type string if determinable, None otherwise
    """
    caption_lower = caption.lower()
    
    # Table indicators
    if any(word in caption_lower for word in ['table', 'matrix', 'data', 'results']):
        return 'table'
    
    # Chart indicators
    if any(word in caption_lower for word in ['chart', 'graph', 'plot', 'axis', 'bar', 'line']):
        return 'chart'
    
    # Diagram indicators
    if any(word in caption_lower for word in ['diagram', 'flow', 'workflow', 'process', 'schema']):
        return 'diagram'
    
    # Map indicators
    if any(word in caption_lower for word in ['map', 'location', 'geography', 'region']):
        return 'map'
    
    # Equation indicators
    if any(word in caption_lower for word in ['equation', 'formula', 'expression', 'calculation']):
        return 'equation'
    
    # Default to figure
    return 'figure'