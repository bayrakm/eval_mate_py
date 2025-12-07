"""
Visual Extraction Orchestrator

Main module for coordinating visual content extraction from documents.
This orchestrator handles images, tables, equations, and other visual elements
from PDF and DOCX files, producing VisualBlock representations for processing.

Supports comprehensive visual content extraction and metadata generation.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union, Iterator
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VisualBlock:
    """
    Canonical representation of visual content for document processing.
    
    Attributes:
        visual_type: Type of visual content (image, table, equation, diagram, etc.)
        content: The visual content data (varies by type)
        caption: Caption or description if available
        position: Position information (page, bbox, etc.)
        metadata: Additional metadata about extraction and content
        asset_path: Path to saved visual asset if applicable
    """
    visual_type: str
    content: Any
    caption: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    asset_path: Optional[str] = None


class VisualExtractor:
    """
    Main orchestrator for visual content extraction.
    
    Handles coordination between different extraction modules:
    - OCR for text-in-images
    - PDF image/table extraction 
    - DOCX image/table/equation extraction
    - Caption detection heuristics
    - Asset management
    """
    
    def __init__(self, assets_dir: str = "data/assets"):
        """
        Initialize the visual extractor.
        
        Args:
            assets_dir: Directory to store extracted visual assets
        """
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extraction counters for asset naming
        self.extraction_counters = {
            'image': 0,
            'table': 0,
            'equation': 0
        }
        
        logger.info(f"Visual extractor initialized with assets directory: {self.assets_dir}")
    
    def extract_visuals_from_file(self, file_path: str) -> List[VisualBlock]:
        """
        Extract all visual content from a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of VisualBlock objects representing extracted visual content
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        logger.info(f"Extracting visuals from: {file_path}")
        
        # Determine file type and route to appropriate extractor
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._extract_from_pdf(str(file_path))
        elif suffix == '.docx':
            return self._extract_from_docx(str(file_path))
        elif suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
            return self._extract_from_image(str(file_path))
        else:
            logger.warning(f"Unsupported file type for visual extraction: {suffix}")
            return []
    
    def _extract_from_pdf(self, pdf_path: str) -> List[VisualBlock]:
        """Extract visual content from PDF file."""
        visual_blocks = []
        
        try:
            # Extract images with metadata
            images = self._extract_pdf_images(pdf_path)
            visual_blocks.extend(images)
            
            # Extract tables with enhanced context
            tables = self._extract_pdf_tables(pdf_path)
            visual_blocks.extend(tables)
            
            logger.info(f"Extracted {len(visual_blocks)} visual elements from PDF: {pdf_path}")
            
        except Exception as e:
            logger.error(f"Failed to extract visuals from PDF {pdf_path}: {e}")
        
        return visual_blocks
    
    def _extract_from_docx(self, docx_path: str) -> List[VisualBlock]:
        """Extract visual content from DOCX file."""
        visual_blocks = []
        
        try:
            # Extract images with alt text and context
            images = self._extract_docx_images(docx_path)
            visual_blocks.extend(images)
            
            # Extract tables with enhanced context
            tables = self._extract_docx_tables(docx_path)
            visual_blocks.extend(tables)
            
            # Extract equations
            equations = self._extract_docx_equations(docx_path)
            visual_blocks.extend(equations)
            
            logger.info(f"Extracted {len(visual_blocks)} visual elements from DOCX: {docx_path}")
            
        except Exception as e:
            logger.error(f"Failed to extract visuals from DOCX {docx_path}: {e}")
        
        return visual_blocks
    
    def _extract_from_image(self, image_path: str) -> List[VisualBlock]:
        """Extract visual content from standalone image file."""
        visual_blocks = []
        
        try:
            # Create VisualBlock for the image itself
            asset_path = self._save_image_asset(image_path)
            
            # Try OCR on the image
            ocr_text = self._extract_text_from_image(image_path)
            
            # Detect if image contains mathematical content
            is_equation = self._detect_equation_in_image(image_path, ocr_text)
            
            visual_type = 'equation' if is_equation else 'image'
            
            visual_block = VisualBlock(
                visual_type=visual_type,
                content={
                    'image_path': image_path,
                    'ocr_text': ocr_text if ocr_text else None,
                    'is_equation': is_equation
                },
                caption=None,  # No caption available for standalone image
                position={'source': 'standalone_image'},
                metadata={
                    'extraction_method': 'standalone_image',
                    'has_ocr_text': bool(ocr_text),
                    'file_size': os.path.getsize(image_path) if os.path.exists(image_path) else 0
                },
                asset_path=asset_path
            )
            
            visual_blocks.append(visual_block)
            logger.info(f"Processed standalone image: {image_path}")
            
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
        
        return visual_blocks
    
    def _extract_pdf_images(self, pdf_path: str) -> List[VisualBlock]:
        """Extract images from PDF with full context."""
        visual_blocks = []
        
        try:
            from app.core.io.pdf_utils import extract_pdf_images_with_bbox
            from app.core.io.caption_heuristics import infer_caption_for_pdf
            
            # Extract images with bounding box information
            for image_data in extract_pdf_images_with_bbox(pdf_path):
                # Save image asset
                asset_path = self._save_pdf_image_asset(image_data, pdf_path)
                
                # Try to infer caption
                caption = infer_caption_for_pdf(
                    pdf_path, 
                    image_data.page, 
                    image_data.bbox_norm
                )
                
                # Apply OCR to extract text
                ocr_text = None
                if asset_path and os.path.exists(asset_path):
                    ocr_text = self._extract_text_from_image(asset_path)
                
                # Detect if this is an equation
                is_equation = self._detect_equation_in_image(asset_path, ocr_text)
                
                visual_type = 'equation' if is_equation else 'image'
                
                visual_block = VisualBlock(
                    visual_type=visual_type,
                    content={
                        'image_data': image_data,
                        'ocr_text': ocr_text,
                        'is_equation': is_equation
                    },
                    caption=caption,
                    position={
                        'page': image_data.page,
                        'bbox_norm': image_data.bbox_norm,
                        'page_width': image_data.page_width,
                        'page_height': image_data.page_height
                    },
                    metadata={
                        'extraction_method': 'pdf_pymupdf',
                        'source_file': pdf_path,
                        'has_caption': bool(caption),
                        'has_ocr_text': bool(ocr_text)
                    },
                    asset_path=asset_path
                )
                
                visual_blocks.append(visual_block)
                
        except Exception as e:
            logger.error(f"Failed to extract images from PDF {pdf_path}: {e}")
        
        return visual_blocks
    
    def _extract_pdf_tables(self, pdf_path: str) -> List[VisualBlock]:
        """Extract tables from PDF with enhanced context."""
        visual_blocks = []
        
        try:
            from app.core.io.table_extraction import extract_tables_with_context_pdf, convert_enhanced_table_to_visual_block
            
            # Extract tables with enhanced metadata
            enhanced_tables = extract_tables_with_context_pdf(pdf_path)
            
            for table_data in enhanced_tables:
                # Convert to VisualBlock format
                visual_block_data = convert_enhanced_table_to_visual_block(table_data)
                
                # Create table image representation for visual analysis
                table_image_path = self._create_table_image_asset(table_data, pdf_path)
                
                visual_block = VisualBlock(
                    visual_type='table',
                    content=visual_block_data['content'],
                    caption=visual_block_data['caption'],
                    position={
                        'page': table_data.source_info.get('page', 0),
                        'table_index': table_data.source_info.get('table_index', 0)
                    },
                    metadata=visual_block_data['metadata'],
                    asset_path=table_image_path
                )
                
                visual_blocks.append(visual_block)
                
        except Exception as e:
            logger.error(f"Failed to extract tables from PDF {pdf_path}: {e}")
        
        return visual_blocks
    
    def _extract_docx_images(self, docx_path: str) -> List[VisualBlock]:
        """Extract images from DOCX with full context."""
        visual_blocks = []
        
        try:
            from app.core.io.docx_utils import iter_docx_images
            from app.core.io.caption_heuristics import infer_caption_for_docx
            
            # Extract images with metadata
            for image_data in iter_docx_images(docx_path):
                # Save image asset
                asset_path = self._save_docx_image_asset(image_data, docx_path)
                
                # Try to infer caption from alt text or nearby paragraphs
                caption = infer_caption_for_docx(
                    docx_path,
                    image_data.alt_text,
                    image_data.paragraph_index
                )
                
                # Apply OCR to extract text
                ocr_text = None
                if asset_path and os.path.exists(asset_path):
                    ocr_text = self._extract_text_from_image(asset_path)
                
                # Detect if this is an equation
                is_equation = self._detect_equation_in_image(asset_path, ocr_text)
                
                visual_type = 'equation' if is_equation else 'image'
                
                visual_block = VisualBlock(
                    visual_type=visual_type,
                    content={
                        'image_data': image_data,
                        'ocr_text': ocr_text,
                        'is_equation': is_equation
                    },
                    caption=caption,
                    position={
                        'paragraph_index': image_data.paragraph_index,
                        'run_index': image_data.run_index,
                        'image_type': image_data.image_type
                    },
                    metadata={
                        'extraction_method': 'docx_python-docx',
                        'source_file': docx_path,
                        'has_alt_text': bool(image_data.alt_text),
                        'has_caption': bool(caption),
                        'has_ocr_text': bool(ocr_text)
                    },
                    asset_path=asset_path
                )
                
                visual_blocks.append(visual_block)
                
        except Exception as e:
            logger.error(f"Failed to extract images from DOCX {docx_path}: {e}")
        
        return visual_blocks
    
    def _extract_docx_tables(self, docx_path: str) -> List[VisualBlock]:
        """Extract tables from DOCX with enhanced context."""
        visual_blocks = []
        
        try:
            from app.core.io.table_extraction import extract_tables_with_context_docx, convert_enhanced_table_to_visual_block
            
            # Extract tables with enhanced metadata
            enhanced_tables = extract_tables_with_context_docx(docx_path)
            
            for table_data in enhanced_tables:
                # Convert to VisualBlock format
                visual_block_data = convert_enhanced_table_to_visual_block(table_data)
                
                # Create table image representation for visual analysis
                table_image_path = self._create_table_image_asset(table_data, docx_path)
                
                visual_block = VisualBlock(
                    visual_type='table',
                    content=visual_block_data['content'],
                    caption=visual_block_data['caption'],
                    position={
                        'table_index': table_data.source_info.get('table_index', 0)
                    },
                    metadata=visual_block_data['metadata'],
                    asset_path=table_image_path
                )
                
                visual_blocks.append(visual_block)
                
        except Exception as e:
            logger.error(f"Failed to extract tables from DOCX {docx_path}: {e}")
        
        return visual_blocks
    
    def _extract_docx_equations(self, docx_path: str) -> List[VisualBlock]:
        """Extract equations from DOCX files."""
        visual_blocks = []
        
        try:
            from app.core.io.docx_utils import get_docx_equation_runs
            
            for equation_text in get_docx_equation_runs(docx_path):
                if not equation_text.strip():
                    continue
                
                # Create equation visual block
                visual_block = VisualBlock(
                    visual_type='equation',
                    content={
                        'equation_text': equation_text,
                        'source': 'docx_omml'
                    },
                    caption=None,  # OMML equations typically don't have separate captions
                    position={'source': 'docx_equation_run'},
                    metadata={
                        'extraction_method': 'docx_omml',
                        'source_file': docx_path,
                        'is_structured': True
                    }
                )
                
                visual_blocks.append(visual_block)
                
        except Exception as e:
            logger.error(f"Failed to extract equations from DOCX {docx_path}: {e}")
        
        return visual_blocks
    
    def _extract_text_from_image(self, image_path: str) -> Optional[str]:
        """Extract text from image using OCR."""
        try:
            from app.core.io.ocr import extract_text_with_tesseract
            return extract_text_with_tesseract(image_path)
        except Exception as e:
            logger.warning(f"OCR failed for image {image_path}: {e}")
            return None
    
    def _detect_equation_in_image(self, image_path: Optional[str], ocr_text: Optional[str]) -> bool:
        """Detect if an image contains mathematical equations."""
        if not ocr_text:
            return False
        
        try:
            from app.core.io.ocr import detect_math_symbols
            return detect_math_symbols(ocr_text)
        except Exception as e:
            logger.warning(f"Math detection failed: {e}")
            return False
    
    def _save_image_asset(self, image_path: str) -> Optional[str]:
        """Save standalone image as asset."""
        try:
            source_path = Path(image_path)
            if not source_path.exists():
                return None
            
            # Generate asset filename
            self.extraction_counters['image'] += 1
            asset_filename = f"image_{self.extraction_counters['image']:04d}{source_path.suffix}"
            asset_path = self.assets_dir / asset_filename
            
            # Copy image to assets directory
            import shutil
            shutil.copy2(source_path, asset_path)
            
            logger.debug(f"Saved image asset: {asset_path}")
            return str(asset_path)
            
        except Exception as e:
            logger.error(f"Failed to save image asset from {image_path}: {e}")
            return None
    
    def _save_pdf_image_asset(self, image_data, pdf_path: str) -> Optional[str]:
        """Save PDF-extracted image as asset."""
        try:
            if not hasattr(image_data, 'image_bytes') or not image_data.image_bytes:
                return None
            
            # Generate asset filename
            self.extraction_counters['image'] += 1
            asset_filename = f"pdf_image_{self.extraction_counters['image']:04d}.png"
            asset_path = self.assets_dir / asset_filename
            
            # Save image bytes
            with open(asset_path, 'wb') as f:
                f.write(image_data.image_bytes)
            
            logger.debug(f"Saved PDF image asset: {asset_path}")
            return str(asset_path)
            
        except Exception as e:
            logger.error(f"Failed to save PDF image asset: {e}")
            return None
    
    def _save_docx_image_asset(self, image_data, docx_path: str) -> Optional[str]:
        """Save DOCX-extracted image as asset."""
        try:
            if not hasattr(image_data, 'image_bytes') or not image_data.image_bytes:
                return None
            
            # Generate asset filename
            self.extraction_counters['image'] += 1
            asset_filename = f"docx_image_{self.extraction_counters['image']:04d}.png"
            asset_path = self.assets_dir / asset_filename
            
            # Save image bytes
            with open(asset_path, 'wb') as f:
                f.write(image_data.image_bytes)
            
            logger.debug(f"Saved DOCX image asset: {asset_path}")
            return str(asset_path)
            
        except Exception as e:
            logger.error(f"Failed to save DOCX image asset: {e}")
            return None
    
    def _create_table_image_asset(self, table_data, source_path: str) -> Optional[str]:
        """Create visual representation of table as PNG asset."""
        try:
            from app.core.io.table_extraction import create_table_image_representation
            
            # Generate table image
            image_bytes = create_table_image_representation(table_data)
            if not image_bytes:
                return None
            
            # Generate asset filename
            self.extraction_counters['table'] += 1
            asset_filename = f"table_{self.extraction_counters['table']:04d}.png"
            asset_path = self.assets_dir / asset_filename
            
            # Save image bytes
            with open(asset_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.debug(f"Created table image asset: {asset_path}")
            return str(asset_path)
            
        except Exception as e:
            logger.error(f"Failed to create table image asset: {e}")
            return None
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about visual extraction session."""
        return {
            'counters': self.extraction_counters.copy(),
            'assets_directory': str(self.assets_dir),
            'total_assets': sum(self.extraction_counters.values())
        }


def extract_visuals_from_document(file_path: str, assets_dir: str = "data/assets") -> List[VisualBlock]:
    """
    Convenience function for extracting visuals from a single document.
    
    Args:
        file_path: Path to the document file
        assets_dir: Directory to store extracted visual assets
        
    Returns:
        List of VisualBlock objects representing extracted visual content
    """
    extractor = VisualExtractor(assets_dir=assets_dir)
    return extractor.extract_visuals_from_file(file_path)


def extract_visuals_from_documents(file_paths: List[str], assets_dir: str = "data/assets") -> Dict[str, List[VisualBlock]]:
    """
    Extract visuals from multiple documents.
    
    Args:
        file_paths: List of paths to document files
        assets_dir: Directory to store extracted visual assets
        
    Returns:
        Dict mapping file paths to lists of VisualBlock objects
    """
    extractor = VisualExtractor(assets_dir=assets_dir)
    results = {}
    
    for file_path in file_paths:
        try:
            visual_blocks = extractor.extract_visuals_from_file(file_path)
            results[file_path] = visual_blocks
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            results[file_path] = []
    
    # Log summary
    total_visuals = sum(len(blocks) for blocks in results.values())
    logger.info(f"Extracted {total_visuals} visual elements from {len(file_paths)} documents")
    
    return results