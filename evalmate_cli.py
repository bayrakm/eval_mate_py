#!/usr/bin/env python3
"""
EvalMate CLI - Unified Terminal Interface for Assignment Evaluation

This CLI tool provides a complete end-to-end evaluation workflow, allowing users to:
- Select rubrics, questions, and submissions from the repository
- Build fusion context and run LLM evaluations
- View colorized results and export to JSON/CSV
- Operate entirely from the terminal without web UI dependencies

Usage:
    uv run python evalmate_cli.py run
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Set UTF-8 encoding for Windows compatibility
if os.name == 'nt':  # Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Try to set console to UTF-8 mode
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

# EvalMate core imports
from app.core.fusion.builder import build_fusion_context
from app.core.llm.evaluator import evaluate_submission, evaluate_submission_narrative
from app.core.store import repo
from app.core.models.schemas import EvalResult

# Initialize Rich console and Typer app
console = Console()
app = typer.Typer(help="EvalMate CLI - Automated multimodal grading assistant")


def display_banner():
    """Display the EvalMate CLI welcome banner."""
    banner = """
[bold cyan]
===================================
        EvalMate CLI
 Automated Multimodal Grading
===================================
[/bold cyan]

[dim]End-to-end student assignment evaluation with AI-powered feedback[/dim]
"""
    console.print(Panel(banner, border_style="cyan", padding=(1, 2)))


def list_and_choose_rubric() -> str:
    """List available rubrics and let user choose one."""
    all_rubrics = repo.list_rubrics()
    if not all_rubrics:
        console.print("[red]ERROR: No rubrics found in repository![/red]")
        console.print("[yellow]TIP: Upload rubrics through the web interface or API first[/yellow]")
        raise typer.Exit(1)
    
    # Filter rubrics that have both questions and submissions
    all_questions = repo.list_questions()
    all_submissions = repo.list_submissions()
    
    rubrics = []
    for rubric in all_rubrics:
        # Check if this rubric has questions
        has_questions = any(q.get('rubric_id') == rubric['id'] for q in all_questions)
        # Check if this rubric has submissions
        has_submissions = any(s.get('rubric_id') == rubric['id'] for s in all_submissions)
        
        if has_questions and has_submissions:
            rubrics.append(rubric)
    
    if not rubrics:
        console.print("[red]ERROR: No rubrics found with both questions and submissions![/red]")
        console.print(f"[yellow]TIP: Found {len(all_rubrics)} total rubrics, but none have complete data sets[/yellow]")
        console.print("[dim]Tip: Upload questions and submissions through the web interface[/dim]")
        raise typer.Exit(1)
    
    console.print("\n[bold cyan]Available Rubrics[/bold cyan]")
    
    # Create a table for rubrics
    table = Table(box=box.SIMPLE)
    table.add_column("#", style="cyan", no_wrap=True, width=3)
    table.add_column("Course", style="green", no_wrap=True)
    table.add_column("Assignment", style="yellow")
    table.add_column("Version", style="magenta", no_wrap=True, width=8)
    table.add_column("Created", style="dim", no_wrap=True)
    
    for i, rubric in enumerate(rubrics, 1):
        created_date = rubric.get('created_at', 'Unknown')
        if created_date and created_date != 'Unknown':
            try:
                # Format the date nicely
                from datetime import datetime
                dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                created_date = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        table.add_row(
            str(i),
            rubric.get('course', 'N/A'),
            rubric.get('assignment', 'N/A'),
            rubric.get('version', 'N/A'),
            created_date
        )
    
    console.print(table)
    
    while True:
        try:
            choice = IntPrompt.ask(
                "\n[bold]Select rubric number",
                default=1,
                show_default=True
            )
            if 1 <= choice <= len(rubrics):
                selected_rubric = rubrics[choice - 1]
                console.print(f"[green]SELECTED: {selected_rubric['course']} - {selected_rubric['assignment']}[/green]")
                return selected_rubric['id']
            else:
                console.print(f"[red]Please enter a number between 1 and {len(rubrics)}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled by user[/yellow]")
            raise typer.Exit(0)


def list_and_choose_question(rubric_id: str) -> str:
    """List available questions for the selected rubric and let user choose one."""
    questions = repo.list_questions(rubric_id)
    if not questions:
        console.print(f"[red]ERROR: No questions found for rubric {rubric_id}![/red]")
        raise typer.Exit(1)
    
    console.print("\n[bold cyan]Available Questions[/bold cyan]")
    
    # Create a table for questions
    table = Table(box=box.SIMPLE)
    table.add_column("#", style="cyan", no_wrap=True, width=3)
    table.add_column("Question ID", style="yellow")
    table.add_column("Created", style="dim", no_wrap=True)
    
    for i, question in enumerate(questions, 1):
        created_date = question.get('created_at', 'Unknown')
        if created_date and created_date != 'Unknown':
            try:
                # Format the date nicely
                from datetime import datetime
                dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                created_date = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        # Truncate long IDs for display
        display_id = question['id']
        if len(display_id) > 40:
            display_id = display_id[:37] + "..."
        
        table.add_row(
            str(i),
            display_id,
            created_date
        )
    
    console.print(table)
    
    while True:
        try:
            choice = IntPrompt.ask(
                "\n[bold]Select question number",
                default=1,
                show_default=True
            )
            if 1 <= choice <= len(questions):
                selected_question = questions[choice - 1]
                console.print(f"[green]SELECTED question: {selected_question['id'][:20]}...[/green]")
                return selected_question['id']
            else:
                console.print(f"[red]Please enter a number between 1 and {len(questions)}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled by user[/yellow]")
            raise typer.Exit(0)


def list_and_choose_submission(rubric_id: str, question_id: str) -> str:
    """List available submissions for the selected rubric/question and let user choose one."""
    submissions = repo.list_submissions(rubric_id)
    
    # Filter submissions that match both rubric_id and question_id
    filtered_submissions = [
        sub for sub in submissions 
        if sub.get('question_id') == question_id
    ]
    
    if not filtered_submissions:
        console.print(f"[red]ERROR: No submissions found for the selected rubric and question![/red]")
        console.print(f"[dim]Rubric: {rubric_id}[/dim]")
        console.print(f"[dim]Question: {question_id}[/dim]")
        raise typer.Exit(1)
    
    console.print("\n[bold cyan]Available Submissions[/bold cyan]")
    
    # Create a table for submissions
    table = Table(box=box.SIMPLE)
    table.add_column("#", style="cyan", no_wrap=True, width=3)
    table.add_column("Student", style="green")
    table.add_column("Submission ID", style="yellow")
    table.add_column("Created", style="dim", no_wrap=True)
    
    for i, submission in enumerate(filtered_submissions, 1):
        created_date = submission.get('created_at', 'Unknown')
        if created_date and created_date != 'Unknown':
            try:
                # Format the date nicely
                from datetime import datetime
                dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                created_date = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        # Truncate long IDs for display
        display_id = submission['id']
        if len(display_id) > 40:
            display_id = display_id[:37] + "..."
        
        table.add_row(
            str(i),
            submission.get('student', 'Unknown'),
            display_id,
            created_date
        )
    
    console.print(table)
    
    while True:
        try:
            choice = IntPrompt.ask(
                "\n[bold]Select submission number",
                default=1,
                show_default=True
            )
            if 1 <= choice <= len(filtered_submissions):
                selected_submission = filtered_submissions[choice - 1]
                console.print(f"[green]SELECTED submission by: {selected_submission.get('student', 'Unknown')}[/green]")
                return selected_submission['id']
            else:
                console.print(f"[red]Please enter a number between 1 and {len(filtered_submissions)}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled by user[/yellow]")
            raise typer.Exit(0)


def display_evaluation_results(result: EvalResult):
    """Display evaluation results - handles both structured and narrative formats."""
    console.print("\n[bold green]EVALUATION COMPLETE![/bold green]")
    
    # Check if this is narrative format (has narrative fields) or structured format
    is_narrative = hasattr(result, 'narrative_evaluation') and result.narrative_evaluation
    
    if is_narrative:
        # NARRATIVE FORMAT - Display as paragraphs like test command
        if result.narrative_evaluation:
            console.print(Panel(
                result.narrative_evaluation,
                title="[bold]📋 Evaluation[/bold]",
                border_style="blue",
                padding=(1, 2)
            ))
            console.print()
        
        if result.narrative_strengths:
            console.print(Panel(
                result.narrative_strengths,
                title="[bold]✅ Strengths[/bold]",
                border_style="green",
                padding=(1, 2)
            ))
            console.print()
        
        if result.narrative_gaps:
            console.print(Panel(
                result.narrative_gaps,
                title="[bold]⚠️  Gaps & Areas for Improvement[/bold]",
                border_style="yellow",
                padding=(1, 2)
            ))
            console.print()
        
        if result.narrative_guidance:
            console.print(Panel(
                result.narrative_guidance,
                title="[bold]💡 Guidance for Improvement[/bold]",
                border_style="cyan",
                padding=(1, 2)
            ))
            console.print()
    else:
        # STRUCTURED FORMAT - Display as table (legacy format)
        if result.items and len(result.items) > 0:
            # Create results table
            table = Table(title="Rubric Evaluation Summary", box=box.DOUBLE_EDGE)
            table.add_column("Criterion ID", style="cyan", no_wrap=True, width=15)
            table.add_column("Score", justify="right", style="bold yellow", width=8)
            table.add_column("Max", justify="right", style="dim", width=6)
            table.add_column("Justification", style="white", min_width=50)
            
            for item in result.items:
                # Truncate long justifications for table display
                justification = item.justification
                if len(justification) > 80:
                    justification = justification[:77] + "..."
                
                # Color-code scores
                score_str = str(round(item.score, 1))
                if item.score >= 80:
                    score_style = "bold green"
                elif item.score >= 60:
                    score_style = "bold yellow"
                else:
                    score_style = "bold red"
                
                table.add_row(
                    item.rubric_item_id[:12] + "..." if len(item.rubric_item_id) > 15 else item.rubric_item_id,
                    f"[{score_style}]{score_str}[/{score_style}]",
                    "100",
                    justification
                )
            
            console.print(table)
        
        # Overall score panel
        total_score = round(result.total, 1) if result.total else 0
        if total_score >= 80:
            score_color = "bold green"
            emoji = "EXCELLENT"
        elif total_score >= 60:
            score_color = "bold yellow"
            emoji = "GOOD"
        else:
            score_color = "bold red"
            emoji = "NEEDS WORK"
        
        score_panel = Panel(
            f"[{score_color}]{emoji} - Total Score: {total_score}/100[/{score_color}]",
            title="Final Grade",
            border_style=score_color.split()[-1],
            padding=(1, 2)
        )
        console.print(score_panel)
        
        # Overall feedback
        if result.overall_feedback:
            feedback_panel = Panel(
                f"[italic]{result.overall_feedback}[/italic]",
                title="Overall Feedback",
                border_style="blue",
                padding=(1, 2)
            )
            console.print(feedback_panel)


def save_results(result: EvalResult) -> tuple[str, str]:
    """Save evaluation results to JSON and CSV files."""
    # Ensure results directory exists
    os.makedirs("data/results", exist_ok=True)
    
    # Generate timestamp-based filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join("data", "results", f"eval_{timestamp}.json")
    csv_path = os.path.join("data", "results", f"eval_{timestamp}.csv")
    
    # Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False, default=str)
    
    # Save CSV (if pandas is available)
    try:
        import pandas as pd
        
        # Prepare data for CSV
        csv_data = []
        for item in result.items:
            csv_data.append({
                'rubric_item_id': item.rubric_item_id,
                'score': round(item.score, 2),
                'justification': item.justification,
                'evidence_block_ids': ', '.join(item.evidence_block_ids) if item.evidence_block_ids else ''
            })
        
        # Add overall row
        csv_data.append({
            'rubric_item_id': 'TOTAL',
            'score': round(result.total, 2),
            'justification': result.overall_feedback,
            'evidence_block_ids': ''
        })
        
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
    except ImportError:
        console.print("[yellow]WARNING: pandas not available, skipping CSV export[/yellow]")
        csv_path = None
    except Exception as e:
        console.print(f"[yellow]WARNING: CSV export failed: {e}[/yellow]")
        csv_path = None
    
    return json_path, csv_path


@app.command("run")
def run_evaluation():
    """
    Run the complete EvalMate evaluation workflow.
    
    This command guides you through:
    1. Selecting a rubric from the repository
    2. Choosing a matching question
    3. Picking a student submission
    4. Building fusion context
    5. Running LLM evaluation
    6. Displaying results and optionally saving them
    """
    try:
        # Display welcome banner
        display_banner()
        
        # Step 1: Select rubric
        console.print("[bold]Step 1/5:[/bold] Select a rubric")
        rubric_id = list_and_choose_rubric()
        
        # Step 2: Select question
        console.print("\n[bold]Step 2/5:[/bold] Select a question")
        question_id = list_and_choose_question(rubric_id)
        
        # Step 3: Select submission
        console.print("\n[bold]Step 3/5:[/bold] Select a submission")
        submission_id = list_and_choose_submission(rubric_id, question_id)
        
        # Step 4: Build fusion context
        console.print("\n[bold]Step 4/5:[/bold] Building fusion context...")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Assembling multimodal context...", total=None)
            try:
                fusion = build_fusion_context(rubric_id, question_id, submission_id)
                progress.update(task, description="SUCCESS: Fusion context built!")
            except Exception as e:
                progress.update(task, description=f"ERROR: Failed to build fusion context: {e}")
                raise
        
        console.print(f"[green]SUCCESS: Fusion built![/green] "
                     f"Text blocks: {fusion.text_block_count}, "
                     f"Visuals: {fusion.visual_count}, "
                     f"Token estimate: {fusion.token_estimate:,}")
        
        # Step 5: Run evaluation
        console.print("\n[bold]Step 5/5:[/bold] Running LLM evaluation...")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Evaluating with AI (this may take 1-2 minutes)...", total=None)
            try:
                # Capture and redirect any Unicode output that might cause issues
                import logging
                import sys
                from io import StringIO
                
                # Temporarily redirect logging to avoid Unicode issues
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                log_capture = StringIO()
                
                # Set encoding-safe handlers
                try:
                    result = evaluate_submission_narrative(rubric_id, question_id, submission_id)
                    progress.update(task, description="SUCCESS: Evaluation completed!")
                finally:
                    # Restore original stdout/stderr
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    
            except Exception as e:
                progress.update(task, description=f"ERROR: Evaluation failed: {str(e).encode('ascii', 'ignore').decode('ascii')}")
                raise
        
        # Display results
        display_evaluation_results(result)
        
        # Optional: Save results
        console.print()
        save_choice = Prompt.ask(
            "Save results to files?", 
            choices=["y", "n"], 
            default="y"
        )
        
        if save_choice.lower() == "y":
            json_path, csv_path = save_results(result)
            console.print(f"[green]SUCCESS: Results saved to:[/green]")
            console.print(f"   JSON: {json_path}")
            if csv_path:
                console.print(f"   CSV:  {csv_path}")
        
        # Ask about continuing
        console.print()
        continue_choice = Prompt.ask(
            "Run another evaluation?", 
            choices=["y", "n"], 
            default="n"
        )
        
        if continue_choice.lower() == "y":
            console.print("\n" + "="*60 + "\n")
            run_evaluation()  # Recursive call for another round
        else:
            console.print("\n[bold cyan]Thank you for using EvalMate CLI![/bold cyan]")
            console.print("[dim]Happy grading![/dim]")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Goodbye! EvalMate CLI session ended.[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[bold red]ERROR: {e}[/bold red]")
        console.print("[dim]Check your environment setup and try again.[/dim]")
        raise typer.Exit(1)


@app.command("status")
def show_status():
    """
    Show repository status and available data.
    """
    console.print("[bold cyan]EvalMate Repository Status[/bold cyan]\n")
    
    try:
        # Count rubrics
        rubrics = repo.list_rubrics()
        console.print(f"Rubrics: [bold green]{len(rubrics)}[/bold green]")
        
        # Count questions
        questions = repo.list_questions()
        console.print(f"Questions: [bold green]{len(questions)}[/bold green]")
        
        # Count submissions
        submissions = repo.list_submissions()
        console.print(f"Submissions: [bold green]{len(submissions)}[/bold green]")
        
        # Count evaluations
        try:
            results = repo.list_eval_results()
            console.print(f"Evaluations: [bold green]{len(results)}[/bold green]")
        except:
            console.print(f"Evaluations: [yellow]Unknown[/yellow]")
        
        if len(rubrics) > 0 and len(questions) > 0 and len(submissions) > 0:
            console.print("\n[green]SUCCESS: Ready to run evaluations![/green]")
        else:
            console.print("\n[yellow]WARNING: Some data missing. Upload files through the web interface first.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]ERROR: Error checking status: {e}[/red]")


@app.command("test")
def test_evaluation(
    question: str = typer.Option(
        "data/questions/COS4015-B_Coursework 001.pdf",
        "--question", "-q",
        help="Path to question file"
    ),
    rubric: str = typer.Option(
        "data/rubrics/COS4015-B_Coursework 001 - Marking Scheme.pdf",
        "--rubric", "-r",
        help="Path to rubric file"
    ),
    submission: str = typer.Option(
        "data/submissions/test1.pdf",
        "--submission", "-s",
        help="Path to student submission file"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output file path for results (JSON)"
    ),
    debug: bool = typer.Option(
        False,
        "--debug", "-d",
        help="Show detailed parsing debug information"
    ),
    show_content: bool = typer.Option(
        False,
        "--show-content",
        help="Display full parsed content of all documents"
    )
):
    """
    Test evaluation with direct file paths (bypasses repository).
    
    This command allows you to quickly test the evaluation system with specific files
    without uploading them to the repository first.
    
    Example:
        uv run python evalmate_cli.py test
        uv run python evalmate_cli.py test -q "path/to/question.pdf" -r "path/to/rubric.pdf" -s "path/to/submission.pdf"
    """
    from pathlib import Path
    from app.core.io.ingest import ingest_any
    from app.core.io.rubric_parser import parse_rubric_to_items
    from app.core.models.schemas import Question, Submission, Rubric
    from app.core.models.ids import new_question_id, new_rubric_id, new_submission_id
    
    display_banner()
    console.print("\n[bold cyan]Test Evaluation Mode[/bold cyan]")
    console.print("[dim]Evaluating with direct file paths...[/dim]\n")
    
    try:
        # Validate files exist
        question_path = Path(question)
        rubric_path = Path(rubric)
        submission_path = Path(submission)
        
        if not question_path.exists():
            console.print(f"[red]ERROR: Question file not found: {question}[/red]")
            raise typer.Exit(1)
        if not rubric_path.exists():
            console.print(f"[red]ERROR: Rubric file not found: {rubric}[/red]")
            raise typer.Exit(1)
        if not submission_path.exists():
            console.print(f"[red]ERROR: Submission file not found: {submission}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[cyan]Question:[/cyan] {question}")
        console.print(f"[cyan]Rubric:[/cyan] {rubric}")
        console.print(f"[cyan]Submission:[/cyan] {submission}\n")
        
        # Step 1: Ingest documents
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing question document...", total=None)
            question_doc = ingest_any(str(question_path))
            progress.update(task, description="[green]✓[/green] Question processed")
            progress.stop_task(task)
            
            task = progress.add_task("Processing rubric document...", total=None)
            rubric_doc = ingest_any(str(rubric_path))
            progress.update(task, description="[green]✓[/green] Rubric processed")
            progress.stop_task(task)
            
            task = progress.add_task("Processing submission document...", total=None)
            submission_doc = ingest_any(str(submission_path))
            progress.update(task, description="[green]✓[/green] Submission processed")
            progress.stop_task(task)
        
        console.print()
        
        # Show parsed content if requested
        if show_content:
            console.print("\n" + "="*80)
            console.print("[bold yellow]📄 PARSED DOCUMENTS CONTENT[/bold yellow]")
            console.print("="*80 + "\n")
            
            # Question Content
            console.print(Panel("[bold cyan]QUESTION DOCUMENT[/bold cyan]", border_style="cyan"))
            console.print(f"[dim]Blocks: {len(question_doc.blocks)} ({sum(1 for b in question_doc.blocks if b.kind=='text')} text, {sum(1 for b in question_doc.blocks if b.kind=='visual')} visual)[/dim]\n")
            
            question_text_blocks = [b for b in question_doc.blocks if b.kind == "text"]
            question_visual_blocks = [b for b in question_doc.blocks if b.kind == "visual"]
            
            for idx, block in enumerate(question_text_blocks[:5], 1):  # Show first 5 blocks
                console.print(f"[cyan]Text Block {idx}:[/cyan]")
                console.print(f"{block.text[:500]}..." if len(block.text) > 500 else block.text)
                console.print()
            
            if len(question_text_blocks) > 5:
                console.print(f"[dim]... and {len(question_text_blocks) - 5} more text blocks[/dim]\n")
            
            # Show visual blocks
            if question_visual_blocks:
                console.print(f"[bold cyan]Visual Content ({len(question_visual_blocks)} visuals):[/bold cyan]")
                for idx, block in enumerate(question_visual_blocks, 1):
                    visual = block.visual
                    console.print(f"\n[cyan]Visual {idx}:[/cyan]")
                    console.print(f"  [dim]Type:[/dim] {visual.type}")
                    console.print(f"  [dim]Source:[/dim] {visual.source_path}")
                    if visual.caption_text:
                        console.print(f"  [dim]Caption:[/dim] {visual.caption_text[:200]}...")
                    if visual.ocr_text:
                        console.print(f"  [dim]OCR Text:[/dim] {visual.ocr_text[:200]}...")
                    if visual.detected_labels:
                        console.print(f"  [dim]Labels:[/dim] {', '.join(visual.detected_labels)}")
                console.print()
            
            # Rubric Content
            console.print(Panel("[bold yellow]RUBRIC DOCUMENT[/bold yellow]", border_style="yellow"))
            console.print(f"[dim]Blocks: {len(rubric_doc.blocks)} ({sum(1 for b in rubric_doc.blocks if b.kind=='text')} text, {sum(1 for b in rubric_doc.blocks if b.kind=='visual')} visual)[/dim]\n")
            
            rubric_text_blocks = [b for b in rubric_doc.blocks if b.kind == "text"]
            rubric_visual_blocks = [b for b in rubric_doc.blocks if b.kind == "visual"]
            
            for idx, block in enumerate(rubric_text_blocks[:10], 1):  # Show first 10 blocks for rubric
                console.print(f"[yellow]Text Block {idx}:[/yellow]")
                console.print(f"{block.text[:500]}..." if len(block.text) > 500 else block.text)
                console.print()
            
            if len(rubric_text_blocks) > 10:
                console.print(f"[dim]... and {len(rubric_text_blocks) - 10} more text blocks[/dim]\n")
            
            # Show visual blocks
            if rubric_visual_blocks:
                console.print(f"[bold yellow]Visual Content ({len(rubric_visual_blocks)} visuals):[/bold yellow]")
                for idx, block in enumerate(rubric_visual_blocks, 1):
                    visual = block.visual
                    console.print(f"\n[yellow]Visual {idx}:[/yellow]")
                    console.print(f"  [dim]Type:[/dim] {visual.type}")
                    console.print(f"  [dim]Source:[/dim] {visual.source_path}")
                    if visual.caption_text:
                        console.print(f"  [dim]Caption:[/dim] {visual.caption_text[:200]}...")
                    if visual.ocr_text:
                        console.print(f"  [dim]OCR Text:[/dim] {visual.ocr_text[:200]}...")
                    if visual.detected_labels:
                        console.print(f"  [dim]Labels:[/dim] {', '.join(visual.detected_labels)}")
                console.print()
            
            # Submission Content
            console.print(Panel("[bold green]SUBMISSION DOCUMENT[/bold green]", border_style="green"))
            console.print(f"[dim]Blocks: {len(submission_doc.blocks)} ({sum(1 for b in submission_doc.blocks if b.kind=='text')} text, {sum(1 for b in submission_doc.blocks if b.kind=='visual')} visual)[/dim]\n")
            
            submission_text_blocks = [b for b in submission_doc.blocks if b.kind == "text"]
            submission_visual_blocks = [b for b in submission_doc.blocks if b.kind == "visual"]
            
            for idx, block in enumerate(submission_text_blocks[:5], 1):  # Show first 5 blocks
                console.print(f"[green]Text Block {idx}:[/green]")
                console.print(f"{block.text[:500]}..." if len(block.text) > 500 else block.text)
                console.print()
            
            if len(submission_text_blocks) > 5:
                console.print(f"[dim]... and {len(submission_text_blocks) - 5} more text blocks[/dim]\n")
            
            # Show visual blocks
            if submission_visual_blocks:
                console.print(f"[bold green]Visual Content ({len(submission_visual_blocks)} visuals):[/bold green]")
                for idx, block in enumerate(submission_visual_blocks, 1):
                    visual = block.visual
                    console.print(f"\n[green]Visual {idx}:[/green]")
                    console.print(f"  [dim]Type:[/dim] {visual.type}")
                    console.print(f"  [dim]Source:[/dim] {visual.source_path}")
                    console.print(f"  [dim]ID:[/dim] {visual.id}")
                    if visual.caption_text:
                        console.print(f"  [dim]Caption:[/dim] {visual.caption_text[:300]}...")
                    if visual.ocr_text:
                        console.print(f"  [dim]OCR Text:[/dim] {visual.ocr_text[:300]}...")
                    if visual.structured_table:
                        console.print(f"  [dim]Table:[/dim] {len(visual.structured_table)} rows")
                        # Show first few rows of table
                        for row_idx, row in enumerate(visual.structured_table[:3], 1):
                            console.print(f"    Row {row_idx}: {' | '.join(str(cell)[:30] for cell in row)}")
                    if visual.detected_labels:
                        console.print(f"  [dim]Labels:[/dim] {', '.join(visual.detected_labels)}")
                console.print()
            
            console.print("="*80 + "\n")
        
        # Step 2: Parse rubric into items
        console.print("[cyan]Parsing rubric criteria...[/cyan]")
        
        # Debug: Show rubric document structure
        if debug:
            console.print(f"[dim]Rubric has {len(rubric_doc.blocks)} blocks:[/dim]")
            text_blocks = [b for b in rubric_doc.blocks if b.kind == "text"]
            visual_blocks = [b for b in rubric_doc.blocks if b.kind == "visual"]
            console.print(f"[dim]  - {len(text_blocks)} text blocks[/dim]")
            console.print(f"[dim]  - {len(visual_blocks)} visual blocks[/dim]")
            
            # Show first few text blocks
            if text_blocks:
                console.print(f"[dim]First text block sample:[/dim]")
                first_text = text_blocks[0].text[:200] if text_blocks[0].text else ""
                console.print(f"[dim]{first_text}...[/dim]\n")
        
        rubric_items = parse_rubric_to_items(rubric_doc)
        console.print(f"[green]✓[/green] Found {len(rubric_items)} rubric criteria\n")
        
        # Display rubric items
        rubric_table = Table(title="Rubric Criteria", box=box.ROUNDED)
        rubric_table.add_column("#", style="cyan", width=3)
        rubric_table.add_column("Title", style="yellow")
        rubric_table.add_column("Weight", style="green", width=10)
        rubric_table.add_column("Type", style="magenta", width=15)
        
        for idx, item in enumerate(rubric_items, 1):
            title_display = item.title[:50] + "..." if len(item.title) > 50 else item.title
            rubric_table.add_row(
                str(idx),
                title_display,
                f"{item.weight:.2f}",
                item.criterion.value
            )
        
        console.print(rubric_table)
        
        # Show detailed rubric criteria if debug mode
        if debug and rubric_items:
            console.print("\n[bold yellow]Detailed Rubric Criteria:[/bold yellow]")
            for idx, item in enumerate(rubric_items, 1):
                console.print(f"\n[cyan]Criterion {idx}: {item.title}[/cyan]")
                console.print(f"[dim]ID:[/dim] {item.id}")
                console.print(f"[dim]Weight:[/dim] {item.weight}")
                console.print(f"[dim]Type:[/dim] {item.criterion.value}")
                console.print(f"[dim]Description:[/dim]")
                console.print(f"  {item.description}")
        
        console.print()
        
        # Step 3: Save objects to repository and build fusion context
        console.print("[cyan]Building evaluation context...[/cyan]")
        
        # Create temporary objects for fusion
        rubric_obj = Rubric(
            id=new_rubric_id(),
            course="TEST",
            assignment="Test Evaluation",
            version="test",
            canonical=rubric_doc,
            items=rubric_items
        )
        
        question_obj = Question(
            id=new_question_id(),
            rubric_id=rubric_obj.id,
            title="Test Question",
            canonical=question_doc
        )
        
        submission_obj = Submission(
            id=new_submission_id(),
            rubric_id=rubric_obj.id,
            question_id=question_obj.id,
            student_handle="test_student",
            canonical=submission_doc
        )
        
        # Temporarily save to repository for fusion context building
        repo.save_rubric(rubric_obj)
        repo.save_question(question_obj)
        repo.save_submission(submission_obj)
        
        # Build fusion context using IDs
        fusion_context = build_fusion_context(
            rubric_id=rubric_obj.id,
            question_id=question_obj.id,
            submission_id=submission_obj.id
        )
        console.print(f"[green]✓[/green] Fusion context built\n")
        
        # Show fusion context details if debug or show_content
        if debug or show_content:
            console.print("\n" + "="*80)
            console.print("[bold magenta]🔗 FUSION CONTEXT (What LLM Receives)[/bold magenta]")
            console.print("="*80 + "\n")
            
            console.print(Panel("[bold]Context Metadata[/bold]", border_style="magenta"))
            console.print(f"[dim]Fusion ID:[/dim] {fusion_context.id}")
            console.print(f"[dim]Token Estimate:[/dim] {fusion_context.token_estimate}")
            console.print(f"[dim]Visual Count:[/dim] {fusion_context.visual_count}")
            console.print(f"[dim]Text Block Count:[/dim] {fusion_context.text_block_count}\n")
            
            # Show rubric items in fusion
            console.print(Panel("[bold]Rubric Items in Fusion Context[/bold]", border_style="yellow"))
            for idx, item in enumerate(fusion_context.rubric_items, 1):
                console.print(f"[yellow]{idx}. {item['title']}[/yellow]")
                console.print(f"   [dim]Weight: {item['weight']}, Criterion: {item['criterion']}[/dim]")
                if debug:
                    console.print(f"   [dim]Description: {item['desc'][:150]}...[/dim]")
                console.print()
            
            # Show question text sample
            console.print(Panel("[bold]Question Text Sample[/bold]", border_style="cyan"))
            q_text_sample = fusion_context.question_text[:500] if fusion_context.question_text else "No question text"
            console.print(f"{q_text_sample}...")
            console.print()
            
            # Show submission text sample
            console.print(Panel("[bold]Submission Text Sample[/bold]", border_style="green"))
            s_text_sample = fusion_context.submission_text[:500] if fusion_context.submission_text else "No submission text"
            console.print(f"{s_text_sample}...")
            console.print()
            
            # Show submission visuals that will be sent to LLM
            if fusion_context.submission_visuals:
                console.print(Panel(f"[bold]Submission Visuals Sent to LLM ({len(fusion_context.submission_visuals)} visuals)[/bold]", border_style="magenta"))
                for idx, visual in enumerate(fusion_context.submission_visuals, 1):
                    console.print(f"\n[magenta]Visual {idx} → LLM:[/magenta]")
                    console.print(f"  [dim]ID:[/dim] {visual.id}")
                    console.print(f"  [dim]Type:[/dim] {visual.type}")
                    
                    if visual.caption:
                        console.print(f"  [dim]Caption (sent to LLM):[/dim]")
                        caption_display = visual.caption if len(visual.caption) <= 400 else visual.caption[:400] + "..."
                        console.print(f"    {caption_display}")
                    else:
                        console.print(f"  [yellow]⚠ No caption generated for this visual[/yellow]")
                    
                    if visual.ocr_text:
                        console.print(f"  [dim]OCR Text (sent to LLM):[/dim]")
                        ocr_display = visual.ocr_text if len(visual.ocr_text) <= 400 else visual.ocr_text[:400] + "..."
                        console.print(f"    {ocr_display}")
                    
                    if visual.rubric_links:
                        console.print(f"  [dim]Rubric Links:[/dim] {', '.join(visual.rubric_links)}")
                console.print()
            else:
                console.print("[yellow]⚠ No submission visuals in fusion context[/yellow]\n")
            
            console.print("="*80 + "\n")
        
        # Step 4: Run evaluation
        console.print("[bold cyan]Running LLM Evaluation...[/bold cyan]")
        console.print("[dim]This may take a minute depending on the submission length...[/dim]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Evaluating submission with GPT-4...", total=None)
            eval_result = evaluate_submission_narrative(
                rubric_id=rubric_obj.id,
                question_id=question_obj.id,
                submission_id=submission_obj.id
            )
            progress.update(task, description="[green]✓[/green] Evaluation complete")
        
        console.print()
        
        # Step 5: Display results (narrative format)
        console.print("[bold green]Evaluation Results[/bold green]\n")
        
        # Display narrative feedback
        if eval_result.narrative_evaluation:
            console.print(Panel(
                eval_result.narrative_evaluation,
                title="[bold]📋 Evaluation[/bold]",
                border_style="blue",
                padding=(1, 2)
            ))
            console.print()
        
        if eval_result.narrative_strengths:
            console.print(Panel(
                eval_result.narrative_strengths,
                title="[bold]✅ Strengths[/bold]",
                border_style="green",
                padding=(1, 2)
            ))
            console.print()
        
        if eval_result.narrative_gaps:
            console.print(Panel(
                eval_result.narrative_gaps,
                title="[bold]⚠️  Gaps & Areas for Improvement[/bold]",
                border_style="yellow",
                padding=(1, 2)
            ))
            console.print()
        
        if eval_result.narrative_guidance:
            console.print(Panel(
                eval_result.narrative_guidance,
                title="[bold]💡 Guidance for Improvement[/bold]",
                border_style="cyan",
                padding=(1, 2)
            ))
            console.print()
        
        # Step 6: Save output if requested
        if output:
            output_path = Path(output)
            output_data = {
                "evaluation": eval_result.model_dump(),
                "metadata": {
                    "question_file": str(question_path),
                    "rubric_file": str(rubric_path),
                    "submission_file": str(submission_path),
                    "evaluated_at": datetime.now().isoformat(),
                    "evaluation_mode": "narrative"
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]✓[/green] Results saved to: {output}")
        
        console.print("\n[bold green]Test evaluation complete![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]ERROR: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()