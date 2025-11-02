"""
Visual Captioning Orchestrator

Orchestrates the captioning of VisualBlock objects by integrating OCR, 
multimodal LLM APIs, and metadata enrichment.

Phase 7: Visual Captioning (Multimodal LLM Integration)
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.types import VisualBlock
from app.core.llm.model_api import generate_caption_with_openai, batch_generate_captions
from app.core.io.ocr import extract_text_with_tesseract

logger = logging.getLogger(__name__)


class VisualCaptioner:
    """
    Handles captioning of visual blocks using multimodal LLMs.
    
    Integrates OCR and visual type detection with OpenAI's GPT-5/GPT-4o
    to generate semantic captions for visual content.
    """
    
    def __init__(
        self, 
        use_batch_processing: bool = True,
        enable_ocr: bool = True,
        fallback_on_error: bool = True
    ):
        """
        Initialize the visual captioner.
        
        Args:
            use_batch_processing: Whether to process multiple visuals in batches
            enable_ocr: Whether to run OCR on images for additional context
            fallback_on_error: Whether to provide fallback captions on API errors
        """
        self.use_batch_processing = use_batch_processing
        self.enable_ocr = enable_ocr
        self.fallback_on_error = fallback_on_error
        
        logger.info(f"VisualCaptioner initialized (batch={use_batch_processing}, ocr={enable_ocr})")
    
    def caption_single_visual(self, visual_block: VisualBlock) -> VisualBlock:
        """
        Generate a caption for a single VisualBlock.
        
        Args:
            visual_block: The visual block to caption
            
        Returns:
            Updated VisualBlock with caption_text filled
        """
        if not visual_block.source_path:
            logger.warning(f"VisualBlock {visual_block.block_id} has no source_path")
            visual_block.caption_text = "Visual content (path unavailable)"
            return visual_block
        
        image_path = Path(visual_block.source_path)
        if not image_path.exists():
            logger.warning(f"Image file not found: {image_path}")
            visual_block.caption_text = f"Visual content from {image_path.name} (file not found)"
            return visual_block
        
        try:
            # Extract OCR text if enabled
            ocr_text = None
            if self.enable_ocr:
                try:
                    ocr_text = extract_text_with_tesseract(str(image_path))
                    if ocr_text:
                        logger.debug(f"Extracted OCR text for {image_path}: {ocr_text[:100]}...")
                except Exception as e:
                    logger.warning(f"OCR extraction failed for {image_path}: {e}")
            
            # Determine visual type from metadata
            visual_type = visual_block.metadata.get("visual_type") or visual_block.metadata.get("type")
            
            # Generate caption using multimodal LLM
            caption = generate_caption_with_openai(
                image_path=str(image_path),
                ocr_text=ocr_text,
                visual_type=visual_type
            )
            
            # Update the visual block
            visual_block.caption_text = caption
            
            # Add OCR text to metadata if available
            if ocr_text and ocr_text.strip():
                visual_block.metadata["ocr_text"] = ocr_text
            
            logger.info(f"Successfully captioned visual {visual_block.block_id}")
            return visual_block
            
        except Exception as e:
            error_msg = f"Failed to caption visual {visual_block.block_id}: {e}"
            logger.error(error_msg)
            
            if self.fallback_on_error:
                # Provide fallback caption
                visual_type = visual_block.metadata.get("visual_type", "figure")
                visual_block.caption_text = f"A {visual_type} related to the assignment topic"
            else:
                visual_block.caption_text = "Caption generation failed"
            
            return visual_block
    
    def caption_visual_blocks(self, visual_blocks: List[VisualBlock]) -> List[VisualBlock]:
        """
        Caption multiple VisualBlocks.
        
        Args:
            visual_blocks: List of visual blocks to caption
            
        Returns:
            List of updated VisualBlocks with captions
        """
        if not visual_blocks:
            return visual_blocks
        
        logger.info(f"Captioning {len(visual_blocks)} visual blocks")
        
        if self.use_batch_processing and len(visual_blocks) > 1:
            return self._caption_batch(visual_blocks)
        else:
            return self._caption_sequential(visual_blocks)
    
    def _caption_sequential(self, visual_blocks: List[VisualBlock]) -> List[VisualBlock]:
        """
        Caption visual blocks one by one.
        
        Args:
            visual_blocks: List of visual blocks to caption
            
        Returns:
            List of updated VisualBlocks with captions
        """
        captioned_blocks = []
        
        for visual_block in visual_blocks:
            captioned_block = self.caption_single_visual(visual_block)
            captioned_blocks.append(captioned_block)
        
        return captioned_blocks
    
    def _caption_batch(self, visual_blocks: List[VisualBlock]) -> List[VisualBlock]:
        """
        Caption visual blocks using batch processing.
        
        Args:
            visual_blocks: List of visual blocks to caption
            
        Returns:
            List of updated VisualBlocks with captions
        """
        # Prepare batch data
        image_paths = []
        ocr_texts = []
        visual_types = []
        valid_indices = []  # Track which blocks have valid paths
        
        for i, visual_block in enumerate(visual_blocks):
            if not visual_block.source_path:
                continue
                
            image_path = Path(visual_block.source_path)
            if not image_path.exists():
                continue
            
            # Extract OCR text if enabled
            ocr_text = None
            if self.enable_ocr:
                try:
                    ocr_text = extract_text_with_tesseract(str(image_path))
                except Exception as e:
                    logger.warning(f"OCR extraction failed for {image_path}: {e}")
            
            # Get visual type
            visual_type = visual_block.metadata.get("visual_type") or visual_block.metadata.get("type")
            
            image_paths.append(str(image_path))
            ocr_texts.append(ocr_text)
            visual_types.append(visual_type)
            valid_indices.append(i)
        
        # Generate captions in batch
        if image_paths:
            try:
                captions = batch_generate_captions(
                    image_paths=image_paths,
                    ocr_texts=ocr_texts,
                    visual_types=visual_types
                )
                
                # Update visual blocks with captions
                for idx, caption in zip(valid_indices, captions):
                    visual_blocks[idx].caption_text = caption
                    
                    # Add OCR text to metadata if available
                    ocr_text = ocr_texts[valid_indices.index(idx)]
                    if ocr_text and ocr_text.strip():
                        visual_blocks[idx].metadata["ocr_text"] = ocr_text
                
                logger.info(f"Successfully captioned {len(captions)} visuals in batch")
                
            except Exception as e:
                logger.error(f"Batch captioning failed: {e}")
                # Fall back to sequential processing
                return self._caption_sequential(visual_blocks)
        
        # Handle blocks that couldn't be processed in batch
        for i, visual_block in enumerate(visual_blocks):
            if i not in valid_indices:
                if self.fallback_on_error:
                    visual_type = visual_block.metadata.get("visual_type", "figure")
                    visual_block.caption_text = f"A {visual_type} related to the assignment topic"
                else:
                    visual_block.caption_text = "Caption generation failed"
        
        return visual_blocks
    
    def enrich_visual_metadata(self, visual_blocks: List[VisualBlock]) -> List[VisualBlock]:
        """
        Enrich visual blocks with additional metadata beyond captions.
        
        Args:
            visual_blocks: List of visual blocks to enrich
            
        Returns:
            List of enriched VisualBlocks
        """
        for visual_block in visual_blocks:
            try:
                # Add captioning metadata
                visual_block.metadata["captioned"] = True
                visual_block.metadata["captioning_method"] = "multimodal_llm"
                
                # Add caption length stats
                if visual_block.caption_text:
                    visual_block.metadata["caption_length"] = len(visual_block.caption_text)
                    visual_block.metadata["caption_words"] = len(visual_block.caption_text.split())
                
                # Mark as processed
                visual_block.metadata["processed_phase"] = "phase_7_captioning"
                
            except Exception as e:
                logger.warning(f"Failed to enrich metadata for visual {visual_block.block_id}: {e}")
        
        return visual_blocks


def caption_document_visuals(
    visual_blocks: List[VisualBlock],
    use_batch_processing: bool = True,
    enable_ocr: bool = True
) -> List[VisualBlock]:
    """
    Convenience function to caption all visual blocks in a document.
    
    Args:
        visual_blocks: List of visual blocks to caption
        use_batch_processing: Whether to use batch processing
        enable_ocr: Whether to extract OCR text for context
        
    Returns:
        List of captioned VisualBlocks
    """
    captioner = VisualCaptioner(
        use_batch_processing=use_batch_processing,
        enable_ocr=enable_ocr,
        fallback_on_error=True
    )
    
    # Caption the visual blocks
    captioned_blocks = captioner.caption_visual_blocks(visual_blocks)
    
    # Enrich with metadata
    enriched_blocks = captioner.enrich_visual_metadata(captioned_blocks)
    
    logger.info(f"Completed captioning {len(enriched_blocks)} visual blocks")
    
    return enriched_blocks