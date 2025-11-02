"""Typer CLI interface for EvalMate management operations."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from app.core.io.ingest import detect_file_type, ingest_docx, ingest_image, ingest_pdf
from app.core.io.rubric_parser import ParseConfig, parse_rubric_to_items
from app.core.models.ids import is_valid_id, new_question_id, new_rubric_id, new_submission_id
from app.core.models.schemas import Question, Rubric, Submission
from app.core.store.repo import get_repository

app = typer.Typer(help="EvalMate - Intelligent Student Assignment Feedback System")
console = Console()

# Sub-applications for different entity types
rubrics_app = typer.Typer(help="Rubric management commands")
questions_app = typer.Typer(help="Question management commands")
submissions_app = typer.Typer(help="Submission management commands")

app.add_typer(rubrics_app, name="rubrics")
app.add_typer(questions_app, name="questions") 
app.add_typer(submissions_app, name="submissions")


def handle_error(operation: str, error: Exception):
    """Handle and display errors consistently."""
    console.print(f"[red]Error {operation}: {error}[/red]")
    sys.exit(1)


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


# Rubrics commands
@rubrics_app.command("upload")
def upload_rubric(
    file: Path = typer.Option(..., "--file", "-f", help="Path to rubric file (PDF/DOCX/Image)"),
    course: Optional[str] = typer.Option(None, "--course", "-c", help="Course identifier"),
    assignment: Optional[str] = typer.Option(None, "--assignment", "-a", help="Assignment identifier"),
    version: str = typer.Option("v1", "--version", "-v", help="Rubric version"),
    prefer_tables: bool = typer.Option(True, "--prefer-tables/--no-prefer-tables", help="Prefer table parsing")
):
    """Upload and parse a rubric file."""
    try:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            sys.exit(1)
        
        # Detect file type and ingest
        file_type = detect_file_type(str(file))
        console.print(f"Detected file type: [blue]{file_type}[/blue]")
        
        if file_type == "pdf":
            canonical_doc = ingest_pdf(str(file))
        elif file_type == "docx":
            canonical_doc = ingest_docx(str(file))
        elif file_type == "image":
            canonical_doc = ingest_image(str(file))
        else:
            console.print(f"[red]Unsupported file type: {file_type}[/red]")
            sys.exit(1)
        
        console.print(f"Ingested document with [green]{len(canonical_doc.blocks)}[/green] blocks")
        
        # Parse rubric items
        parse_config = ParseConfig(prefer_tables=prefer_tables)
        rubric_items = parse_rubric_to_items(canonical_doc, parse_config)
        
        if not rubric_items:
            console.print("[red]No rubric items could be parsed from the document[/red]")
            sys.exit(1)
        
        console.print(f"Parsed [green]{len(rubric_items)}[/green] rubric items")
        
        # Determine metadata
        metadata = {
            "course": course,
            "assignment": assignment,
            "version": version
        }
        
        # Infer missing metadata from filename
        if not metadata["course"] or not metadata["assignment"]:
            inferred = infer_metadata_from_filename(file.name)
            metadata["course"] = metadata["course"] or inferred["course"]
            metadata["assignment"] = metadata["assignment"] or inferred["assignment"]
        
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
        
        console.print(f"✅ Saved rubric with ID: [green]{rubric.id}[/green]")
        console.print(f"   Course: {rubric.course}")
        console.print(f"   Assignment: {rubric.assignment}")
        console.print(f"   Version: {rubric.version}")
        console.print(f"   Items: {len(rubric.items)}")
        
    except Exception as e:
        handle_error("uploading rubric", e)


@rubrics_app.command("list")
def list_rubrics():
    """List all rubrics."""
    try:
        repo = get_repository()
        rubrics = repo.list_rubrics()
        
        if not rubrics:
            console.print("No rubrics found.")
            return
        
        table = Table(title="Rubrics")
        table.add_column("ID", style="cyan")
        table.add_column("Course", style="green")
        table.add_column("Assignment", style="blue")
        table.add_column("Version", style="yellow")
        table.add_column("Items", style="magenta")
        
        for rubric in rubrics:
            table.add_row(
                rubric.id,
                rubric.course,
                rubric.assignment,
                rubric.version,
                str(len(rubric.items))
            )
        
        console.print(table)
        
    except Exception as e:
        handle_error("listing rubrics", e)


@rubrics_app.command("get")
def get_rubric(
    id: str = typer.Option(..., "--id", "-i", help="Rubric ID")
):
    """Get full rubric details by ID."""
    try:
        if not is_valid_id(id):
            console.print(f"[red]Invalid rubric ID format: {id}[/red]")
            sys.exit(1)
        
        repo = get_repository()
        rubric = repo.get_rubric(id)
        
        if not rubric:
            console.print(f"[red]Rubric not found: {id}[/red]")
            sys.exit(1)
        
        console.print(f"[bold]Rubric: {rubric.course} - {rubric.assignment} ({rubric.version})[/bold]")
        console.print(f"ID: [cyan]{rubric.id}[/cyan]")
        console.print(f"Created: Available via repository")
        console.print(f"Document blocks: {len(rubric.canonical.blocks)}")
        console.print(f"\n[bold]Rubric Items ({len(rubric.items)}):[/bold]")
        
        for i, item in enumerate(rubric.items, 1):
            console.print(f"  {i}. [green]{item.title}[/green] ({item.weight:.1%})")
            console.print(f"     {item.description}")
            console.print(f"     Criterion: [blue]{item.criterion.value}[/blue]")
        
    except Exception as e:
        handle_error("getting rubric", e)


# Questions commands
@questions_app.command("upload")
def upload_question(
    file: Path = typer.Option(..., "--file", "-f", help="Path to question file (PDF/DOCX/Image)"),
    rubric_id: str = typer.Option(..., "--rubric-id", "-r", help="Rubric ID to associate with"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Question title")
):
    """Upload and parse a question file."""
    try:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            sys.exit(1)
        
        if not is_valid_id(rubric_id):
            console.print(f"[red]Invalid rubric ID format: {rubric_id}[/red]")
            sys.exit(1)
        
        # Validate rubric exists
        repo = get_repository()
        rubric = repo.get_rubric(rubric_id)
        if not rubric:
            console.print(f"[red]Rubric not found: {rubric_id}[/red]")
            sys.exit(1)
        
        # Detect file type and ingest
        file_type = detect_file_type(str(file))
        console.print(f"Detected file type: [blue]{file_type}[/blue]")
        
        if file_type == "pdf":
            canonical_doc = ingest_pdf(str(file))
        elif file_type == "docx":
            canonical_doc = ingest_docx(str(file))
        elif file_type == "image":
            canonical_doc = ingest_image(str(file))
        else:
            console.print(f"[red]Unsupported file type: {file_type}[/red]")
            sys.exit(1)
        
        console.print(f"Ingested document with [green]{len(canonical_doc.blocks)}[/green] blocks")
        
        # Determine title
        question_title = title or file.stem
        
        # Create question
        question = Question(
            id=new_question_id(),
            title=question_title,
            rubric_id=rubric_id,
            canonical=canonical_doc
        )
        
        # Save to repository
        repo.save_question(question)
        
        console.print(f"✅ Saved question with ID: [green]{question.id}[/green]")
        console.print(f"   Title: {question.title}")
        console.print(f"   Rubric: {rubric_id}")
        
    except Exception as e:
        handle_error("uploading question", e)


@questions_app.command("list")
def list_questions(
    rubric_id: Optional[str] = typer.Option(None, "--rubric-id", "-r", help="Filter by rubric ID")
):
    """List questions, optionally filtered by rubric."""
    try:
        repo = get_repository()
        questions = repo.list_questions()
        
        # Apply rubric filter if provided
        if rubric_id:
            if not is_valid_id(rubric_id):
                console.print(f"[red]Invalid rubric ID format: {rubric_id}[/red]")
                sys.exit(1)
            questions = [q for q in questions if q.rubric_id == rubric_id]
        
        if not questions:
            filter_msg = f" for rubric {rubric_id}" if rubric_id else ""
            console.print(f"No questions found{filter_msg}.")
            return
        
        table = Table(title="Questions")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Rubric ID", style="blue")
        table.add_column("Created", style="yellow")
        
        for question in questions:
            table.add_row(
                question.id,
                question.title,
                question.rubric_id,
                "Available via repo"
            )
        
        console.print(table)
        
    except Exception as e:
        handle_error("listing questions", e)


@questions_app.command("get")
def get_question(
    id: str = typer.Option(..., "--id", "-i", help="Question ID")
):
    """Get full question details by ID."""
    try:
        if not is_valid_id(id):
            console.print(f"[red]Invalid question ID format: {id}[/red]")
            sys.exit(1)
        
        repo = get_repository()
        question = repo.get_question(id)
        
        if not question:
            console.print(f"[red]Question not found: {id}[/red]")
            sys.exit(1)
        
        console.print(f"[bold]Question: {question.title}[/bold]")
        console.print(f"ID: [cyan]{question.id}[/cyan]")
        console.print(f"Rubric ID: [blue]{question.rubric_id}[/blue]")
        console.print(f"Created: Available via repository")
        console.print(f"Document blocks: {len(question.canonical.blocks)}")
        
    except Exception as e:
        handle_error("getting question", e)


# Submissions commands
@submissions_app.command("upload")
def upload_submission(
    file: Path = typer.Option(..., "--file", "-f", help="Path to submission file (PDF/DOCX/Image)"),
    rubric_id: str = typer.Option(..., "--rubric-id", "-r", help="Rubric ID"),
    question_id: str = typer.Option(..., "--question-id", "-q", help="Question ID"),
    student: str = typer.Option(..., "--student", "-s", help="Student handle/identifier")
):
    """Upload and parse a submission file."""
    try:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            sys.exit(1)
        
        if not is_valid_id(rubric_id):
            console.print(f"[red]Invalid rubric ID format: {rubric_id}[/red]")
            sys.exit(1)
        
        if not is_valid_id(question_id):
            console.print(f"[red]Invalid question ID format: {question_id}[/red]")
            sys.exit(1)
        
        # Validate rubric and question exist
        repo = get_repository()
        
        rubric = repo.get_rubric(rubric_id)
        if not rubric:
            console.print(f"[red]Rubric not found: {rubric_id}[/red]")
            sys.exit(1)
        
        question = repo.get_question(question_id)
        if not question:
            console.print(f"[red]Question not found: {question_id}[/red]")
            sys.exit(1)
        
        # Detect file type and ingest
        file_type = detect_file_type(str(file))
        console.print(f"Detected file type: [blue]{file_type}[/blue]")
        
        if file_type == "pdf":
            canonical_doc = ingest_pdf(str(file))
        elif file_type == "docx":
            canonical_doc = ingest_docx(str(file))
        elif file_type == "image":
            canonical_doc = ingest_image(str(file))
        else:
            console.print(f"[red]Unsupported file type: {file_type}[/red]")
            sys.exit(1)
        
        console.print(f"Ingested document with [green]{len(canonical_doc.blocks)}[/green] blocks")
        
        # Create submission
        submission = Submission(
            id=new_submission_id(),
            rubric_id=rubric_id,
            question_id=question_id,
            student_handle=student,
            canonical=canonical_doc
        )
        
        # Save to repository
        repo.save_submission(submission)
        
        console.print(f"✅ Saved submission with ID: [green]{submission.id}[/green]")
        console.print(f"   Student: {submission.student_handle}")
        console.print(f"   Rubric: {rubric_id}")
        console.print(f"   Question: {question_id}")
        
    except Exception as e:
        handle_error("uploading submission", e)


@submissions_app.command("list")
def list_submissions(
    rubric_id: Optional[str] = typer.Option(None, "--rubric-id", "-r", help="Filter by rubric ID"),
    question_id: Optional[str] = typer.Option(None, "--question-id", "-q", help="Filter by question ID"),
    student: Optional[str] = typer.Option(None, "--student", "-s", help="Filter by student handle")
):
    """List submissions with optional filters."""
    try:
        repo = get_repository()
        submissions = repo.list_submissions()
        
        # Apply filters if provided
        if rubric_id:
            if not is_valid_id(rubric_id):
                console.print(f"[red]Invalid rubric ID format: {rubric_id}[/red]")
                sys.exit(1)
            submissions = [s for s in submissions if s.rubric_id == rubric_id]
        
        if question_id:
            if not is_valid_id(question_id):
                console.print(f"[red]Invalid question ID format: {question_id}[/red]")
                sys.exit(1)
            submissions = [s for s in submissions if s.question_id == question_id]
        
        if student:
            submissions = [s for s in submissions if s.student_handle == student]
        
        if not submissions:
            console.print("No submissions found with the specified filters.")
            return
        
        table = Table(title="Submissions")
        table.add_column("ID", style="cyan")
        table.add_column("Student", style="green")
        table.add_column("Rubric ID", style="blue")
        table.add_column("Question ID", style="yellow")
        table.add_column("Created", style="magenta")
        
        for submission in submissions:
            table.add_row(
                submission.id,
                submission.student_handle,
                submission.rubric_id,
                submission.question_id,
                "Available via repo"
            )
        
        console.print(table)
        
    except Exception as e:
        handle_error("listing submissions", e)


@submissions_app.command("get")
def get_submission(
    id: str = typer.Option(..., "--id", "-i", help="Submission ID")
):
    """Get full submission details by ID."""
    try:
        if not is_valid_id(id):
            console.print(f"[red]Invalid submission ID format: {id}[/red]")
            sys.exit(1)
        
        repo = get_repository()
        submission = repo.get_submission(id)
        
        if not submission:
            console.print(f"[red]Submission not found: {id}[/red]")
            sys.exit(1)
        
        console.print(f"[bold]Submission: {submission.student_handle}[/bold]")
        console.print(f"ID: [cyan]{submission.id}[/cyan]")
        console.print(f"Student: [green]{submission.student_handle}[/green]")
        console.print(f"Rubric ID: [blue]{submission.rubric_id}[/blue]")
        console.print(f"Question ID: [yellow]{submission.question_id}[/yellow]")
        console.print(f"Created: Available via repository")
        console.print(f"Document blocks: {len(submission.canonical.blocks)}")
        
    except Exception as e:
        handle_error("getting submission", e)


if __name__ == "__main__":
    app()