"""
CLI Evaluation Interface

Typer CLI to run LLM-based evaluations from the terminal.
"""

import json
import logging
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON

from app.core.llm.evaluator import evaluate_submission
from app.core.store import repo

# Setup rich console
console = Console()

# Create typer app
app = typer.Typer(
    help="Run LLM-based grading and evaluation.",
    rich_markup_mode="rich"
)


@app.command("run")
def run_eval(
    rubric_id: str = typer.Option(..., "--rubric-id", "-r", help="ID of the rubric to evaluate against"),
    question_id: str = typer.Option(..., "--question-id", "-q", help="ID of the assignment question"),
    submission_id: str = typer.Option(..., "--submission-id", "-s", help="ID of the student submission"),
    pretty: bool = typer.Option(True, "--pretty/--raw", help="Pretty print output or raw JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """
    Run LLM evaluation for a submission against a rubric.
    
    This command executes the complete evaluation pipeline and displays results.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        console.print("[dim]Verbose logging enabled[/dim]")
    
    console.print(f"[bold blue]Starting Evaluation[/bold blue]")
    console.print(f"Rubric: [cyan]{rubric_id}[/cyan]")
    console.print(f"Question: [cyan]{question_id}[/cyan]")
    console.print(f"Submission: [cyan]{submission_id}[/cyan]")
    
    try:
        with console.status("[bold green]Evaluating submission..."):
            result = evaluate_submission(rubric_id, question_id, submission_id)
        
        console.print("[bold green]Evaluation Complete![/bold green]")
        
        if pretty:
            # Display formatted results
            display_evaluation_result(result)
        else:
            # Output raw JSON
            typer.echo(result.model_dump_json())
            
    except Exception as e:
        console.print(f"[bold red]Evaluation Failed:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command("status")
def check_status(
    submission_id: str = typer.Option(..., "--submission-id", "-s", help="ID of the submission to check")
):
            console.print(f"[green]Submission {submission_id} has been evaluated[/green]")
    try:
        result = repo.get_eval_result(submission_id)
        if result:
            console.print(f"[green]Submission {submission_id} has been evaluated[/green]")
            console.print(f"Total Score: [bold]{result.total}[/bold]")
            console.print(f"Evaluated: {result.metadata.get('evaluated_at', 'Unknown')}")
            console.print(f"Model: {result.metadata.get('model', 'Unknown')}")
        else:
            console.print(f"[yellow]Submission {submission_id} has not been evaluated[/yellow]")
    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")
        sys.exit(1)


@app.command("result")
def show_result(
    submission_id: str = typer.Option(..., "--submission-id", "-s", help="ID of the submission"),
    format: str = typer.Option("pretty", "--format", "-f", help="Output format: pretty, json")
):
    """Display evaluation result for a submission."""
    try:
        result = repo.get_eval_result(submission_id)
        if not result:
            console.print(f"[yellow]No evaluation result found for submission {submission_id}[/yellow]")
            return
        
        if format == "json":
            typer.echo(result.model_dump_json(indent=2))
        else:
            display_evaluation_result(result)
            
    except Exception as e:
        console.print(f"[red]Error retrieving result: {e}[/red]")
        sys.exit(1)


def display_evaluation_result(result):
    """Display evaluation result in a formatted way."""
    # Main score panel
    score_panel = Panel(
        f"[bold green]{result.total}[/bold green]/100",
        title="[bold]Total Score[/bold]",
        expand=False
    )
    console.print(score_panel)
    
    # Detailed scores table
    table = Table(title="Criterion Scores", show_header=True, header_style="bold magenta")
    table.add_column("Rubric Item ID", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Justification", style="white")
    table.add_column("Evidence Blocks", style="dim")
    
    for item in result.items:
        evidence_str = ", ".join(item.evidence_block_ids) if item.evidence_block_ids else "[none]"
        table.add_row(
            item.rubric_item_id,
            f"{item.score:.1f}",
            item.justification[:100] + ("..." if len(item.justification) > 100 else ""),
            evidence_str
        )
    
    console.print(table)
    
    # Overall feedback
    if result.overall_feedback:
        feedback_panel = Panel(
            result.overall_feedback,
            title="[bold]Overall Feedback[/bold]",
            border_style="blue"
        )
        console.print(feedback_panel)
    
    # Metadata
    metadata_text = ""
    if result.metadata:
        metadata_text = f"Model: {result.metadata.get('model', 'Unknown')}\n"
        metadata_text += f"Evaluated: {result.metadata.get('evaluated_at', 'Unknown')}\n"
        metadata_text += f"Student: {result.metadata.get('student', 'Unknown')}"
        
        metadata_panel = Panel(
            metadata_text,
            title="[bold]Evaluation Details[/bold]",
            border_style="dim"
        )
        console.print(metadata_panel)


if __name__ == "__main__":
    app()
