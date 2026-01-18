"""
JSON-based storage utilities for EvalMate.

Provides functions for saving, loading, and managing JSON files
with proper error handling and directory management.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Union

from app.config import DIRECTORIES


def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save a dictionary as a JSON file.
    
    Args:
        data: Dictionary to save as JSON
        file_path: Path where the JSON file should be saved
        
    Raises:
        OSError: If the file cannot be written
        TypeError: If data cannot be serialized to JSON
        
    TODO: Add atomic write operations for data integrity
    TODO: Implement JSON schema validation
    TODO: Add compression support for large files
    """
    file_path = Path(file_path)
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"JSON saved to: {file_path}")
    except (OSError, TypeError) as e:
        print(f"Error saving JSON to {file_path}: {e}")
        raise


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return as a dictionary.
    
    Args:
        file_path: Path to the JSON file to load
        
    Returns:
        Dictionary containing the JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        
    TODO: Add JSON schema validation on load
    TODO: Implement caching for frequently accessed files
    TODO: Add support for streaming large JSON files
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"JSON loaded from: {file_path}")
        return data
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {file_path}: {e}")
        raise
    except OSError as e:
        print(f"Error reading JSON from {file_path}: {e}")
        raise


def list_json_files(directory_path: Union[str, Path]) -> List[str]:
    """
    List all JSON files in a directory.
    
    Args:
        directory_path: Path to the directory to search
        
    Returns:
        List of JSON file paths (as strings) found in the directory
        
    TODO: Add recursive directory search option
    TODO: Implement file filtering by patterns or metadata
    TODO: Add sorting options (by name, date, size)
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        print(f"Directory not found: {directory_path}")
        return []
    
    if not directory_path.is_dir():
        print(f"Path is not a directory: {directory_path}")
        return []
    
    try:
        json_files = [
            str(file_path) 
            for file_path in directory_path.iterdir() 
            if file_path.is_file() and file_path.suffix.lower() == '.json'
        ]
        
        json_files.sort()  # Sort alphabetically
        print(f"Found {len(json_files)} JSON files in: {directory_path}")
        return json_files
        
    except OSError as e:
        print(f"Error listing directory {directory_path}: {e}")
        return []


def file_exists(file_path: Union[str, Path]) -> bool:
    """
    Check if a JSON file exists.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file exists and is a file, False otherwise
        
    TODO: Add validation to ensure file is valid JSON
    TODO: Implement file integrity checks
    """
    return Path(file_path).is_file()


def delete_json(file_path: Union[str, Path]) -> bool:
    """
    Delete a JSON file safely.
    
    Args:
        file_path: Path to the JSON file to delete
        
    Returns:
        True if file was deleted successfully, False otherwise
        
    TODO: Add backup functionality before deletion
    TODO: Implement secure deletion for sensitive data
    """
    file_path = Path(file_path)
    
    try:
        if file_path.exists():
            file_path.unlink()
            print(f"Deleted JSON file: {file_path}")
            return True
        else:
            print(f"File not found for deletion: {file_path}")
            return False
    except OSError as e:
        print(f"Error deleting JSON file {file_path}: {e}")
        return False


def save_record(category: str, obj_id: str, data: dict) -> None:
    """
    Save a record to the appropriate JSON file with atomic write operation.
    
    Args:
        category: The category (rubrics, questions, submissions, evals)
        obj_id: The unique identifier for the object
        data: The data dictionary to save
        
    Raises:
        OSError: If the file cannot be written
        ValueError: If category is invalid
    """
    if category not in DIRECTORIES:
        raise ValueError(f"Invalid category: {category}")
    
    file_path = DIRECTORIES[category] / f"{obj_id}.json"
    
    # Atomic write using temporary file
    temp_path = None
    try:
        # Create temporary file in the same directory
        with tempfile.NamedTemporaryFile(
            mode='w', 
            encoding='utf-8', 
            dir=file_path.parent, 
            delete=False,
            suffix='.tmp'
        ) as temp_file:
            temp_path = temp_file.name
            json.dump(data, temp_file, indent=2, ensure_ascii=False, default=str)
        
        # Atomically replace the target file
        os.replace(temp_path, file_path)
        print(f"Record saved to {category}: {obj_id}")
        
    except Exception as e:
        # Clean up temporary file if it exists
        if temp_path and Path(temp_path).exists():
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        print(f"Error saving record to {category}: {e}")
        raise


def load_record(category: str, obj_id: str) -> dict:
    """
    Load a record from the appropriate JSON file.
    
    Args:
        category: The category (rubrics, questions, submissions, evals)
        obj_id: The unique identifier for the object
        
    Returns:
        The loaded data dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If category is invalid
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if category not in DIRECTORIES:
        raise ValueError(f"Invalid category: {category}")
    
    file_path = DIRECTORIES[category] / f"{obj_id}.json"
    return load_json(file_path)


def list_records(category: str) -> list[str]:
    """
    List all record IDs in a category.
    
    Args:
        category: The category (rubrics, questions, submissions, evals)
        
    Returns:
        List of record IDs (filenames without .json extension)
        
    Raises:
        ValueError: If category is invalid
    """
    if category not in DIRECTORIES:
        raise ValueError(f"Invalid category: {category}")
    
    directory_path = DIRECTORIES[category]
    
    if not directory_path.exists():
        return []
    
    try:
        record_ids = [
            file_path.stem  # filename without extension
            for file_path in directory_path.iterdir()
            if file_path.is_file() and file_path.suffix.lower() == '.json'
        ]
        
        record_ids.sort()  # Sort alphabetically
        return record_ids
        
    except OSError as e:
        print(f"Error listing records in {category}: {e}")
        return []


def record_exists(category: str, obj_id: str) -> bool:
    """
    Check if a record exists in the given category.
    
    Args:
        category: The category (rubrics, questions, submissions, evals)
        obj_id: The unique identifier for the object
        
    Returns:
        True if record exists, False otherwise
    """
    if category not in DIRECTORIES:
        return False
    
    file_path = DIRECTORIES[category] / f"{obj_id}.json"
    return file_path.is_file()


def delete_record(category: str, obj_id: str) -> bool:
    """
    Delete a record from the given category.
    
    Args:
        category: The category (rubrics, questions, submissions, evals)
        obj_id: The unique identifier for the object
        
    Returns:
        True if record was deleted successfully, False otherwise
    """
    if category not in DIRECTORIES:
        return False
    
    file_path = DIRECTORIES[category] / f"{obj_id}.json"
    return delete_json(file_path)
