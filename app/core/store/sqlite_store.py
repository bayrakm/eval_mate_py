"""
SQLite-based storage utilities for EvalMate.

Provides database initialization, connection management, and CRUD operations
for storing rubrics, questions, submissions, and evaluation results.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.config import DATABASE_PATH


def init_db(db_path: Union[str, Path] = None) -> None:
    """
    Initialize the SQLite database with required tables.
    
    Args:
        db_path: Optional custom database path. Uses config default if None.
        
    TODO: Add database migration system for schema updates
    TODO: Implement database versioning and backup functionality
    TODO: Add indexes for better query performance
    """
    if db_path is None:
        db_path = DATABASE_PATH
    
    db_path = Path(db_path)
    
    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create rubrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rubrics (
                    id TEXT PRIMARY KEY,
                    course TEXT NOT NULL,
                    assignment TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '1.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    json_data TEXT NOT NULL
                )
            """)
            
            # Create questions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    rubric_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    json_data TEXT NOT NULL,
                    FOREIGN KEY (rubric_id) REFERENCES rubrics (id)
                )
            """)
            
            # Create submissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY,
                    rubric_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    student TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    json_data TEXT NOT NULL,
                    FOREIGN KEY (rubric_id) REFERENCES rubrics (id),
                    FOREIGN KEY (question_id) REFERENCES questions (id)
                )
            """)
            
            # Create evals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evals (
                    id TEXT PRIMARY KEY,
                    submission_id TEXT NOT NULL,
                    rubric_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    json_data TEXT NOT NULL,
                    FOREIGN KEY (submission_id) REFERENCES submissions (id),
                    FOREIGN KEY (rubric_id) REFERENCES rubrics (id)
                )
            """)
            
            conn.commit()
            print(f" Database initialized: {db_path}")
            
    except sqlite3.Error as e:
        print(f" Database initialization error: {e}")
        raise


def get_connection(db_path: Union[str, Path] = None) -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    
    Args:
        db_path: Optional custom database path. Uses config default if None.
        
    Returns:
        SQLite connection object
        
    TODO: Implement connection pooling for better performance
    TODO: Add connection timeout and retry logic
    """
    if db_path is None:
        db_path = DATABASE_PATH
    
    try:
        # Initialize database if it doesn't exist
        if not Path(db_path).exists():
            init_db(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        print(f" Database connection error: {e}")
        raise


def insert_record(table: str, record_id: str, json_data: Dict[str, Any], **fields) -> bool:
    """
    Insert a record into the specified table.
    
    Args:
        table: Table name ('rubrics', 'questions', 'submissions', 'evals')
        record_id: Unique identifier for the record
        json_data: Dictionary containing the record data
        **fields: Additional table-specific fields
        
    Returns:
        True if record was inserted successfully, False otherwise
        
    TODO: Add conflict resolution strategies (update, ignore, fail)
    TODO: Implement batch insert functionality
    TODO: Add data validation before insertion
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert json_data to string
            json_str = json.dumps(json_data, default=str)
            
            if table == "rubrics":
                cursor.execute("""
                    INSERT INTO rubrics (id, course, assignment, version, json_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (record_id, fields.get('course', ''), fields.get('assignment', ''), 
                      fields.get('version', '1.0'), json_str))
                      
            elif table == "questions":
                cursor.execute("""
                    INSERT INTO questions (id, rubric_id, json_data)
                    VALUES (?, ?, ?)
                """, (record_id, fields.get('rubric_id', ''), json_str))
                
            elif table == "submissions":
                cursor.execute("""
                    INSERT INTO submissions (id, rubric_id, question_id, student, json_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (record_id, fields.get('rubric_id', ''), fields.get('question_id', ''),
                      fields.get('student', ''), json_str))
                      
            elif table == "evals":
                cursor.execute("""
                    INSERT INTO evals (id, submission_id, rubric_id, json_data)
                    VALUES (?, ?, ?, ?)
                """, (record_id, fields.get('submission_id', ''), fields.get('rubric_id', ''), 
                      json_str))
            else:
                raise ValueError(f"Unknown table: {table}")
            
            conn.commit()
            print(f" Record inserted into {table}: {record_id}")
            return True
            
    except (sqlite3.Error, ValueError) as e:
        print(f" Error inserting record into {table}: {e}")
        return False


def get_record(table: str, record_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a record from the specified table.
    
    Args:
        table: Table name
        record_id: Unique identifier for the record
        
    Returns:
        Dictionary containing the record data, or None if not found
        
    TODO: Add caching for frequently accessed records
    TODO: Implement partial record loading for large datasets
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            
            if row:
                # Convert Row object to dict and parse JSON data
                record = dict(row)
                record['data'] = json.loads(record['json_data'])
                del record['json_data']  # Remove raw JSON string
                return record
            else:
                print(f"  Record not found in {table}: {record_id}")
                return None
                
    except (sqlite3.Error, json.JSONDecodeError) as e:
        print(f" Error retrieving record from {table}: {e}")
        return None


def list_records(table: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    List records from the specified table.
    
    Args:
        table: Table name
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of dictionaries containing record data
        
    TODO: Add filtering and sorting options
    TODO: Implement cursor-based pagination for large datasets
    TODO: Add search functionality across JSON data
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT ? OFFSET ?", 
                          (limit, offset))
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                record = dict(row)
                record['data'] = json.loads(record['json_data'])
                del record['json_data']  # Remove raw JSON string
                records.append(record)
            
            print(f" Retrieved {len(records)} records from {table}")
            return records
            
    except (sqlite3.Error, json.JSONDecodeError) as e:
        print(f" Error listing records from {table}: {e}")
        return []


def delete_record(table: str, record_id: str) -> bool:
    """
    Delete a record from the specified table.
    
    Args:
        table: Table name
        record_id: Unique identifier for the record
        
    Returns:
        True if record was deleted successfully, False otherwise
        
    TODO: Add cascade deletion for related records
    TODO: Implement soft deletion with recovery options
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"  Record deleted from {table}: {record_id}")
                return True
            else:
                print(f"  Record not found for deletion in {table}: {record_id}")
                return False
                
    except sqlite3.Error as e:
        print(f" Error deleting record from {table}: {e}")
        return False


def get_table_count(table: str) -> int:
    """
    Get the number of records in a table.
    
    Args:
        table: Table name
        
    Returns:
        Number of records in the table
        
    TODO: Add caching for table counts
    TODO: Implement estimated counts for very large tables
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        print(f" Error getting table count for {table}: {e}")
        return 0


def save_record(category: str, obj_id: str, data: dict, **extra_fields) -> bool:
    """
    Save a record using the unified interface.
    
    Args:
        category: The category (rubrics, questions, submissions, evals)
        obj_id: The unique identifier for the object
        data: The data dictionary to save
        **extra_fields: Additional fields specific to the table
        
    Returns:
        True if record was saved successfully, False otherwise
    """
    return insert_record(category, obj_id, data, **extra_fields)


def load_record(category: str, obj_id: str) -> dict:
    """
    Load a record using the unified interface.
    
    Args:
        category: The category (rubrics, questions, submissions, evals)
        obj_id: The unique identifier for the object
        
    Returns:
        The loaded data dictionary
        
    Raises:
        KeyError: If the record is not found
    """
    record = get_record(category, obj_id)
    if record is None:
        raise KeyError(f"No record found for {obj_id} in {category}")
    return record['data']


def list_records_metadata(category: str, where_clause: str = "", params: tuple = ()) -> list[dict]:
    """
    List records with metadata using optional filtering.
    
    Args:
        category: The category table name
        where_clause: Optional WHERE clause (without 'WHERE' keyword)
        params: Parameters for the WHERE clause
        
    Returns:
        List of record dictionaries with metadata
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {category} ORDER BY created_at DESC"
            if where_clause:
                query = f"SELECT * FROM {category} WHERE {where_clause} ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                record = dict(row)
                # Parse JSON data but keep other fields
                record['data'] = json.loads(record['json_data'])
                del record['json_data']  # Remove raw JSON string
                records.append(record)
            
            return records
            
    except (sqlite3.Error, json.JSONDecodeError) as e:
        print(f" Error listing records from {category}: {e}")
        return []


def record_exists(category: str, obj_id: str) -> bool:
    """
    Check if a record exists in the given category.
    
    Args:
        category: The category table name
        obj_id: The unique identifier for the object
        
    Returns:
        True if record exists, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {category} WHERE id = ?", (obj_id,))
            return cursor.fetchone() is not None
    except sqlite3.Error:
        return False


def fetch_record(table: str, id: str) -> dict | None:
    """
    Fetch a record by ID (alias for get_record).
    
    Args:
        table: Table name
        id: Record ID
        
    Returns:
        Record dictionary or None if not found
    """
    return get_record(table, id)