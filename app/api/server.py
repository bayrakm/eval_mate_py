"""FastAPI server implementation for EvalMate Phase 5 user flows."""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.api.schemas import (
    ErrorResponse,
    ListQuestionsResponse,
    ListRubricsResponse,
    ListSubmissionsResponse,
    QuestionCreateParams,
    QuestionMeta,
    QuestionResponse,
    RubricCreateParams,
    RubricMeta,
    RubricResponse,
    SubmissionCreateParams,
    SubmissionMeta,
    SubmissionResponse,
)
from app.core.io.ingest import detect_file_type, ingest_docx, ingest_image, ingest_pdf
from app.core.io.rubric_extractor import (
    extract_rubric_structured,
    rubric_items_from_extraction,
    save_rubric_json
)
from app.core.models.ids import is_valid_id, new_question_id, new_rubric_id, new_submission_id
from app.core.models.schemas import Question, Rubric, Submission
from app.core.store.repo import get_repository

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="EvalMate API",
    description="Intelligent Student Assignment Feedback System API",
    version="1.0.0",
)

# CORS middleware - allow all origins for MVP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directories
UPLOAD_BASE = Path("data/uploads")
RUBRICS_DIR = UPLOAD_BASE / "rubrics"
QUESTIONS_DIR = UPLOAD_BASE / "questions"
SUBMISSIONS_DIR = UPLOAD_BASE / "submissions"

# Ensure upload directories exist
for directory in [RUBRICS_DIR, QUESTIONS_DIR, SUBMISSIONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove directory components and dangerous characters
    clean_name = os.path.basename(filename)
    # Replace any remaining problematic characters
    clean_name = "".join(c for c in clean_name if c.isalnum() or c in "._-")
    return clean_name


def save_upload_file(upload_file: UploadFile, directory: Path) -> Path:
    """Save uploaded file to directory with unique name."""
    # Create unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = sanitize_filename(upload_file.filename or "unknown")
    unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{safe_filename}"
    
    file_path = directory / unique_filename
    
    # Write file contents
    with open(file_path, "wb") as f:
        content = upload_file.file.read()
        f.write(content)
    
    logger.info(f"Saved upload file to: {file_path}")
    return file_path


def infer_metadata_from_filename(filename: str) -> dict:
    """Infer course/assignment metadata from filename stem."""
    stem = Path(filename).stem
    
    # Try to parse patterns like "CS101_A1" or "CS101-A1" or "CS101 A1"
    parts = stem.replace("_", " ").replace("-", " ").split()
    
    if len(parts) >= 2:
        return {
            "course": parts[0],
            "assignment": parts[1],
        }
    elif len(parts) == 1:
        return {
            "course": parts[0],
            "assignment": "ASSIGNMENT",
        }
    else:
        return {
            "course": "COURSE",
            "assignment": "ASSIGNMENT",
        }


# Rubrics endpoints
@app.post("/rubrics/upload", response_model=RubricResponse)
async def upload_rubric(
    file: UploadFile = File(...),
    params: Optional[str] = Form(None)
):
    """Upload and parse a rubric file."""
    try:
        # Parse optional parameters
        create_params = RubricCreateParams()
        if params:
            try:
                param_dict = json.loads(params)
                create_params = RubricCreateParams(**param_dict)
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid params JSON: {e}"
                )
        
        # Save uploaded file
        file_path = save_upload_file(file, RUBRICS_DIR)
        
        # Detect file type and ingest
        file_type = detect_file_type(str(file_path))
        logger.info(f"Detected file type: {file_type}")
        
        if file_type == "pdf":
            canonical_doc = ingest_pdf(str(file_path))
        elif file_type == "docx":
            canonical_doc = ingest_docx(str(file_path))
        elif file_type == "image":
            canonical_doc = ingest_image(str(file_path))
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type: {file_type}"
            )
        
        logger.info(f"Ingested document with {len(canonical_doc.blocks)} blocks")
        
        # Parse rubric items via ADE
        rubric_data = extract_rubric_structured(str(file_path))
        rubric_items = rubric_items_from_extraction(rubric_data)
        
        if not rubric_items:
            # This shouldn't happen with Phase 4 fallbacks, but just in case
            raise HTTPException(
                status_code=422,
                detail="No rubric items could be parsed from the document"
            )
        
        logger.info(f"Parsed {len(rubric_items)} rubric items")

        # Save extracted rubric JSON for reuse
        try:
            saved_path = save_rubric_json(rubric_data)
            logger.info(f"Saved rubric extraction JSON to: {saved_path}")
        except Exception as e:
            logger.warning(f"Failed to save rubric extraction JSON: {e}")
        
        # Determine metadata
        metadata = {}
        if create_params.course:
            metadata["course"] = create_params.course
        if create_params.assignment:
            metadata["assignment"] = create_params.assignment
        metadata["version"] = create_params.version
        
        # Infer missing metadata from filename
        if not metadata.get("course") or not metadata.get("assignment"):
            inferred = infer_metadata_from_filename(file.filename or "unknown")
            metadata.setdefault("course", rubric_data.get("course") or inferred["course"])
            metadata.setdefault("assignment", inferred["assignment"])
        
        # Create rubric
        rubric = Rubric(
            id=new_rubric_id(),
            course=metadata["course"],
            assignment=metadata["assignment"],
            version=metadata["version"],
            items=rubric_items,
            canonical=canonical_doc
        )
        
        # Save to repository
        repo = get_repository()
        repo.save_rubric(rubric)
        
        logger.info(f"Saved rubric with ID: {rubric.id}")
        
        return RubricResponse(
            meta=RubricMeta(
                id=rubric.id,
                course=rubric.course,
                assignment=rubric.assignment,
                version=rubric.version
            ),
            item_count=len(rubric.items)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading rubric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rubrics", response_model=ListRubricsResponse)
async def list_rubrics():
    """List all rubrics."""
    try:
        repo = get_repository()
        rubrics = repo.list_rubrics()
        
        return ListRubricsResponse(
            items=[
                RubricMeta(
                    id=rubric.id,
                    course=rubric.course,
                    assignment=rubric.assignment,
                    version=rubric.version
                )
                for rubric in rubrics
            ]
        )
    except Exception as e:
        logger.error(f"Error listing rubrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rubrics/{rubric_id}")
async def get_rubric(rubric_id: str):
    """Get full rubric by ID."""
    try:
        if not is_valid_id(rubric_id):
            raise HTTPException(status_code=422, detail="Invalid rubric ID format")
        
        repo = get_repository()
        rubric = repo.get_rubric(rubric_id)
        
        if not rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        
        return rubric.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rubric {rubric_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Questions endpoints
@app.post("/questions/upload", response_model=QuestionResponse)
async def upload_question(
    file: UploadFile = File(...),
    params: str = Form(...)
):
    """Upload and parse a question file."""
    try:
        # Parse required parameters
        try:
            param_dict = json.loads(params)
            create_params = QuestionCreateParams(**param_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid params JSON: {e}"
            )
        
        # Validate rubric exists
        if not is_valid_id(create_params.rubric_id):
            raise HTTPException(status_code=422, detail="Invalid rubric ID format")
        
        repo = get_repository()
        rubric = repo.get_rubric(create_params.rubric_id)
        if not rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        
        # Save uploaded file
        file_path = save_upload_file(file, QUESTIONS_DIR)
        
        # Detect file type and ingest
        file_type = detect_file_type(str(file_path))
        logger.info(f"Detected file type: {file_type}")
        
        if file_type == "pdf":
            canonical_doc = ingest_pdf(str(file_path))
        elif file_type == "docx":
            canonical_doc = ingest_docx(str(file_path))
        elif file_type == "image":
            canonical_doc = ingest_image(str(file_path))
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type: {file_type}"
            )
        
        logger.info(f"Ingested question document with {len(canonical_doc.blocks)} blocks")
        
        # Determine title
        title = create_params.title
        if not title:
            title = Path(file.filename or "unknown").stem
        
        # Create question
        question = Question(
            id=new_question_id(),
            title=title,
            rubric_id=create_params.rubric_id,
            canonical=canonical_doc
        )
        
        # Save to repository
        repo.save_question(question)
        
        logger.info(f"Saved question with ID: {question.id}")
        
        return QuestionResponse(
            meta=QuestionMeta(
                id=question.id,
                title=question.title,
                rubric_id=question.rubric_id
            ),
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions", response_model=ListQuestionsResponse)
async def list_questions(rubric_id: Optional[str] = None):
    """List questions, optionally filtered by rubric."""
    try:
        repo = get_repository()
        questions = repo.list_questions()
        
        # Apply rubric filter if provided
        if rubric_id:
            if not is_valid_id(rubric_id):
                raise HTTPException(status_code=422, detail="Invalid rubric ID format")
            questions = [q for q in questions if q.rubric_id == rubric_id]
        
        return ListQuestionsResponse(
            items=[
                QuestionMeta(
                    id=question.id,
                    title=question.title,
                    rubric_id=question.rubric_id
                )
                for question in questions
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions/{question_id}")
async def get_question(question_id: str):
    """Get full question by ID."""
    try:
        if not is_valid_id(question_id):
            raise HTTPException(status_code=422, detail="Invalid question ID format")
        
        repo = get_repository()
        question = repo.get_question(question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        return question.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question {question_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Submissions endpoints
@app.post("/submissions/upload", response_model=SubmissionResponse)
async def upload_submission(
    file: UploadFile = File(...),
    params: str = Form(...)
):
    """Upload and parse a submission file."""
    try:
        # Parse required parameters
        try:
            param_dict = json.loads(params)
            create_params = SubmissionCreateParams(**param_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid params JSON: {e}"
            )
        
        # Validate rubric and question exist
        if not is_valid_id(create_params.rubric_id):
            raise HTTPException(status_code=422, detail="Invalid rubric ID format")
        if not is_valid_id(create_params.question_id):
            raise HTTPException(status_code=422, detail="Invalid question ID format")
        
        repo = get_repository()
        
        rubric = repo.get_rubric(create_params.rubric_id)
        if not rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        
        question = repo.get_question(create_params.question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Save uploaded file
        file_path = save_upload_file(file, SUBMISSIONS_DIR)
        
        # Detect file type and ingest
        file_type = detect_file_type(str(file_path))
        logger.info(f"Detected file type: {file_type}")
        
        if file_type == "pdf":
            canonical_doc = ingest_pdf(str(file_path))
        elif file_type == "docx":
            canonical_doc = ingest_docx(str(file_path))
        elif file_type == "image":
            canonical_doc = ingest_image(str(file_path))
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type: {file_type}"
            )
        
        logger.info(f"Ingested submission document with {len(canonical_doc.blocks)} blocks")
        
        # Create submission
        submission = Submission(
            id=new_submission_id(),
            rubric_id=create_params.rubric_id,
            question_id=create_params.question_id,
            student_handle=create_params.student_handle,
            canonical=canonical_doc
        )
        
        # Save to repository
        repo.save_submission(submission)
        
        logger.info(f"Saved submission with ID: {submission.id}")
        
        return SubmissionResponse(
            meta=SubmissionMeta(
                id=submission.id,
                rubric_id=submission.rubric_id,
                question_id=submission.question_id,
                student_handle=submission.student_handle
            ),
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submissions", response_model=ListSubmissionsResponse)
async def list_submissions(
    rubric_id: Optional[str] = None,
    question_id: Optional[str] = None,
    student_handle: Optional[str] = None
):
    """List submissions with optional filters."""
    try:
        repo = get_repository()
        submissions = repo.list_submissions()
        
        # Apply filters if provided
        if rubric_id:
            if not is_valid_id(rubric_id):
                raise HTTPException(status_code=422, detail="Invalid rubric ID format")
            submissions = [s for s in submissions if s.rubric_id == rubric_id]
        
        if question_id:
            if not is_valid_id(question_id):
                raise HTTPException(status_code=422, detail="Invalid question ID format")
            submissions = [s for s in submissions if s.question_id == question_id]
        
        if student_handle:
            submissions = [s for s in submissions if s.student_handle == student_handle]
        
        return ListSubmissionsResponse(
            items=[
                SubmissionMeta(
                    id=submission.id,
                    rubric_id=submission.rubric_id,
                    question_id=submission.question_id,
                    student_handle=submission.student_handle
                )
                for submission in submissions
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing submissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submissions/{submission_id}")
async def get_submission(submission_id: str):
    """Get full submission by ID."""
    try:
        if not is_valid_id(submission_id):
            raise HTTPException(status_code=422, detail="Invalid submission ID format")
        
        repo = get_repository()
        submission = repo.get_submission(submission_id)
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return submission.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting submission {submission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include fusion routes
from app.api import fusion_routes
app.include_router(fusion_routes.router)

# Include evaluation routes
from app.api import evaluate_routes
app.include_router(evaluate_routes.router)

# Include chat routes
from app.api import chat_routes
app.include_router(chat_routes.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
