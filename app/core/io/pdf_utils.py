"""
PDF Visual Extraction Utilities

This module provides PDF-specific utilities for extracting images and visual content
with bounding box information. Supports both PyMuPDF (preferred) and pdfplumber fallbacks.

Phase 6: Visual Extraction
"""

import logging
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Optional imports with graceful fallbacks
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.info("PyMuPDF not available, falling back to pdfplumber for PDF processing")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available, PDF processing will be limited")


@dataclass
class PdfImage:
    """
    Represents an extracted image from a PDF with metadata.
    
    Attributes:
        page: 0-based page number where image was found
        bbox: Bounding box in absolute pixel coordinates (x1, y1, x2, y2) or None
        bbox_norm: Normalized bounding box coordinates (0.0 to 1.0) or None
        image_bytes: Raw image bytes
        page_width: Width of the PDF page in points
        page_height: Height of the PDF page in points
        image_index: Index of image on the page (for naming)
    """
    page: int
    bbox: Optional[Tuple[float, float, float, float]]  # absolute pixels
    bbox_norm: Optional[Tuple[float, float, float, float]]  # normalized 0-1
    image_bytes: bytes
    page_width: float
    page_height: float
    image_index: int = 0


def pdf_page_count(path: str) -> int:
    """
    Get the number of pages in a PDF file.
    
    Args:
        path: Path to PDF file
        
    Returns:
        int: Number of pages, 0 if file cannot be read
    """
    try:
        if PYMUPDF_AVAILABLE:
            doc = fitz.open(path)
            count = len(doc)
            doc.close()
            return count
        elif PDFPLUMBER_AVAILABLE:
            with pdfplumber.open(path) as pdf:
                return len(pdf.pages)
        else:
            logger.error("No PDF library available")
            return 0
    except Exception as e:
        logger.error(f"Failed to get page count for {path}: {e}")
        return 0


def extract_pdf_images_with_bbox_pymupdf(path: str) -> List[PdfImage]:
    """
    Extract images from PDF using PyMuPDF with accurate bounding boxes.
    
    Args:
        path: Path to PDF file
        
    Returns:
        List of PdfImage objects with bbox information
    """
    images = []
    
    try:
        doc = fitz.open(path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image reference
                    xref = img[0]
                    
                    # Extract image data
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Try to get bounding box
                    bbox = None
                    bbox_norm = None
                    try:
                        # Find rectangles that reference this image
                        image_rects = page.get_image_rects(xref)
                        if image_rects:
                            # Use the first rectangle (most images have one placement)
                            rect = image_rects[0]
                            bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
                            
                            # Normalize bbox to 0-1 range
                            if page_width > 0 and page_height > 0:
                                bbox_norm = (
                                    rect.x0 / page_width,
                                    rect.y0 / page_height,
                                    rect.x1 / page_width,
                                    rect.y1 / page_height
                                )
                    except Exception as bbox_error:
                        logger.debug(f"Could not get bbox for image {img_index} on page {page_num}: {bbox_error}")
                    
                    pdf_image = PdfImage(
                        page=page_num,
                        bbox=bbox,
                        bbox_norm=bbox_norm,
                        image_bytes=image_bytes,
                        page_width=page_width,
                        page_height=page_height,
                        image_index=img_index
                    )
                    images.append(pdf_image)
                    
                except Exception as img_error:
                    logger.warning(f"Failed to extract image {img_index} from page {page_num}: {img_error}")
                    continue
        
        doc.close()
        
    except Exception as e:
        logger.error(f"Failed to extract images from PDF {path} using PyMuPDF: {e}")
    
    return images


def extract_pdf_images_with_bbox_pdfplumber(path: str) -> List[PdfImage]:
    """
    Extract images from PDF using pdfplumber (fallback method).
    
    Note: pdfplumber has limited image extraction capabilities compared to PyMuPDF.
    Bounding boxes may not always be accurate.
    
    Args:
        path: Path to PDF file
        
    Returns:
        List of PdfImage objects, possibly with None bbox values
    """
    images = []
    
    try:
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Get images on this page
                    page_images = page.images
                    
                    for img_index, img_info in enumerate(page_images):
                        try:
                            # Try to crop the image region
                            bbox_info = None
                            if 'x0' in img_info and 'y0' in img_info and 'x1' in img_info and 'y1' in img_info:
                                bbox_info = (img_info['x0'], img_info['y0'], img_info['x1'], img_info['y1'])
                                
                                # Crop the image from the page
                                cropped = page.crop(bbox_info)
                                page_image = cropped.to_image()
                                
                                # Convert to PIL Image
                                pil_image = page_image.original
                                
                                pdf_image = PdfImage(
                                    page=page_num,
                                    bbox=bbox_info,
                                    pil_image=pil_image,
                                    image_index=img_index
                                )
                                images.append(pdf_image)
                            
                        except Exception as img_error:
                            logger.warning(f"Failed to extract image {img_index} from page {page_num} using pdfplumber: {img_error}")
                            continue
                            
                except Exception as page_error:
                    logger.warning(f"Failed to process page {page_num}: {page_error}")
                    continue
                    
    except Exception as e:
        logger.error(f"Failed to extract images from PDF {path} using pdfplumber: {e}")
    
    return images


def extract_pdf_images_with_bbox(path: str) -> List[PdfImage]:
    """
    Extract embedded images from PDF with page index and pixel bbox if available.
    
    Uses PyMuPDF if available (preferred), falls back to pdfplumber.
    
    Args:
        path: Path to PDF file
        
    Returns:
        List of PdfImage objects with PIL images and metadata
    """
    if PYMUPDF_AVAILABLE:
        logger.debug(f"Extracting PDF images using PyMuPDF from {path}")
        return extract_pdf_images_with_bbox_pymupdf(path)
    elif PDFPLUMBER_AVAILABLE:
        logger.debug(f"Extracting PDF images using pdfplumber from {path}")
        return extract_pdf_images_with_bbox_pdfplumber(path)
    else:
        logger.error("No PDF processing library available for image extraction")
        return []


def normalize_bbox_to_page(bbox: Tuple[float, float, float, float], page_width: float, page_height: float) -> Tuple[float, float, float, float]:
    """
    Normalize bounding box coordinates to 0-1 range relative to page dimensions.
    
    Args:
        bbox: Absolute pixel coordinates (x1, y1, x2, y2)
        page_width: Page width in pixels
        page_height: Page height in pixels
        
    Returns:
        Normalized coordinates (x1_norm, y1_norm, x2_norm, y2_norm) in range [0, 1]
    """
    x1, y1, x2, y2 = bbox
    
    x1_norm = max(0.0, min(1.0, x1 / page_width))
    y1_norm = max(0.0, min(1.0, y1 / page_height))
    x2_norm = max(0.0, min(1.0, x2 / page_width))
    y2_norm = max(0.0, min(1.0, y2 / page_height))
    
    return (x1_norm, y1_norm, x2_norm, y2_norm)


def get_pdf_page_dimensions(path: str, page_num: int) -> Optional[Tuple[float, float]]:
    """
    Get dimensions of a specific PDF page.
    
    Args:
        path: Path to PDF file
        page_num: 0-based page number
        
    Returns:
        Tuple of (width, height) in points, or None if failed
    """
    try:
        if PYMUPDF_AVAILABLE:
            doc = fitz.open(path)
            if page_num < len(doc):
                page = doc[page_num]
                rect = page.rect
                dimensions = (rect.width, rect.height)
                doc.close()
                return dimensions
            doc.close()
        elif PDFPLUMBER_AVAILABLE:
            with pdfplumber.open(path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    return (page.width, page.height)
    except Exception as e:
        logger.warning(f"Failed to get page dimensions for page {page_num} in {path}: {e}")
    
    return None


def extract_pdf_text_blocks_for_captions(path: str, page_num: int) -> List[dict]:
    """
    Extract text blocks from a PDF page for caption detection.
    
    Returns text with bounding box information to help locate captions
    near images.
    
    Args:
        path: Path to PDF file
        page_num: 0-based page number
        
    Returns:
        List of dicts with 'text', 'bbox', and 'fontsize' keys
    """
    text_blocks = []
    
    try:
        if PDFPLUMBER_AVAILABLE:
            with pdfplumber.open(path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    
                    # Get words with position information
                    words = page.extract_words()
                    
                    # Group words into lines/blocks
                    current_line = []
                    current_y = None
                    
                    for word in words:
                        word_y = word.get('top', 0)
                        
                        # If this word is on a different line (different y coordinate)
                        if current_y is None or abs(word_y - current_y) > 5:  # 5 point tolerance
                            if current_line:
                                # Finalize current line
                                text = ' '.join([w['text'] for w in current_line])
                                min_x = min([w['x0'] for w in current_line])
                                max_x = max([w['x1'] for w in current_line])
                                min_y = min([w['top'] for w in current_line])
                                max_y = max([w['bottom'] for w in current_line])
                                
                                text_blocks.append({
                                    'text': text,
                                    'bbox': (min_x, min_y, max_x, max_y),
                                    'fontsize': current_line[0].get('size', 12)
                                })
                            
                            current_line = [word]
                            current_y = word_y
                        else:
                            current_line.append(word)
                    
                    # Don't forget the last line
                    if current_line:
                        text = ' '.join([w['text'] for w in current_line])
                        min_x = min([w['x0'] for w in current_line])
                        max_x = max([w['x1'] for w in current_line])
                        min_y = min([w['top'] for w in current_line])
                        max_y = max([w['bottom'] for w in current_line])
                        
                        text_blocks.append({
                            'text': text,
                            'bbox': (min_x, min_y, max_x, max_y),
                            'fontsize': current_line[0].get('size', 12)
                        })
                        
    except Exception as e:
        logger.warning(f"Failed to extract text blocks from page {page_num} in {path}: {e}")
    
    return text_blocks