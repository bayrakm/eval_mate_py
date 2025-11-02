"""
Document ingestion system for EvalMate.

Handles extraction of text content from PDF and DOCX files, converting
them into CanonicalDoc objects with structured DocBlocks for further processing.

Supports visual content extraction alongside text ingestion for comprehensive document analysis.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Union

# Core schema imports
from app.core.models.schemas import CanonicalDoc, DocBlock
from app.core.models.ids import new_doc_id, new_block_id

# Document processing imports
from .text_utils import (
    clean_text, split_into_paragraphs, normalize_whitespace,
    extract_title_from_text, remove_page_artifacts, merge_broken_words
)

logger = logging.getLogger(__name__)


def _convert_visual_blocks_to_doc_blocks(visual_blocks) -> List[DocBlock]:
    """
    Convert VisualBlock objects to DocBlock objects for document integration.
    
    Args:
        visual_blocks: List of VisualBlock objects from visual extraction
        
    Returns:
        List of DocBlock objects with kind='visual'
    """
    doc_blocks = []
    
    for visual_block in visual_blocks:
        try:
            # Create VisualBlock object for the schema
            from app.core.models.schemas import VisualBlock, VisualType
            
            # Map visual type to enum
            visual_type_map = {
                'image': VisualType.FIGURE,
                'table': VisualType.TABLE,
                'equation': VisualType.EQUATION,
                'chart': VisualType.CHART,
                'diagram': VisualType.DIAGRAM,
                'map': VisualType.MAP,
                'figure': VisualType.FIGURE
            }
            
            visual_type = visual_type_map.get(visual_block.visual_type, VisualType.FIGURE)
            
            # Extract structured table data if available
            structured_table = None
            if (visual_block.content and 
                isinstance(visual_block.content, dict) and 
                'type' in visual_block.content and 
                visual_block.content['type'] == 'table'):
                structured_table = visual_block.content.get('rows', [])
                if visual_block.content.get('headers'):
                    structured_table = [visual_block.content['headers']] + structured_table
            
            # Extract OCR text if available
            ocr_text = None
            if (visual_block.content and 
                isinstance(visual_block.content, dict)):
                ocr_text = visual_block.content.get('ocr_text')
            
            # Create VisualBlock for the schema
            visual_content = VisualBlock(
                type=visual_type,
                source_path=visual_block.asset_path or "unknown",  # Provide fallback for empty paths
                caption_text=visual_block.caption,
                ocr_text=ocr_text,
                structured_table=structured_table,
                detected_labels=None  # Could be populated in future
            )
            
            # Create DocBlock with VisualBlock
            doc_block = DocBlock(
                id=new_block_id(),
                kind="visual",
                text=None,  # Visual blocks don't have text content in the schema
                visual=visual_content,
                page=(visual_block.position.get('page', 0) + 1) if visual_block.position else 1,  # Convert 0-based to 1-based
                bbox=list(visual_block.position.get('bbox_norm')) if visual_block.position and visual_block.position.get('bbox_norm') else None  # Convert tuple to list
            )
            doc_blocks.append(doc_block)
            
        except Exception as e:
            logger.warning(f"Failed to convert visual block to doc block: {e}")
            continue
    
    return doc_blocks


def _extract_visuals_from_file(file_path: str) -> List[DocBlock]:
    """
    Extract visual content from a file and convert to DocBlock objects.
    
    Args:
        file_path: Path to the file to extract visuals from
        
    Returns:
        List of DocBlock objects with visual content
    """
    try:
        from app.core.visual_extraction import extract_visuals_from_document
        
        # Extract visual content
        visual_blocks = extract_visuals_from_document(file_path)
        
        # Convert to DocBlock format
        doc_blocks = _convert_visual_blocks_to_doc_blocks(visual_blocks)
        
        logger.info(f"Extracted {len(doc_blocks)} visual blocks from {file_path}")
        return doc_blocks
        
    except Exception as e:
        logger.warning(f"Visual extraction failed for {file_path}: {e}")
        return []


def ingest_pdf(path: str) -> CanonicalDoc:
    """
    Extract text from a PDF file, split into paragraph blocks, and return a CanonicalDoc.
    Each paragraph becomes one DocBlock(kind='text').
    Include page number and bbox=None for now.
    
    Args:
        path: Path to the PDF file
        
    Returns:
        CanonicalDoc with text blocks extracted from PDF
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the PDF cannot be parsed
        
    Examples:
        >>> doc = ingest_pdf("sample.pdf")
        >>> len(doc.blocks) > 0
        True
        >>> all(block.kind == "text" for block in doc.blocks)
        True
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF processing. Install with: pip install pdfplumber")
    
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    logger.info(f"Starting PDF ingestion: {path}")
    
    try:
        all_text = ""
        page_texts = []
        
        with pdfplumber.open(path) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                
                if page_text:
                    # Clean and process page text
                    page_text = remove_page_artifacts(page_text)
                    page_text = merge_broken_words(page_text)
                    page_text = clean_text(page_text)
                    
                    if page_text:  # Only store non-empty pages
                        page_texts.append((page_num, page_text))
                        all_text += page_text + "\n\n"
        
        if not all_text.strip():
            logger.warning(f"No text content found in PDF: {path}")
            blocks = []
        else:
            # Extract title from first page or filename
            title = extract_title_from_text(all_text) if all_text else path_obj.stem
            
            # Split into paragraphs and create blocks
            paragraphs = split_into_paragraphs(all_text)
            blocks = []
            
            # Track which page each paragraph likely came from
            current_page = 1
            for para in paragraphs:
                # Simple heuristic: assign paragraph to page based on content position
                for page_num, page_text in page_texts:
                    if para in page_text:
                        current_page = page_num
                        break
                
                block = DocBlock(
                    id=new_block_id(),
                    kind="text",
                    text=normalize_whitespace(para),
                    visual=None,
                    page=current_page,
                    bbox=None
                )
                blocks.append(block)
            
            logger.info(f"Extracted {len(blocks)} text blocks from PDF")
        
        # Create canonical document
        doc = CanonicalDoc(
            id=new_doc_id(),
            title=title if 'title' in locals() else path_obj.stem,
            source_files=[str(path_obj)],
            blocks=blocks,
            created_at=datetime.utcnow()
        )
        
        # Extract visual content and add to blocks
        visual_blocks = _extract_visuals_from_file(str(path_obj))
        doc.blocks.extend(visual_blocks)
        
        total_blocks = len(doc.blocks)
        text_blocks = len(blocks)
        visual_count = len(visual_blocks)
        
        logger.info(f"Successfully ingested PDF: {text_blocks} text blocks, {visual_count} visual blocks, {total_blocks} total")
        return doc
        
    except Exception as e:
        logger.error(f"Failed to parse PDF {path}: {e}")
        raise ValueError(f"Unable to parse {path}: {e}")


def ingest_docx(path: str) -> CanonicalDoc:
    """
    Extract text paragraphs from a Word document and return a CanonicalDoc.
    Skip empty paragraphs. Each becomes one DocBlock(kind='text').
    
    Args:
        path: Path to the DOCX file
        
    Returns:
        CanonicalDoc with text blocks extracted from DOCX
        
    Raises:
        FileNotFoundError: If the DOCX file doesn't exist
        ValueError: If the DOCX cannot be parsed
        
    Examples:
        >>> doc = ingest_docx("sample.docx")
        >>> len(doc.blocks) >= 0
        True
        >>> all(block.kind == "text" for block in doc.blocks)
        True
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
    
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")
    
    logger.info(f"Starting DOCX ingestion: {path}")
    
    try:
        doc_content = Document(path)
        
        # Extract all paragraphs
        raw_paragraphs = []
        for para in doc_content.paragraphs:
            if para.text.strip():  # Skip empty paragraphs
                raw_paragraphs.append(para.text)
        
        if not raw_paragraphs:
            logger.warning(f"No text content found in DOCX: {path}")
            blocks = []
            title = path_obj.stem
        else:
            # Combine all text for title extraction
            all_text = "\n\n".join(raw_paragraphs)
            title = extract_title_from_text(all_text)
            
            # Process each paragraph into a block
            blocks = []
            for para_text in raw_paragraphs:
                # Clean the paragraph text
                cleaned_text = clean_text(para_text)
                if cleaned_text:  # Only create blocks for non-empty text
                    block = DocBlock(
                        id=new_block_id(),
                        kind="text",
                        text=normalize_whitespace(cleaned_text),
                        visual=None,
                        page=1,  # DOCX doesn't have meaningful page numbers during extraction
                        bbox=None
                    )
                    blocks.append(block)
            
            logger.info(f"Extracted {len(blocks)} text blocks from DOCX")
        
        # Create canonical document
        doc = CanonicalDoc(
            id=new_doc_id(),
            title=title,
            source_files=[str(path_obj)],
            blocks=blocks,
            created_at=datetime.utcnow()
        )
        
        # Extract visual content and add to blocks
        visual_blocks = _extract_visuals_from_file(str(path_obj))
        doc.blocks.extend(visual_blocks)
        
        total_blocks = len(doc.blocks)
        text_blocks = len(blocks)
        visual_count = len(visual_blocks)
        
        logger.info(f"Successfully ingested DOCX: {text_blocks} text blocks, {visual_count} visual blocks, {total_blocks} total")
        return doc
        
    except Exception as e:
        logger.error(f"Failed to parse DOCX {path}: {e}")
        raise ValueError(f"Unable to parse {path}: {e}")


def ingest_image(path: str) -> CanonicalDoc:
    """
    Ingest image file with OCR and visual processing.
    
    Args:
        path: Path to the image file
        
    Returns:
        CanonicalDoc with OCR text blocks and visual content
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
        
    Examples:
        >>> doc = ingest_image("sample.jpg")
        >>> len(doc.blocks) >= 0
        True
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    
    logger.info(f"Starting image ingestion with visual processing: {path}")
    
    # Extract visual content from image
    visual_blocks = _extract_visuals_from_file(str(path_obj))
    
    # Extract any OCR text from visual blocks to create text blocks
    text_blocks = []
    for visual_doc_block in visual_blocks:
        if (visual_doc_block.visual and 
            visual_doc_block.visual.ocr_text and 
            visual_doc_block.visual.ocr_text.strip()):
            
            # Create text block from OCR content
            text_block = DocBlock(
                id=new_block_id(),
                kind="text",
                text=normalize_whitespace(clean_text(visual_doc_block.visual.ocr_text)),
                visual=None,
                page=1,
                bbox=None
            )
            text_blocks.append(text_block)
    
    # Combine text and visual blocks
    all_blocks = text_blocks + visual_blocks
    
    # Create canonical document
    doc = CanonicalDoc(
        id=new_doc_id(),
        title=path_obj.stem,
        source_files=[str(path_obj)],
        blocks=all_blocks,
        created_at=datetime.utcnow()
    )
    
    text_count = len(text_blocks)
    visual_count = len(visual_blocks)
    
    logger.info(f"Successfully processed image: {text_count} text blocks (OCR), {visual_count} visual blocks")
    return doc


def detect_file_type(path: str) -> str:
    """
    Return one of: 'pdf', 'docx', 'image', 'unknown' based on file extension.
    
    Args:
        path: Path to the file
        
    Returns:
        File type string: 'pdf', 'docx', 'image', or 'unknown'
        
    Examples:
        >>> detect_file_type("document.pdf")
        'pdf'
        >>> detect_file_type("report.docx")
        'docx'
        >>> detect_file_type("image.jpg")
        'image'
        >>> detect_file_type("unknown.xyz")
        'unknown'
    """
    path_obj = Path(path)
    extension = path_obj.suffix.lower()
    
    if extension == '.pdf':
        return 'pdf'
    elif extension in ['.docx', '.doc']:
        return 'docx'
    elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']:
        return 'image'
    else:
        return 'unknown'


def ingest_any(path: str) -> CanonicalDoc:
    """
    Auto-detect file type and call appropriate ingest_*() function.
    
    Args:
        path: Path to the file to ingest
        
    Returns:
        CanonicalDoc from the appropriate ingestion function
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file type is unsupported or parsing fails
        
    Examples:
        >>> doc = ingest_any("sample.pdf")
        >>> isinstance(doc, CanonicalDoc)
        True
        >>> doc = ingest_any("sample.docx")
        >>> isinstance(doc, CanonicalDoc)
        True
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    file_type = detect_file_type(path)
    logger.info(f"Detected file type '{file_type}' for: {path}")
    
    if file_type == 'pdf':
        return ingest_pdf(path)
    elif file_type == 'docx':
        return ingest_docx(path)
    elif file_type == 'image':
        return ingest_image(path)
    else:
        raise ValueError(f"Unsupported file type '{file_type}' for file: {path}")


def batch_ingest(paths: List[str]) -> List[CanonicalDoc]:
    """
    Ingest multiple files and return a list of CanonicalDoc objects.
    
    Args:
        paths: List of file paths to ingest
        
    Returns:
        List of CanonicalDoc objects
        
    Note:
        This function logs errors for individual files but continues processing.
        Failed files are skipped and not included in the results.
    """
    docs = []
    
    for path in paths:
        try:
            doc = ingest_any(path)
            docs.append(doc)
            logger.info(f"Successfully ingested: {path}")
        except Exception as e:
            logger.error(f"Failed to ingest {path}: {e}")
            # Continue with other files
    
    logger.info(f"Batch ingestion complete: {len(docs)}/{len(paths)} files processed")
    return docs


def get_supported_extensions() -> List[str]:
    """
    Get list of supported file extensions.
    
    Returns:
        List of supported file extensions (with dots)
        
    Examples:
        >>> extensions = get_supported_extensions()
        >>> '.pdf' in extensions
        True
        >>> '.docx' in extensions
        True
    """
    return ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']


def is_supported_file(path: str) -> bool:
    """
    Check if a file is supported for ingestion.
    
    Args:
        path: Path to check
        
    Returns:
        True if file type is supported
        
    Examples:
        >>> is_supported_file("document.pdf")
        True
        >>> is_supported_file("data.csv")
        False
    """
    return detect_file_type(path) != 'unknown'


def ingest_with_captioning(path: str, enable_captions: bool = True) -> CanonicalDoc:
    """
    Ingest document with multimodal captioning for visual content.
    
    This function extends the standard ingestion pipeline to include
    automatic caption generation for visual elements using GPT-5/GPT-4o.
    
    Args:
        path: Path to the document to ingest
        enable_captions: Whether to generate captions for visual blocks
        
    Returns:
        CanonicalDoc with captioned visual content
        
    Examples:
        >>> doc = ingest_with_captioning("sample.pdf")
        >>> visual_blocks = [b for b in doc.blocks if b.kind == "visual"]
        >>> assert all(b.visual.caption_text for b in visual_blocks)
    """
    logger.info(f"Starting document ingestion with captioning: {path} (captions={enable_captions})")
    
    # First, do standard ingestion
    canonical_doc = ingest_any(path)
    
    if not enable_captions:
        logger.info("Captioning disabled, returning standard ingestion result")
        return canonical_doc
    
    # Extract visual blocks for captioning
    visual_blocks = []
    text_blocks = []
    
    for block in canonical_doc.blocks:
        if block.kind == "visual" and block.visual:
            # Convert DocBlock VisualBlock to the types used by captioning
            from app.core.types import VisualBlock as CaptioningVisualBlock
            
            # Create a VisualBlock object for the captioning system
            captioning_visual = CaptioningVisualBlock(
                block_id=block.id,
                source_path=block.visual.source_path,
                caption_text=block.visual.caption_text or "",
                page_number=block.page,
                metadata={
                    "visual_type": block.visual.type.value if block.visual.type else "figure",
                    "bbox": block.bbox,
                    "ocr_text": block.visual.ocr_text,
                    "original_schema": "doc_block"
                }
            )
            visual_blocks.append(captioning_visual)
        else:
            text_blocks.append(block)
    
    # Generate captions for visual blocks if any exist
    if visual_blocks:
        logger.info(f"Generating captions for {len(visual_blocks)} visual blocks")
        
        try:
            # Import captioning functionality
            from app.core.io.captioning import caption_document_visuals
            
            # Generate captions
            captioned_visuals = caption_document_visuals(
                visual_blocks=visual_blocks,
                use_batch_processing=True,
                enable_ocr=True
            )
            
            # Update the original blocks with captions
            visual_block_map = {vb.block_id: vb for vb in captioned_visuals}
            
            updated_blocks = []
            for block in canonical_doc.blocks:
                if block.kind == "visual" and block.id in visual_block_map:
                    captioned_visual = visual_block_map[block.id]
                    
                    # Update the visual block with new caption
                    block.visual.caption_text = captioned_visual.caption_text
                    
                    # Add OCR text if available
                    if "ocr_text" in captioned_visual.metadata:
                        block.visual.ocr_text = captioned_visual.metadata["ocr_text"]
                
                updated_blocks.append(block)
            
            # Update the canonical document
            canonical_doc.blocks = updated_blocks
            
            # Update metadata
            canonical_doc.metadata["phase_7_captioning"] = True
            canonical_doc.metadata["captioned_visuals"] = len(captioned_visuals)
            canonical_doc.metadata["processing_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"Successfully added captions to {len(captioned_visuals)} visual blocks")
            
        except Exception as e:
            logger.error(f"Failed to generate captions: {e}")
            # Continue without captions rather than failing entirely
            canonical_doc.metadata["phase_7_captioning"] = False
            canonical_doc.metadata["captioning_error"] = str(e)
    else:
        logger.info("No visual blocks found for captioning")
        canonical_doc.metadata["phase_7_captioning"] = True
        canonical_doc.metadata["captioned_visuals"] = 0
    
    return canonical_doc