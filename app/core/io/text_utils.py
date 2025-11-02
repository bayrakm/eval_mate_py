"""
Text processing utilities for EvalMate document ingestion.

Provides text cleaning and segmentation functions to normalize content
before creating DocBlocks from extracted document text.
"""

import re
import unicodedata
import logging
import regex
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Strip whitespace, collapse multiple spaces/newlines, and normalize Unicode.
    
    Args:
        text: Raw text string to clean
        
    Returns:
        Cleaned and normalized text string
        
    Examples:
        >>> clean_text("  Hello\\n\\n\\nworld!  ")
        'Hello\\n\\nworld!'
        >>> clean_text("Text   with    spaces")
        'Text with spaces'
    """
    if not text:
        return ""
    
    # Normalize Unicode characters (NFKC form)
    text = unicodedata.normalize('NFKC', text)
    
    # Remove or replace problematic characters
    text = text.replace('\r\n', '\n')  # Normalize line endings
    text = text.replace('\r', '\n')    # Handle old Mac line endings
    
    # Collapse multiple spaces into single spaces
    text = re.sub(r' +', ' ', text)
    
    # Collapse multiple newlines into at most double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text by double newline or large whitespace gaps into logical paragraphs.
    
    Args:
        text: Cleaned text string to split
        
    Returns:
        List of paragraph strings, filtered to remove empty paragraphs
        
    Examples:
        >>> split_into_paragraphs("Para 1\\n\\nPara 2\\n\\nPara 3")
        ['Para 1', 'Para 2', 'Para 3']
        >>> split_into_paragraphs("Single paragraph with\\nline breaks")
        ['Single paragraph with\\nline breaks']
    """
    if not text:
        return []
    
    # Split on double newlines (paragraph boundaries)
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Clean each paragraph and filter out empty ones
    cleaned_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para:  # Only keep non-empty paragraphs
            cleaned_paragraphs.append(para)
    
    logger.debug(f"Split text into {len(cleaned_paragraphs)} paragraphs")
    return cleaned_paragraphs


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace within a paragraph while preserving structure.
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
        
    Examples:
        >>> normalize_whitespace("Line 1\\nLine 2\\nLine 3")
        'Line 1\\nLine 2\\nLine 3'
        >>> normalize_whitespace("Text    with\\ttabs")
        'Text with tabs'
    """
    if not text:
        return ""
    
    # Replace tabs and other whitespace with spaces
    text = re.sub(r'[\t\f\v]+', ' ', text)
    
    # Collapse multiple spaces but preserve single newlines
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Collapse spaces within each line
        line = re.sub(r' +', ' ', line.strip())
        normalized_lines.append(line)
    
    return '\n'.join(normalized_lines)


def extract_title_from_text(text: str, max_length: int = 100) -> str:
    """
    Extract a likely title from the beginning of text content.
    
    Args:
        text: Full text content
        max_length: Maximum length for title
        
    Returns:
        Extracted title string
        
    Examples:
        >>> extract_title_from_text("Assignment 1: Data Analysis\\n\\nThis is the content...")
        'Assignment 1: Data Analysis'
        >>> extract_title_from_text("Very long title that exceeds the maximum length limit")[:20]
        'Very long title that'
    """
    if not text:
        return "Untitled Document"
    
    # Try to find the first line that looks like a title
    lines = text.split('\n')
    
    for line in lines[:3]:  # Check first 3 lines
        line = line.strip()
        if line and len(line) <= max_length:
            # Check if it looks like a title (not too long, has capital letters)
            if any(c.isupper() for c in line) and len(line.split()) <= 15:
                return line
    
    # Fallback: use first line or truncated first paragraph
    first_line = lines[0].strip() if lines else ""
    if first_line:
        if len(first_line) <= max_length:
            return first_line
        else:
            # Truncate at word boundary
            words = first_line.split()
            title = ""
            for word in words:
                if len(title + " " + word) <= max_length - 3:
                    title += (" " if title else "") + word
                else:
                    break
            return title + "..." if title else "Untitled Document"
    
    return "Untitled Document"


def is_likely_header(text: str) -> bool:
    """
    Determine if a text block is likely a header or section title.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if text appears to be a header
        
    Examples:
        >>> is_likely_header("Chapter 1: Introduction")
        True
        >>> is_likely_header("This is a long paragraph with lots of text content.")
        False
    """
    if not text:
        return False
    
    text = text.strip()
    
    # Check length - headers are usually short
    if len(text) > 150:
        return False
    
    # Check for header patterns
    header_patterns = [
        r'^(Chapter|Section|Part)\s+\d+',  # Chapter 1, Section 2, etc.
        r'^\d+\.\s+',  # Numbered sections: "1. Introduction"
        r'^[A-Z][^.]*[^.]$',  # All caps or title case, no ending period
        r'^\d+\.\d+',  # Subsection numbering: "1.1", "2.3"
    ]
    
    for pattern in header_patterns:
        if re.match(pattern, text):
            return True
    
    # Check if all words are title case and no ending punctuation
    words = text.split()
    if len(words) <= 8 and all(word[0].isupper() for word in words if word):
        if not text.endswith(('.', '!', '?')):
            return True
    
    return False


def remove_page_artifacts(text: str) -> str:
    """
    Remove common PDF artifacts like page numbers, headers, footers.
    
    Args:
        text: Text that may contain page artifacts
        
    Returns:
        Text with artifacts removed
        
    Examples:
        >>> remove_page_artifacts("Page 5\\nActual content here\\nFooter text")
        'Actual content here'
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip likely page numbers
        if re.match(r'^(Page\s+)?\d+$', line, re.IGNORECASE):
            continue
        
        # Skip very short lines that might be headers/footers
        if len(line) < 10 and (line.isupper() or line.isdigit()):
            continue
        
        # Skip common footer patterns
        footer_patterns = [
            r'^(confidential|proprietary|copyright|\(c\))',
            r'^\d{1,2}/\d{1,2}/\d{2,4}$',  # Dates
            r'^www\.',  # URLs
        ]
        
        is_footer = False
        for pattern in footer_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_footer = True
                break
        
        if not is_footer:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def merge_broken_words(text: str) -> str:
    """
    Merge words that were broken across lines during PDF extraction.
    
    Args:
        text: Text with potentially broken words
        
    Returns:
        Text with broken words merged
        
    Examples:
        >>> merge_broken_words("This is bro-\\nken text")
        'This is broken text'
        >>> merge_broken_words("Hyphen-\\nated word")
        'Hyphenated word'
    """
    if not text:
        return ""
    
    # Pattern for words broken with hyphens across lines
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # Pattern for words broken without hyphens (less common)
    text = re.sub(r'(\w+)\s*\n\s*([a-z]+)', r'\1\2', text)
    
    return text


# Phase 4: Rubric parsing utilities

# Bullet markers pattern
BULLET_MARKERS = r"[•\-\–\*\+]+"

def detect_bulleted_items(text: str) -> List[str]:
    """
    Split text into bullet list items based on bullet markers.
    
    Args:
        text: Text containing bullet points
        
    Returns:
        List of individual bullet items (without markers)
        
    Examples:
        >>> detect_bulleted_items("• Item 1\\n• Item 2\\n• Item 3")
        ['Item 1', 'Item 2', 'Item 3']
    """
    if not text:
        return []
    
    # First check if there are any bullet markers
    pattern = rf"^\s*{BULLET_MARKERS}\s*"
    if not regex.search(pattern, text, flags=regex.MULTILINE):
        return []  # No bullet markers found
    
    # Split on bullet markers at line start
    items = regex.split(pattern, text, flags=regex.MULTILINE)
    
    # Clean up items and filter empty ones
    cleaned_items = []
    for item in items:
        cleaned = clean_text(item)
        if cleaned:
            cleaned_items.append(cleaned)
    
    return cleaned_items


def detect_numbered_items(text: str) -> List[str]:
    """
    Split text into numbered list items.
    
    Args:
        text: Text containing numbered items
        
    Returns:
        List of individual numbered items (without numbers)
        
    Examples:
        >>> detect_numbered_items("1. First item\\n2. Second item\\n3. Third item")
        ['First item', 'Second item', 'Third item']
    """
    if not text:
        return []
    
    # Pattern for various numbering schemes
    numbering_patterns = [
        r"^\s*\d+\.\s*",           # 1. 2. 3.
        r"^\s*\d+\)\s*",           # 1) 2) 3)
        r"^\s*\(\d+\)\s*",         # (1) (2) (3)
        r"^\s*[a-z]\.\s*",         # a. b. c.
        r"^\s*[a-z]\)\s*",         # a) b) c)
        r"^\s*\([a-z]\)\s*",       # (a) (b) (c)
        r"^\s*[ivx]+\.\s*",        # i. ii. iii.
        r"^\s*\([ivx]+\)\s*",      # (i) (ii) (iii)
    ]
    
    # Try each pattern
    for pattern in numbering_patterns:
        items = regex.split(pattern, text, flags=regex.MULTILINE | regex.IGNORECASE)
        if len(items) > 1:
            # Clean up items and filter empty ones
            cleaned_items = []
            for item in items:
                cleaned = clean_text(item)
                if cleaned:
                    cleaned_items.append(cleaned)
            
            if len(cleaned_items) > 1:  # At least 2 items found
                return cleaned_items
    
    return []


def split_heading_and_body(item_text: str) -> Tuple[str, str]:
    """
    Split item text into title (heading) and description (body).
    
    Args:
        item_text: Full text of a list item
        
    Returns:
        Tuple of (title, description)
        
    Examples:
        >>> split_heading_and_body("Accuracy: Check facts and calculations")
        ('Accuracy', 'Check facts and calculations')
        >>> split_heading_and_body("Structure - organize content well")
        ('Structure', 'organize content well')
    """
    if not item_text:
        return "", ""
    
    # Pattern 1: Look for colon separator
    colon_match = regex.match(r"^([^:]+):\s*(.*)$", item_text, regex.DOTALL)
    if colon_match:
        title = clean_text(colon_match.group(1))
        description = clean_text(colon_match.group(2))
        return title, description
    
    # Pattern 2: Look for dash separator  
    dash_match = regex.match(r"^([^—–-]+)\s*[—–-]\s*(.*)$", item_text, regex.DOTALL)
    if dash_match:
        title = clean_text(dash_match.group(1))
        description = clean_text(dash_match.group(2))
        return title, description
    
    # Pattern 3: Look for parenthetical weight and split around it
    weight_match = regex.search(r"\([\d%\.]+\)", item_text)
    if weight_match:
        before_weight = item_text[:weight_match.start()].strip()
        after_weight = item_text[weight_match.end():].strip()
        
        if before_weight and after_weight:
            return clean_text(before_weight), clean_text(after_weight)
        elif before_weight:
            # Title is before weight, description is empty
            return clean_text(before_weight), ""
    
    # Pattern 4: Split on first sentence boundary or first ~8 words
    sentences = regex.split(r"[.!?]+", item_text, maxsplit=1)
    if len(sentences) > 1 and len(sentences[0]) < 100:
        title = clean_text(sentences[0])
        description = clean_text(sentences[1])
        return title, description
    
    # Pattern 5: Take first ~8 words as title
    words = item_text.split()
    if len(words) > 8:
        title_words = words[:8]
        description_words = words[8:]
        title = " ".join(title_words)
        description = " ".join(description_words)
        return clean_text(title), clean_text(description)
    
    # Fallback: entire text as title, empty description
    return clean_text(item_text), ""


def parse_inline_weight(text: str) -> Tuple[Optional[float], str]:
    """
    Parse inline weight tokens and remove them from text.
    
    Args:
        text: Text that may contain weight indicators
        
    Returns:
        Tuple of (weight_fraction or None, text_without_weight)
        
    Examples:
        >>> parse_inline_weight("Accuracy (40%): Check facts")
        (0.4, 'Accuracy : Check facts')
        >>> parse_inline_weight("Structure [30 pts] - organize well")  
        (0.3, 'Structure  - organize well')
    """
    if not text:
        return None, text
    
    # Weight patterns to detect
    weight_patterns = [
        # Percentage patterns
        (r"\((\d+(?:\.\d+)?)\s*%\)", r"percentage"),
        (r"\[(\d+(?:\.\d+)?)\s*%\]", r"percentage"),
        (r"(\d+(?:\.\d+)?)\s*%", r"percentage"),
        
        # Points patterns  
        (r"\((\d+(?:\.\d+)?)\s*(?:pts?|points?)\)", r"points"),
        (r"\[(\d+(?:\.\d+)?)\s*(?:pts?|points?)\]", r"points"),
        (r"(\d+(?:\.\d+)?)\s*(?:pts?|points?)", r"points"),
        
        # Fraction patterns
        (r"\((\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)\)", r"fraction"),
        (r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)", r"fraction"),
        
        # Weight label patterns
        (r"weight:\s*(\d+(?:\.\d+)?)", r"decimal"),
        (r"weight\s*=\s*(\d+(?:\.\d+)?)", r"decimal"),
    ]
    
    for pattern, weight_type in weight_patterns:
        match = regex.search(pattern, text, regex.IGNORECASE)
        if match:
            # Extract weight value
            if weight_type == "percentage":
                weight = float(match.group(1)) / 100.0
            elif weight_type == "points":
                # For points, we'll normalize later - just store as fraction for now
                weight = float(match.group(1))
            elif weight_type == "fraction":
                numerator = float(match.group(1))
                denominator = float(match.group(2))
                weight = numerator / denominator if denominator != 0 else None
            elif weight_type == "decimal":
                val = float(match.group(1))
                # If > 1, assume it's percentage
                weight = val / 100.0 if val > 1 else val
            else:
                weight = None
            
            # Remove weight token from text
            cleaned_text = regex.sub(pattern, "", text, flags=regex.IGNORECASE).strip()
            cleaned_text = regex.sub(r"\s+", " ", cleaned_text)  # Collapse spaces
            
            return weight, cleaned_text
    
    return None, text