"""
Unified repository interface for EvalMate persistence layer.

This module provides a high-level API for storing and retrieving all domain
entities (rubrics, questions, submissions, evaluation results) that works
transparently with both JSON and SQLite backends.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.models.schemas import Rubric, Question, Submission, EvalResult
from app.core.store.backend_selector import get_backend, get_backend_name

logger = logging.getLogger(__name__)


def _deserialize_from_storage(data: Dict[str, Any], model_class) -> Any:
    """
    Helper function to deserialize data from storage, handling Pydantic model creation.
    
    This function uses Pydantic's model_validate_json to properly handle JSON-serialized
    data including enums and datetime objects that are stored as strings.
    
    Args:
        data: The raw data dictionary from storage
        model_class: The Pydantic model class to create
        
    Returns:
        Instance of the model class
    """
    try:
        # If data is already a dict from JSON parsing, we need to convert
        # it back to JSON string first, then use model_validate_json
        # which properly handles enum and datetime deserialization
        if isinstance(data, dict):
            import json
            json_str = json.dumps(data)
            return model_class.model_validate_json(json_str)
        else:
            # If it's already a JSON string
            return model_class.model_validate_json(data)
    except Exception as e:
        logger.error(f"Failed to deserialize {model_class.__name__}: {e}")
        raise
from app.core.store.backend_selector import get_backend, get_backend_name

logger = logging.getLogger(__name__)


# ---------- Rubrics ----------

def save_rubric(rubric: Rubric) -> str:
    """
    Save a Rubric to the selected backend.
    
    Args:
        rubric: The Rubric object to save
        
    Returns:
        str: The rubric ID
        
    Raises:
        RuntimeError: If the save operation fails
        
    Examples:
        >>> rubric = Rubric(id="RUB001", course="CS101", ...)
        >>> rubric_id = save_rubric(rubric)
        >>> assert rubric_id == "RUB001"
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        # Convert to dict for storage
        rubric_data = rubric.model_dump(mode='json')  # Use json mode for proper serialization
        
        if backend_name == "sqlite":
            # Extract metadata for SQLite columns
            extra_fields = {
                'course': rubric.course,
                'assignment': rubric.assignment,
                'version': rubric.version
            }
            success = backend.save_record("rubrics", rubric.id, rubric_data, **extra_fields)
            if not success:
                raise RuntimeError(f"Failed to save rubric {rubric.id} to SQLite backend")
        else:
            # JSON backend
            backend.save_record("rubrics", rubric.id, rubric_data)
        
        logger.info(f"Saved rubric {rubric.id} to {backend_name} backend")
        return rubric.id
        
    except Exception as e:
        logger.error(f"Failed to save rubric {rubric.id}: {e}")
        raise RuntimeError(f"Failed to save rubric {rubric.id}: {e}")


def list_rubrics() -> List[Dict[str, Any]]:
    """
    Return list of basic metadata for all rubrics.
    
    Returns:
        List of dictionaries with rubric metadata:
        [{'id': ..., 'course': ..., 'assignment': ..., 'version': ...}, ...]
        
    Examples:
        >>> rubrics = list_rubrics()
        >>> assert isinstance(rubrics, list)
        >>> if rubrics:
        ...     assert 'id' in rubrics[0]
        ...     assert 'course' in rubrics[0]
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        if backend_name == "sqlite":
            # Use metadata from SQLite columns
            records = backend.list_records_metadata("rubrics")
            metadata_list = []
            for record in records:
                metadata_list.append({
                    'id': record['id'],
                    'course': record['course'],
                    'assignment': record['assignment'],
                    'version': record['version'],
                    'created_at': record.get('created_at')
                })
        else:
            # JSON backend - need to load each file to get metadata
            record_ids = backend.list_records("rubrics")
            metadata_list = []
            for record_id in record_ids:
                try:
                    data = backend.load_record("rubrics", record_id)
                    metadata_list.append({
                        'id': data['id'],
                        'course': data['course'],
                        'assignment': data['assignment'],
                        'version': data['version'],
                        'created_at': data.get('created_at')
                    })
                except Exception as e:
                    logger.warning(f"Failed to load rubric metadata for {record_id}: {e}")
        
        logger.info(f"Listed {len(metadata_list)} rubrics from {backend_name} backend")
        return metadata_list
        
    except Exception as e:
        logger.error(f"Failed to list rubrics: {e}")
        return []


def get_rubric(rubric_id: str) -> Rubric:
    """
    Retrieve a Rubric by ID.
    
    Args:
        rubric_id: The unique identifier for the rubric
        
    Returns:
        Rubric: The loaded rubric object
        
    Raises:
        KeyError: If the rubric is not found
        RuntimeError: If the load operation fails
        
    Examples:
        >>> rubric = get_rubric("RUB001")
        >>> assert rubric.id == "RUB001"
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        if backend_name == "sqlite":
            data = backend.load_record("rubrics", rubric_id)
        else:
            data = backend.load_record("rubrics", rubric_id)
        
        rubric = _deserialize_from_storage(data, Rubric)
        logger.info(f"Retrieved rubric {rubric_id} from {backend_name} backend")
        return rubric
        
    except FileNotFoundError:
        raise KeyError(f"No rubric found for ID: {rubric_id}")
    except Exception as e:
        logger.error(f"Failed to retrieve rubric {rubric_id}: {e}")
        raise RuntimeError(f"Failed to retrieve rubric {rubric_id}: {e}")


# ---------- Questions ----------

def save_question(question: Question) -> str:
    """
    Save a Question and map to its rubric.
    
    Args:
        question: The Question object to save
        
    Returns:
        str: The question ID
        
    Raises:
        RuntimeError: If the save operation fails
        
    Examples:
        >>> question = Question(id="Q001", rubric_id="RUB001", ...)
        >>> question_id = save_question(question)
        >>> assert question_id == "Q001"
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        question_data = question.model_dump(mode='json')
        
        if backend_name == "sqlite":
            extra_fields = {
                'rubric_id': question.rubric_id
            }
            success = backend.save_record("questions", question.id, question_data, **extra_fields)
            if not success:
                raise RuntimeError(f"Failed to save question {question.id} to SQLite backend")
        else:
            backend.save_record("questions", question.id, question_data)
        
        logger.info(f"Saved question {question.id} to {backend_name} backend")
        return question.id
        
    except Exception as e:
        logger.error(f"Failed to save question {question.id}: {e}")
        raise RuntimeError(f"Failed to save question {question.id}: {e}")


def list_questions(rubric_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List questions; if rubric_id given, filter accordingly.
    
    Args:
        rubric_id: Optional rubric ID to filter by
        
    Returns:
        List of dictionaries with question metadata
        
    Examples:
        >>> questions = list_questions()
        >>> assert isinstance(questions, list)
        >>> questions_filtered = list_questions("RUB001")
        >>> assert isinstance(questions_filtered, list)
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        if backend_name == "sqlite":
            if rubric_id:
                records = backend.list_records_metadata("questions", "rubric_id = ?", (rubric_id,))
            else:
                records = backend.list_records_metadata("questions")
            
            metadata_list = []
            for record in records:
                metadata_list.append({
                    'id': record['id'],
                    'rubric_id': record['rubric_id'],
                    'created_at': record.get('created_at')
                })
        else:
            record_ids = backend.list_records("questions")
            metadata_list = []
            for record_id in record_ids:
                try:
                    data = backend.load_record("questions", record_id)
                    if rubric_id is None or data.get('rubric_id') == rubric_id:
                        metadata_list.append({
                            'id': data['id'],
                            'rubric_id': data['rubric_id'],
                            'created_at': data.get('created_at')
                        })
                except Exception as e:
                    logger.warning(f"Failed to load question metadata for {record_id}: {e}")
        
        logger.info(f"Listed {len(metadata_list)} questions from {backend_name} backend")
        return metadata_list
        
    except Exception as e:
        logger.error(f"Failed to list questions: {e}")
        return []


def get_question(question_id: str) -> Question:
    """
    Retrieve a Question by ID.
    
    Args:
        question_id: The unique identifier for the question
        
    Returns:
        Question: The loaded question object
        
    Raises:
        KeyError: If the question is not found
        RuntimeError: If the load operation fails
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        data = backend.load_record("questions", question_id)
        question = _deserialize_from_storage(data, Question)
        logger.info(f"Retrieved question {question_id} from {backend_name} backend")
        return question
        
    except FileNotFoundError:
        raise KeyError(f"No question found for ID: {question_id}")
    except Exception as e:
        logger.error(f"Failed to retrieve question {question_id}: {e}")
        raise RuntimeError(f"Failed to retrieve question {question_id}: {e}")


# ---------- Submissions ----------

def save_submission(submission: Submission) -> str:
    """
    Save a student Submission.
    
    Args:
        submission: The Submission object to save
        
    Returns:
        str: The submission ID
        
    Raises:
        RuntimeError: If the save operation fails
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        submission_data = submission.model_dump(mode='json')
        
        if backend_name == "sqlite":
            extra_fields = {
                'rubric_id': submission.rubric_id,
                'question_id': submission.question_id,
                'student': submission.student_handle
            }
            success = backend.save_record("submissions", submission.id, submission_data, **extra_fields)
            if not success:
                raise RuntimeError(f"Failed to save submission {submission.id} to SQLite backend")
        else:
            backend.save_record("submissions", submission.id, submission_data)
        
        logger.info(f"Saved submission {submission.id} to {backend_name} backend")
        return submission.id
        
    except Exception as e:
        logger.error(f"Failed to save submission {submission.id}: {e}")
        raise RuntimeError(f"Failed to save submission {submission.id}: {e}")


def list_submissions(rubric_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List submissions, optionally filtered by rubric.
    
    Args:
        rubric_id: Optional rubric ID to filter by
        
    Returns:
        List of dictionaries with submission metadata
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        if backend_name == "sqlite":
            if rubric_id:
                records = backend.list_records_metadata("submissions", "rubric_id = ?", (rubric_id,))
            else:
                records = backend.list_records_metadata("submissions")
            
            metadata_list = []
            for record in records:
                metadata_list.append({
                    'id': record['id'],
                    'rubric_id': record['rubric_id'],
                    'question_id': record['question_id'],
                    'student': record['student'],
                    'created_at': record.get('created_at')
                })
        else:
            record_ids = backend.list_records("submissions")
            metadata_list = []
            for record_id in record_ids:
                try:
                    data = backend.load_record("submissions", record_id)
                    if rubric_id is None or data.get('rubric_id') == rubric_id:
                        metadata_list.append({
                            'id': data['id'],
                            'rubric_id': data['rubric_id'],
                            'question_id': data['question_id'],
                            'student': data['student_handle'],
                            'created_at': data.get('created_at')
                        })
                except Exception as e:
                    logger.warning(f"Failed to load submission metadata for {record_id}: {e}")
        
        logger.info(f"Listed {len(metadata_list)} submissions from {backend_name} backend")
        return metadata_list
        
    except Exception as e:
        logger.error(f"Failed to list submissions: {e}")
        return []


def get_submission(submission_id: str) -> Submission:
    """
    Retrieve a Submission by ID.
    
    Args:
        submission_id: The unique identifier for the submission
        
    Returns:
        Submission: The loaded submission object
        
    Raises:
        KeyError: If the submission is not found
        RuntimeError: If the load operation fails
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        data = backend.load_record("submissions", submission_id)
        submission = _deserialize_from_storage(data, Submission)
        logger.info(f"Retrieved submission {submission_id} from {backend_name} backend")
        return submission
        
    except FileNotFoundError:
        raise KeyError(f"No submission found for ID: {submission_id}")
    except Exception as e:
        logger.error(f"Failed to retrieve submission {submission_id}: {e}")
        raise RuntimeError(f"Failed to retrieve submission {submission_id}: {e}")


# ---------- Evaluation Results ----------

def save_eval_result(eval_result: EvalResult) -> str:
    """
    Persist EvalResult for a submission.
    
    Args:
        eval_result: The EvalResult object to save
        
    Returns:
        str: The evaluation result ID
        
    Raises:
        RuntimeError: If the save operation fails
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        # Generate ID for EvalResult since the model doesn't have one
        from app.core.models.ids import new_eval_id
        eval_id = new_eval_id()
        
        eval_data = eval_result.model_dump(mode='json')
        
        if backend_name == "sqlite":
            extra_fields = {
                'submission_id': eval_result.submission_id,
                'rubric_id': eval_result.rubric_id
            }
            success = backend.save_record("evals", eval_id, eval_data, **extra_fields)
            if not success:
                raise RuntimeError(f"Failed to save eval result {eval_id} to SQLite backend")
        else:
            backend.save_record("evals", eval_id, eval_data)
        
        logger.info(f"Saved eval result {eval_id} to {backend_name} backend")
        return eval_id
        
    except Exception as e:
        logger.error(f"Failed to save eval result: {e}")
        raise RuntimeError(f"Failed to save eval result: {e}")


def list_eval_results(submission_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List evaluation results; optionally filter by submission.
    
    Args:
        submission_id: Optional submission ID to filter by
        
    Returns:
        List of dictionaries with evaluation result metadata
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        if backend_name == "sqlite":
            if submission_id:
                records = backend.list_records_metadata("evals", "submission_id = ?", (submission_id,))
            else:
                records = backend.list_records_metadata("evals")
            
            metadata_list = []
            for record in records:
                metadata_list.append({
                    'id': record['id'],
                    'submission_id': record['submission_id'],
                    'rubric_id': record['rubric_id'],
                    'created_at': record.get('created_at')
                })
        else:
            record_ids = backend.list_records("evals")
            metadata_list = []
            for record_id in record_ids:
                try:
                    data = backend.load_record("evals", record_id)
                    if submission_id is None or data.get('submission_id') == submission_id:
                        metadata_list.append({
                            'id': data['id'],
                            'submission_id': data['submission_id'],
                            'rubric_id': data['rubric_id'],
                            'created_at': data.get('created_at')
                        })
                except Exception as e:
                    logger.warning(f"Failed to load eval result metadata for {record_id}: {e}")
        
        logger.info(f"Listed {len(metadata_list)} eval results from {backend_name} backend")
        return metadata_list
        
    except Exception as e:
        logger.error(f"Failed to list eval results: {e}")
        return []


def get_eval_result(eval_id: str) -> EvalResult:
    """
    Fetch a specific EvalResult by ID.
    
    Args:
        eval_id: The unique identifier for the evaluation result
        
    Returns:
        EvalResult: The loaded evaluation result object
        
    Raises:
        KeyError: If the evaluation result is not found
        RuntimeError: If the load operation fails
    """
    backend = get_backend()
    backend_name = get_backend_name()
    
    try:
        data = backend.load_record("evals", eval_id)
        eval_result = _deserialize_from_storage(data, EvalResult)
        logger.info(f"Retrieved eval result {eval_id} from {backend_name} backend")
        return eval_result
        
    except FileNotFoundError:
        raise KeyError(f"No eval result found for ID: {eval_id}")
    except Exception as e:
        logger.error(f"Failed to retrieve eval result {eval_id}: {e}")
        raise RuntimeError(f"Failed to retrieve eval result {eval_id}: {e}")


# ---------- Utility Functions ----------

class Repository:
    """Repository interface that wraps the module-level functions."""
    
    def save_rubric(self, rubric: Rubric) -> str:
        """Save a rubric."""
        return save_rubric(rubric)
    
    def list_rubrics(self) -> List[Rubric]:
        """List all rubrics."""
        # Get the metadata list first
        metadata_list = list_rubrics()
        
        # Convert to full Rubric objects
        rubrics = []
        for metadata in metadata_list:
            try:
                rubric = get_rubric(metadata['id'])
                if rubric:
                    rubrics.append(rubric)
            except Exception as e:
                logger.warning(f"Failed to load rubric {metadata.get('id', 'unknown')}: {e}")
        
        return rubrics
    
    def get_rubric(self, rubric_id: str) -> Optional[Rubric]:
        """Get a rubric by ID."""
        return get_rubric(rubric_id)
    
    def save_question(self, question: Question) -> str:
        """Save a question."""
        return save_question(question)
    
    def list_questions(self) -> List[Question]:
        """List all questions."""
        return list_questions()
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a question by ID."""
        return get_question(question_id)
    
    def save_submission(self, submission: Submission) -> str:
        """Save a submission."""
        return save_submission(submission)
    
    def list_submissions(self) -> List[Submission]:
        """List all submissions."""
        return list_submissions()
    
    def get_submission(self, submission_id: str) -> Optional[Submission]:
        """Get a submission by ID."""
        return get_submission(submission_id)
    
    def save_eval_result(self, eval_result: EvalResult) -> str:
        """Save an evaluation result."""
        return save_eval_result(eval_result)
    
    def list_eval_results(self) -> List[EvalResult]:
        """List all evaluation results."""
        return list_eval_results()
    
    def get_eval_result(self, eval_id: str) -> Optional[EvalResult]:
        """Get an evaluation result by ID."""
        return get_eval_result(eval_id)


def get_repository() -> Repository:
    """
    Get a repository instance.
    
    Returns:
        Repository instance that provides access to all storage operations
    """
    return Repository()


def get_repository_info() -> Dict[str, Any]:
    """
    Get information about the current repository configuration.
    
    Returns:
        Dictionary with repository information
    """
    backend_name = get_backend_name()
    
    return {
        'backend': backend_name,
        'storage_mode': backend_name,
        'initialized': True,
        'available_backends': ['json', 'sqlite']
    }