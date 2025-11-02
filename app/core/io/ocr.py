"""
OCR Wrapper Module - Tesseract Integration with Graceful Fallbacks

This module provides OCR functionality using Tesseract OCR with preprocessing
and graceful error handling. It's designed to work without Tesseract installed
by failing gracefully rather than raising exceptions.

Supports visual content text extraction for comprehensive document processing.
"""

import shutil
import logging
from typing import Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Optional imports with graceful fallbacks
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available, OCR functionality will be disabled")

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.info("OpenCV not available, OCR preprocessing will be basic")


def tesseract_available() -> bool:
    """
    Check if Tesseract OCR binary is available on the system PATH.
    
    Returns:
        bool: True if tesseract binary is found, False otherwise
    """
    if not PYTESSERACT_AVAILABLE:
        return False
    
    return shutil.which("tesseract") is not None


def preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR results using OpenCV if available.
    
    Applies:
    - Grayscale conversion
    - Threshold to binary image
    - Mild median blur to reduce noise
    
    Args:
        img: PIL Image to preprocess
        
    Returns:
        PIL.Image: Preprocessed image, or original if OpenCV unavailable
    """
    if not OPENCV_AVAILABLE:
        # Basic preprocessing: convert to grayscale
        return img.convert('L')
    
    try:
        # Convert PIL to OpenCV format
        img_array = np.array(img)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply median blur to reduce noise
        denoised = cv2.medianBlur(gray, 3)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        return Image.fromarray(thresh)
        
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}, using original image")
        return img.convert('L')


def ocr_image_to_text(img: Image.Image, lang: str = 'eng', psm: int = 6) -> str:
    """
    Extract text from image using Tesseract OCR with preprocessing.
    
    Args:
        img: PIL Image to process
        lang: Tesseract language code (default: 'eng')
        psm: Page segmentation mode (default: 6 - uniform block of text)
    
    Returns:
        str: Extracted text, empty string if OCR fails or unavailable
    """
    if not tesseract_available():
        logger.debug("Tesseract not available, returning empty OCR text")
        return ""
    
    try:
        # Preprocess image for better OCR
        processed_img = preprocess_image_for_ocr(img)
        
        # Configure Tesseract
        config = f'--psm {psm} -l {lang}'
        
        # Run OCR
        text = pytesseract.image_to_string(processed_img, config=config)
        
        # Clean up the text
        text = text.strip()
        
        logger.debug(f"OCR extracted {len(text)} characters")
        return text
        
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return ""


def detect_math_symbols(text: str) -> bool:
    """
    Detect if text contains mathematical symbols or notation.
    
    Used for heuristic type detection of visual blocks.
    
    Args:
        text: Text to analyze
        
    Returns:
        bool: True if mathematical symbols detected
    """
    math_symbols = {
        # Greek letters
        'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',
        'Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ', 'Ν', 'Ξ', 'Ο', 'Π', 'Ρ', 'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω',
        # Mathematical operators
        '∑', '∏', '∫', '∮', '∆', '∇', '∂', '∞', '±', '∓', '×', '÷', '√', '∛', '∜',
        # Comparison operators
        '≈', '≠', '≡', '≤', '≥', '⊂', '⊃', '⊆', '⊇', '∈', '∉', '∪', '∩',
        # Arrows
        '→', '←', '↑', '↓', '↔', '⇒', '⇐', '⇑', '⇓', '⇔',
        # Other symbols
        '°', '′', '″', '‰', '∝', '⊥', '∠', '∥'
    }
    
    # Check for direct symbol matches
    for symbol in math_symbols:
        if symbol in text:
            return True
    
    # Check for common math patterns
    math_patterns = ['x^', '^2', '^3', '_i', '_j', '_n', 'sin(', 'cos(', 'tan(', 'log(', 'ln(', 'exp(']
    for pattern in math_patterns:
        if pattern in text.lower():
            return True
    
    return False


def extract_equation_keywords(text: str) -> list[str]:
    """
    Extract equation-related keywords from OCR text.
    
    Args:
        text: OCR text to analyze
        
    Returns:
        list: Keywords that suggest mathematical content
    """
    equation_keywords = []
    
    # Common mathematical terms
    math_terms = [
        'equation', 'formula', 'theorem', 'proof', 'derivative', 'integral',
        'function', 'variable', 'constant', 'matrix', 'vector', 'limit',
        'sum', 'product', 'infinity', 'logarithm', 'exponential'
    ]
    
    text_lower = text.lower()
    for term in math_terms:
        if term in text_lower:
            equation_keywords.append(term)
    
    # Check for mathematical symbols
    if detect_math_symbols(text):
        equation_keywords.append('mathematical_symbols')
    
    return equation_keywords


def extract_text_with_tesseract(image_path: str, lang: str = 'eng', psm: int = 6) -> str:
    """
    Extract text from image file using Tesseract OCR.
    
    This is the main function used by the captioning system.
    
    Args:
        image_path: Path to the image file
        lang: Tesseract language code (default: 'eng')
        psm: Page segmentation mode (default: 6 - uniform block of text)
        
    Returns:
        Extracted text content
    """
    try:
        # Open and process image
        img = Image.open(image_path)
        
        # Extract text using OCR
        text = ocr_image_to_text(img, lang=lang, psm=psm)
        
        return text.strip()
        
    except Exception as e:
        logger.warning(f"OCR extraction failed for {image_path}: {e}")
        return ""