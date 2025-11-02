"""
Table extraction utilities for rubric parsing and visual content processing.

Provides helpers to extract tables from DOCX and PDF documents with graceful
fallbacks when table extraction libraries are unavailable.

Extended for Phase 6: Visual Extraction with enhanced table processing capabilities.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from io import BytesIO

logger = logging.getLogger(__name__)


@dataclass
class TableFrame:
    """Simple container for tabular data."""
    headers: List[str]  # normalized lower-case headers if present; else []
    rows: List[List[str]]  # table rows as lists of cell strings


@dataclass
class EnhancedTableData:
    """
    Enhanced table representation for Phase 6 visual extraction.
    
    Attributes:
        headers: List of column headers (may be empty)
        rows: List of rows, each row is a list of cell values
        caption: Table caption if detected
        source_info: Information about source (page number, position, etc.)
        metadata: Additional metadata (formatting, cell types, etc.)
        visual_type: Type classification of the table
        quality_metrics: Quality assessment of the extracted table
    """
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None
    source_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    visual_type: Optional[str] = None
    quality_metrics: Optional[Dict[str, Any]] = None


def extract_tables_from_canonical(canonical) -> List[TableFrame]:
    """
    Try to recover tabular rubric content from a CanonicalDoc.
    
    Strategy:
      1) If original DOCX present: use python-docx to read tables directly
      2) If original PDF present: try camelot; if unavailable/fails, try tabula-py  
      3) As last resort, return [] (no tables)
    
    Args:
        canonical: CanonicalDoc object with source files information
        
    Returns:
        List of TableFrame objects containing extracted tables
    """
    tables = []
    
    # Check if we have source file references
    if not hasattr(canonical, 'source_files') or not canonical.source_files:
        logger.info("No source files referenced in canonical doc, cannot extract tables")
        return tables
    
    for source_file in canonical.source_files:
        source_path = Path(source_file)
        
        if not source_path.exists():
            logger.warning(f"Source file not found: {source_file}")
            continue
            
        if source_path.suffix.lower() == '.docx':
            logger.info(f"Extracting tables from DOCX: {source_file}")
            docx_tables = extract_tables_from_docx(str(source_path))
            tables.extend(docx_tables)
            
        elif source_path.suffix.lower() == '.pdf':
            logger.info(f"Extracting tables from PDF: {source_file}")
            pdf_tables = extract_tables_from_pdf(str(source_path))
            tables.extend(pdf_tables)
    
    logger.info(f"Extracted {len(tables)} tables from {len(canonical.source_files)} source files")
    return tables


def extract_tables_from_docx(path: str) -> List[TableFrame]:
    """
    Extract tables from a DOCX document using python-docx.
    
    Args:
        path: Path to DOCX file
        
    Returns:
        List of TableFrame objects
    """
    try:
        from docx import Document
    except ImportError:
        logger.warning("python-docx not available for DOCX table extraction")
        return []
    
    tables = []
    
    try:
        doc = Document(path)
        
        for table_idx, table in enumerate(doc.tables):
            logger.debug(f"Processing DOCX table {table_idx + 1}")
            
            # Extract table data
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    # Clean cell text
                    cell_text = cell.text.strip()
                    cell_text = ' '.join(cell_text.split())  # Normalize whitespace
                    row_data.append(cell_text)
                table_data.append(row_data)
            
            if not table_data:
                continue
                
            # Try to detect headers
            headers = []
            data_rows = table_data
            
            if table_data:
                # Check if first row looks like headers
                first_row = table_data[0]
                if _looks_like_headers(first_row):
                    headers = [h.lower().strip() for h in first_row]
                    data_rows = table_data[1:]
                    logger.debug(f"Detected headers: {headers}")
            
            if data_rows:  # Only add if we have data rows
                tables.append(TableFrame(headers=headers, rows=data_rows))
                logger.debug(f"Added DOCX table with {len(data_rows)} rows")
    
    except Exception as e:
        logger.error(f"Error extracting tables from DOCX {path}: {e}")
    
    return tables


def extract_tables_from_pdf(path: str) -> List[TableFrame]:
    """
    Extract tables from a PDF document using camelot or tabula as fallback.
    
    Args:
        path: Path to PDF file
        
    Returns:
        List of TableFrame objects
    """
    tables = []
    
    # Try camelot first
    tables = _extract_with_camelot(path)
    if tables:
        logger.info(f"Successfully extracted {len(tables)} tables using camelot")
        return tables
    
    # Fallback to tabula
    tables = _extract_with_tabula(path)
    if tables:
        logger.info(f"Successfully extracted {len(tables)} tables using tabula")
        return tables
    
    logger.warning(f"No tables could be extracted from PDF: {path}")
    return []


def _extract_with_camelot(path: str) -> List[TableFrame]:
    """Try extracting tables with camelot-py."""
    try:
        import camelot
    except ImportError:
        logger.debug("camelot-py not available")
        return []
    
    tables = []
    
    try:
        # Try stream flavor first (better for simple tables)
        camelot_tables = camelot.read_pdf(path, flavor='stream')
        logger.debug(f"Camelot stream detected {len(camelot_tables)} tables")
        
        if len(camelot_tables) == 0:
            # Try lattice flavor (better for complex tables)
            camelot_tables = camelot.read_pdf(path, flavor='lattice')
            logger.debug(f"Camelot lattice detected {len(camelot_tables)} tables")
        
        for table in camelot_tables:
            # Convert to our format
            df = table.df
            
            if df.empty:
                continue
                
            # Extract headers and data
            headers = []
            data_rows = df.values.tolist()
            
            # Check if first row looks like headers
            if len(data_rows) > 0 and _looks_like_headers(data_rows[0]):
                headers = [str(h).lower().strip() for h in data_rows[0]]
                data_rows = data_rows[1:]
            
            # Clean data rows
            cleaned_rows = []
            for row in data_rows:
                cleaned_row = [str(cell).strip() for cell in row]
                if any(cell for cell in cleaned_row):  # Skip empty rows
                    cleaned_rows.append(cleaned_row)
            
            if cleaned_rows:
                tables.append(TableFrame(headers=headers, rows=cleaned_rows))
                
    except Exception as e:
        logger.debug(f"Camelot extraction failed: {e}")
    
    return tables


def _extract_with_tabula(path: str) -> List[TableFrame]:
    """Try extracting tables with tabula-py."""
    try:
        import tabula
    except ImportError:
        logger.debug("tabula-py not available")
        return []
    
    tables = []
    
    try:
        # Extract all tables from all pages
        dfs = tabula.read_pdf(path, pages='all', multiple_tables=True)
        logger.debug(f"Tabula detected {len(dfs)} tables")
        
        for df in dfs:
            if df.empty:
                continue
                
            # Extract headers and data
            headers = []
            data_rows = df.values.tolist()
            
            # Check if first row looks like headers
            if len(data_rows) > 0 and _looks_like_headers(data_rows[0]):
                headers = [str(h).lower().strip() for h in data_rows[0]]
                data_rows = data_rows[1:]
            
            # Clean data rows
            cleaned_rows = []
            for row in data_rows:
                cleaned_row = [str(cell).strip() if str(cell) != 'nan' else '' for cell in row]
                if any(cell for cell in cleaned_row):  # Skip empty rows
                    cleaned_rows.append(cleaned_row)
            
            if cleaned_rows:
                tables.append(TableFrame(headers=headers, rows=cleaned_rows))
                
    except Exception as e:
        logger.debug(f"Tabula extraction failed: {e}")
    
    return tables


def _looks_like_headers(row: List[str]) -> bool:
    """
    Heuristic to determine if a row looks like table headers.
    
    Args:
        row: List of cell values
        
    Returns:
        True if row appears to be headers
    """
    if not row:
        return False
    
    # Header keywords that suggest this is a header row
    header_keywords = [
        'criterion', 'criteria', 'dimension', 'aspect', 'category', 'component',
        'description', 'descriptor', 'details', 'standard', 'exemplar',
        'weight', '%', 'percent', 'percentage', 'points', 'marks', 'score', 'pts',
        'type', 'level', 'grade', 'rating'
    ]
    
    # Check if any cell contains header keywords
    for cell in row:
        if cell is None or not str(cell).strip():
            continue
            
        cell_lower = str(cell).lower().strip()
        for keyword in header_keywords:
            if keyword in cell_lower:
                return True
    
    # Additional heuristics
    non_empty_cells = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
    if not non_empty_cells:
        return False
    
    # Headers often have shorter text
    avg_length = sum(len(cell) for cell in non_empty_cells) / len(non_empty_cells)
    if avg_length < 20:  # Short text suggests headers
        # Check if cells look like column names (not sentences)
        sentence_indicators = ['.', '?', '!']
        has_sentences = any(
            any(indicator in cell for indicator in sentence_indicators)
            for cell in non_empty_cells
        )
        if not has_sentences:
            return True
    
    return False


# Phase 6: Enhanced table extraction functionality

def extract_tables_with_context_pdf(pdf_path: str, page_num: Optional[int] = None) -> List[EnhancedTableData]:
    """
    Extract tables from PDF with enhanced context information for Phase 6.
    
    Args:
        pdf_path: Path to PDF file
        page_num: Specific page to extract from (0-based), or None for all pages
        
    Returns:
        List of EnhancedTableData objects with rich metadata
    """
    tables = []
    
    try:
        # Try pdfplumber first for better table detection
        tables.extend(_extract_enhanced_tables_pdfplumber(pdf_path, page_num))
        
    except Exception as e:
        logger.warning(f"pdfplumber enhanced extraction failed for {pdf_path}: {e}")
    
    # If no tables found, try camelot/tabula as fallback
    if not tables:
        try:
            legacy_tables = extract_tables_from_pdf(pdf_path)
            # Convert legacy format to enhanced format
            for i, legacy_table in enumerate(legacy_tables):
                enhanced_table = EnhancedTableData(
                    headers=legacy_table.headers,
                    rows=legacy_table.rows,
                    source_info={
                        'source': 'legacy_extraction',
                        'pdf_path': pdf_path,
                        'table_index': i
                    },
                    metadata={'extraction_method': 'legacy_fallback'}
                )
                tables.append(enhanced_table)
                
        except Exception as e:
            logger.warning(f"Legacy table extraction failed for {pdf_path}: {e}")
    
    return tables


def _extract_enhanced_tables_pdfplumber(pdf_path: str, page_num: Optional[int] = None) -> List[EnhancedTableData]:
    """Extract tables using pdfplumber with enhanced metadata."""
    tables = []
    
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_process = [pdf.pages[page_num]] if page_num is not None else pdf.pages
            
            for page_idx, page in enumerate(pages_to_process):
                actual_page_num = page_num if page_num is not None else page_idx
                
                # Extract tables from the page
                page_tables = page.extract_tables()
                
                for table_idx, table in enumerate(page_tables):
                    if not table or len(table) < 2:  # Skip empty or single-row tables
                        continue
                    
                    # Process table data
                    headers, rows = _process_table_data(table)
                    
                    # Try to find caption using nearby text
                    caption = _find_table_caption_pdf(page, table_idx)
                    
                    # Detect table type
                    table_type = _detect_table_type_from_content(headers, rows, caption)
                    
                    # Calculate quality metrics
                    quality_metrics = _calculate_table_quality(headers, rows)
                    
                    # Create enhanced table data object
                    enhanced_table = EnhancedTableData(
                        headers=headers,
                        rows=rows,
                        caption=caption,
                        source_info={
                            'source': 'pdfplumber',
                            'page': actual_page_num,
                            'table_index': table_idx,
                            'pdf_path': pdf_path,
                            'page_width': page.width,
                            'page_height': page.height
                        },
                        metadata={
                            'extraction_method': 'pdfplumber_enhanced',
                            'total_rows': len(rows),
                            'total_columns': len(headers) if headers else (len(rows[0]) if rows else 0)
                        },
                        visual_type=table_type,
                        quality_metrics=quality_metrics
                    )
                    
                    tables.append(enhanced_table)
                    
    except ImportError:
        logger.warning("pdfplumber not available for enhanced table extraction")
    except Exception as e:
        logger.error(f"Failed to extract enhanced tables with pdfplumber from {pdf_path}: {e}")
    
    return tables


def extract_tables_with_context_docx(docx_path: str) -> List[EnhancedTableData]:
    """
    Extract tables from DOCX with enhanced context information for Phase 6.
    
    Args:
        docx_path: Path to DOCX file
        
    Returns:
        List of EnhancedTableData objects with rich metadata
    """
    tables = []
    
    try:
        from app.core.io.docx_utils import iter_docx_tables
        
        for table_idx, table_data in enumerate(iter_docx_tables(docx_path)):
            if not table_data or len(table_data) < 2:  # Skip empty or single-row tables
                continue
            
            # Process table data
            headers, rows = _process_table_data(table_data)
            
            # Try to find caption
            caption = _find_table_caption_docx(docx_path, table_idx)
            
            # Detect table type
            table_type = _detect_table_type_from_content(headers, rows, caption)
            
            # Calculate quality metrics
            quality_metrics = _calculate_table_quality(headers, rows)
            
            # Create enhanced table data object
            enhanced_table = EnhancedTableData(
                headers=headers,
                rows=rows,
                caption=caption,
                source_info={
                    'source': 'docx',
                    'table_index': table_idx,
                    'docx_path': docx_path
                },
                metadata={
                    'extraction_method': 'python-docx_enhanced',
                    'total_rows': len(rows),
                    'total_columns': len(headers) if headers else (len(rows[0]) if rows else 0)
                },
                visual_type=table_type,
                quality_metrics=quality_metrics
            )
            
            tables.append(enhanced_table)
            
    except Exception as e:
        logger.error(f"Failed to extract enhanced tables from DOCX {docx_path}: {e}")
    
    return tables


def _process_table_data(table_data: List[List[str]]) -> Tuple[List[str], List[List[str]]]:
    """Process raw table data to extract headers and clean rows."""
    headers = []
    rows = []
    
    if not table_data:
        return headers, rows
    
    # Check if first row looks like headers
    first_row = table_data[0]
    if first_row and _looks_like_headers(first_row):
        headers = [str(cell).strip() if cell is not None else "" for cell in first_row]
        data_rows = table_data[1:]
    else:
        data_rows = table_data
    
    # Process data rows
    for row in data_rows:
        if row and any((str(cell).strip() if cell is not None else "") for cell in row):  # Skip completely empty rows
            processed_row = [str(cell).strip() if cell is not None else "" for cell in row]
            rows.append(processed_row)
    
    return headers, rows


def _find_table_caption_pdf(page, table_index: int) -> Optional[str]:
    """Find caption for a table in a PDF page."""
    try:
        from app.core.io.caption_heuristics import find_caption_patterns_in_text_blocks
        
        # Extract text lines from the page
        lines = page.extract_text_lines()
        
        # Convert to format expected by caption heuristics
        text_blocks = []
        for line in lines:
            text_blocks.append({'text': line.get('text', '')})
        
        # Look for table captions
        caption = find_caption_patterns_in_text_blocks(text_blocks)
        
        # Filter to only table-related captions
        if caption and 'table' in caption.lower():
            return caption
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to find table caption in PDF: {e}")
        return None


def _find_table_caption_docx(docx_path: str, table_index: int) -> Optional[str]:
    """Find caption for a table in a DOCX file."""
    try:
        from app.core.io.docx_utils import extract_docx_paragraphs_with_context, detect_figure_captions_in_docx
        
        paragraphs = extract_docx_paragraphs_with_context(docx_path)
        captions = detect_figure_captions_in_docx(paragraphs)
        
        # Look for table-specific captions
        for para_idx, caption_text in captions:
            if 'table' in caption_text.lower():
                return caption_text
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to find table caption in DOCX: {e}")
        return None


def _detect_table_type_from_content(headers: List[str], rows: List[List[str]], caption: Optional[str] = None) -> str:
    """Detect the type/purpose of a table based on its content."""
    # Analyze headers and content for patterns
    headers_text = ' '.join(headers).lower() if headers else ''
    caption_text = caption.lower() if caption else ''
    
    # Combine all text for analysis
    all_text = f"{headers_text} {caption_text}".strip()
    
    # Check for common table types
    if any(keyword in all_text for keyword in ['score', 'grade', 'points', 'marks', 'pts']):
        return 'scoring_table'
    elif any(keyword in all_text for keyword in ['criteria', 'rubric', 'assessment', 'evaluation']):
        return 'rubric_table'
    elif any(keyword in all_text for keyword in ['data', 'results', 'values', 'measurements']):
        return 'data_table'
    elif any(keyword in all_text for keyword in ['question', 'answer', 'response', 'q&a']):
        return 'qa_table'
    elif any(keyword in all_text for keyword in ['schedule', 'timeline', 'agenda', 'calendar']):
        return 'schedule_table'
    elif len(rows) <= 3 and len(headers) <= 3:
        return 'summary_table'
    else:
        return 'general_table'


def _calculate_table_quality(headers: List[str], rows: List[List[str]]) -> Dict[str, Any]:
    """Calculate quality metrics for extracted table data."""
    quality = {
        'is_valid': True,
        'issues': [],
        'quality_score': 1.0,
        'metrics': {}
    }
    
    # Check basic structure
    if not rows:
        quality['is_valid'] = False
        quality['issues'].append('Table has no data rows')
        quality['quality_score'] = 0.0
        return quality
    
    # Check row consistency
    row_lengths = [len(row) for row in rows]
    if len(set(row_lengths)) > 1:
        quality['issues'].append('Inconsistent row lengths')
        quality['quality_score'] *= 0.8
    
    # Check for mostly empty cells
    total_cells = sum(row_lengths)
    empty_cells = sum(1 for row in rows for cell in row if not cell.strip())
    empty_ratio = empty_cells / total_cells if total_cells > 0 else 1.0
    
    if empty_ratio > 0.5:
        quality['issues'].append('More than 50% empty cells')
        quality['quality_score'] *= 0.6
    
    # Check header-data consistency
    if headers:
        expected_columns = len(headers)
        if row_lengths and max(row_lengths) != expected_columns:
            quality['issues'].append('Header count does not match data columns')
            quality['quality_score'] *= 0.7
    
    # Calculate metrics
    quality['metrics'] = {
        'total_rows': len(rows),
        'total_columns': max(row_lengths) if row_lengths else 0,
        'empty_cell_ratio': empty_ratio,
        'has_headers': bool(headers),
        'consistent_structure': len(set(row_lengths)) == 1
    }
    
    return quality


def convert_enhanced_table_to_visual_block(table_data: EnhancedTableData) -> Dict[str, Any]:
    """
    Convert EnhancedTableData to VisualBlock format for Phase 6.
    
    Args:
        table_data: EnhancedTableData object to convert
        
    Returns:
        Dict representing a VisualBlock for table data
    """
    # Create structured representation
    table_structure = {
        'type': 'table',
        'headers': table_data.headers,
        'rows': table_data.rows,
        'dimensions': {
            'rows': len(table_data.rows),
            'columns': len(table_data.headers) if table_data.headers else (len(table_data.rows[0]) if table_data.rows else 0)
        }
    }
    
    # Create VisualBlock representation
    visual_block = {
        'visual_type': 'table',
        'content': table_structure,
        'caption': table_data.caption,
        'metadata': {
            'source_info': table_data.source_info or {},
            'extraction_metadata': table_data.metadata or {},
            'has_headers': bool(table_data.headers),
            'is_structured': True,
            'table_type': table_data.visual_type,
            'quality_metrics': table_data.quality_metrics or {}
        }
    }
    
    return visual_block


def create_table_image_representation(table_data: EnhancedTableData) -> Optional[bytes]:
    """
    Convert table data to a visual representation (PNG image).
    
    This is useful for creating image representations of tables
    that can be processed by image analysis tools in Phase 7/9.
    
    Args:
        table_data: EnhancedTableData object to visualize
        
    Returns:
        PNG image bytes if successful, None otherwise
    """
    try:
        # Try to use matplotlib for table visualization
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.table import Table
        
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('off')
        
        # Prepare data for matplotlib table
        if table_data.headers:
            cell_text = [table_data.headers] + table_data.rows
        else:
            cell_text = table_data.rows
        
        # Create table
        table = ax.table(
            cellText=cell_text,
            cellLoc='center',
            loc='center',
            bbox=[0, 0, 1, 1]
        )
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Highlight headers if present
        if table_data.headers:
            for i in range(len(table_data.headers)):
                table[(0, i)].set_facecolor('#40466e')
                table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Add caption if available
        if table_data.caption:
            plt.title(table_data.caption, pad=20, fontsize=12, weight='bold')
        
        # Save to bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        logger.warning("matplotlib not available for table visualization")
        return None
    except Exception as e:
        logger.error(f"Failed to convert table to image: {e}")
        return None