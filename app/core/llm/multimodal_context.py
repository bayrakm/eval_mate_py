"""
Multimodal Context Builder

Prepares unified context combining text and visual content for later evaluation phases.
Builds structured context that can be used by evaluation LLMs in Phase 9.

Phase 7: Visual Captioning (Multimodal LLM Integration)
"""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

from app.core.types import DocBlock, VisualBlock

logger = logging.getLogger(__name__)


class MultimodalContext:
    """
    Represents a unified context combining textual and visual content.
    
    This structure prepares content for evaluation phases by organizing
    text and visual blocks into a coherent context representation.
    """
    
    def __init__(
        self,
        document_id: str,
        text_blocks: List[DocBlock],
        visual_blocks: List[VisualBlock],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize multimodal context.
        
        Args:
            document_id: Unique identifier for the document
            text_blocks: List of textual content blocks
            visual_blocks: List of visual content blocks (with captions)
            metadata: Additional context metadata
        """
        self.document_id = document_id
        self.text_blocks = text_blocks
        self.visual_blocks = visual_blocks
        self.metadata = metadata or {}
        
        # Compute summary statistics
        self._compute_stats()
    
    def _compute_stats(self):
        """Compute and store context statistics."""
        self.metadata.update({
            "total_text_blocks": len(self.text_blocks),
            "total_visual_blocks": len(self.visual_blocks),
            "total_blocks": len(self.text_blocks) + len(self.visual_blocks),
            "text_word_count": self._count_text_words(),
            "visual_caption_count": self._count_visual_words(),
            "context_creation_phase": "phase_7_multimodal"
        })
    
    def _count_text_words(self) -> int:
        """Count total words in text blocks."""
        total_words = 0
        for block in self.text_blocks:
            if hasattr(block, 'content') and block.content:
                total_words += len(block.content.split())
        return total_words
    
    def _count_visual_words(self) -> int:
        """Count total words in visual captions."""
        total_words = 0
        for block in self.visual_blocks:
            if hasattr(block, 'caption_text') and block.caption_text:
                total_words += len(block.caption_text.split())
        return total_words
    
    def get_interleaved_content(self) -> List[Dict[str, Any]]:
        """
        Get content blocks ordered by their original document position.
        
        Returns:
            List of content items with type, content, and metadata
        """
        # Combine all blocks with their page/position info
        all_blocks = []
        
        # Add text blocks
        for block in self.text_blocks:
            all_blocks.append({
                "type": "text",
                "content": getattr(block, 'content', ''),
                "page_number": getattr(block, 'page_number', 0),
                "block_id": getattr(block, 'block_id', ''),
                "metadata": getattr(block, 'metadata', {})
            })
        
        # Add visual blocks
        for block in self.visual_blocks:
            all_blocks.append({
                "type": "visual",
                "content": getattr(block, 'caption_text', ''),
                "visual_path": getattr(block, 'source_path', ''),
                "page_number": getattr(block, 'page_number', 0),
                "block_id": getattr(block, 'block_id', ''),
                "metadata": getattr(block, 'metadata', {})
            })
        
        # Sort by page number, then by block_id for stability
        all_blocks.sort(key=lambda x: (x.get('page_number', 0), x.get('block_id', '')))
        
        return all_blocks
    
    def to_text_representation(self, include_metadata: bool = False) -> str:
        """
        Convert to a text-only representation suitable for LLM evaluation.
        
        Args:
            include_metadata: Whether to include block metadata in output
            
        Returns:
            Text representation of the multimodal content
        """
        lines = []
        lines.append(f"Document: {self.document_id}")
        lines.append("=" * 50)
        
        # Get interleaved content
        content_blocks = self.get_interleaved_content()
        
        current_page = None
        for block in content_blocks:
            page_num = block.get('page_number', 0)
            
            # Add page separator if needed
            if current_page is not None and page_num != current_page:
                lines.append(f"\\n--- Page {page_num} ---\\n")
            elif current_page is None and page_num > 0:
                lines.append(f"--- Page {page_num} ---\\n")
            current_page = page_num
            
            # Add block content
            if block['type'] == 'text':
                content = block.get('content', '').strip()
                if content:
                    lines.append(content)
            
            elif block['type'] == 'visual':
                caption = block.get('content', '').strip()
                if caption:
                    lines.append(f"[VISUAL: {caption}]")
                else:
                    lines.append("[VISUAL: Figure or diagram]")
            
            # Add metadata if requested
            if include_metadata and block.get('metadata'):
                metadata_str = str(block['metadata'])
                lines.append(f"  [Metadata: {metadata_str}]")
            
            lines.append("")  # Add spacing between blocks
        
        return "\\n".join(lines)
    
    def to_structured_dict(self) -> Dict[str, Any]:
        """
        Convert to a structured dictionary representation.
        
        Returns:
            Dictionary with organized content and metadata
        """
        return {
            "document_id": self.document_id,
            "metadata": self.metadata,
            "content": {
                "text_blocks": [
                    {
                        "block_id": getattr(block, 'block_id', ''),
                        "content": getattr(block, 'content', ''),
                        "page_number": getattr(block, 'page_number', 0),
                        "metadata": getattr(block, 'metadata', {})
                    }
                    for block in self.text_blocks
                ],
                "visual_blocks": [
                    {
                        "block_id": getattr(block, 'block_id', ''),
                        "caption_text": getattr(block, 'caption_text', ''),
                        "source_path": getattr(block, 'source_path', ''),
                        "page_number": getattr(block, 'page_number', 0),
                        "metadata": getattr(block, 'metadata', {})
                    }
                    for block in self.visual_blocks
                ]
            },
            "statistics": {
                "total_blocks": self.metadata.get("total_blocks", 0),
                "text_word_count": self.metadata.get("text_word_count", 0),
                "visual_caption_count": self.metadata.get("visual_caption_count", 0)
            }
        }


class MultimodalContextBuilder:
    """
    Builder for creating MultimodalContext objects from document blocks.
    
    Handles filtering, organizing, and enriching content for evaluation phases.
    """
    
    def __init__(self, include_empty_captions: bool = True):
        """
        Initialize the context builder.
        
        Args:
            include_empty_captions: Whether to include visual blocks without captions
        """
        self.include_empty_captions = include_empty_captions
    
    def build_context(
        self,
        document_id: str,
        all_blocks: List[Union[DocBlock, VisualBlock]],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> MultimodalContext:
        """
        Build a multimodal context from mixed block types.
        
        Args:
            document_id: Unique identifier for the document
            all_blocks: List of DocBlock and VisualBlock objects
            additional_metadata: Extra metadata to include
            
        Returns:
            MultimodalContext object
        """
        # Separate text and visual blocks
        text_blocks = []
        visual_blocks = []
        
        for block in all_blocks:
            if isinstance(block, VisualBlock):
                # Filter visual blocks based on caption availability
                if self.include_empty_captions or getattr(block, 'caption_text', ''):
                    visual_blocks.append(block)
            else:
                # Assume it's a text block (DocBlock)
                text_blocks.append(block)
        
        # Prepare metadata
        metadata = additional_metadata or {}
        metadata.update({
            "builder_config": {
                "include_empty_captions": self.include_empty_captions
            }
        })
        
        # Create context
        context = MultimodalContext(
            document_id=document_id,
            text_blocks=text_blocks,
            visual_blocks=visual_blocks,
            metadata=metadata
        )
        
        logger.info(
            f"Built multimodal context for {document_id}: "
            f"{len(text_blocks)} text blocks, {len(visual_blocks)} visual blocks"
        )
        
        return context
    
    def build_from_separated_blocks(
        self,
        document_id: str,
        text_blocks: List[DocBlock],
        visual_blocks: List[VisualBlock],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> MultimodalContext:
        """
        Build context from pre-separated text and visual blocks.
        
        Args:
            document_id: Unique identifier for the document
            text_blocks: List of text content blocks
            visual_blocks: List of visual content blocks
            additional_metadata: Extra metadata to include
            
        Returns:
            MultimodalContext object
        """
        # Filter visual blocks based on caption availability
        if not self.include_empty_captions:
            visual_blocks = [
                block for block in visual_blocks 
                if getattr(block, 'caption_text', '')
            ]
        
        # Prepare metadata
        metadata = additional_metadata or {}
        metadata.update({
            "builder_config": {
                "include_empty_captions": self.include_empty_captions
            }
        })
        
        # Create context
        context = MultimodalContext(
            document_id=document_id,
            text_blocks=text_blocks,
            visual_blocks=visual_blocks,
            metadata=metadata
        )
        
        logger.info(
            f"Built multimodal context for {document_id}: "
            f"{len(text_blocks)} text blocks, {len(visual_blocks)} visual blocks"
        )
        
        return context


def create_evaluation_context(
    document_id: str,
    all_blocks: List[Union[DocBlock, VisualBlock]],
    format_type: str = "text"
) -> Union[str, Dict[str, Any]]:
    """
    Convenience function to create evaluation-ready context.
    
    Args:
        document_id: Document identifier
        all_blocks: Mixed list of content blocks
        format_type: Output format ("text" or "structured")
        
    Returns:
        Context in requested format
    """
    builder = MultimodalContextBuilder(include_empty_captions=True)
    context = builder.build_context(document_id, all_blocks)
    
    if format_type == "text":
        return context.to_text_representation(include_metadata=False)
    elif format_type == "structured":
        return context.to_structured_dict()
    else:
        raise ValueError(f"Unknown format_type: {format_type}")