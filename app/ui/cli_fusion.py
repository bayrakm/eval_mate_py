"""
Typer CLI for fusion context management.

This module provides command-line interface for building, listing, and managing
fusion contexts that unify rubric, question, and submission data.
"""

import json
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from app.core.fusion.builder import (
    build_fusion_context,
    load_fusion_context,
    list_fusion_contexts,
    validate_fusion_context
)
from app.core.fusion.schema import FusionContext

# Initialize CLI app and console
app = typer.Typer(help="Fusion context CLI - Unified evaluation context management")
console = Console()


@app.command("build")
def build(
    rubric_id: str = typer.Option(..., "--rubric-id", "-r", help="ID of the rubric"),
    question_id: str = typer.Option(..., "--question-id", "-q", help="ID of the question"),
    submission_id: str = typer.Option(..., "--submission-id", "-s", help="ID of the submission"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    Build fusion context and save to data/fusion.
    
    Creates a unified evaluation context by merging the specified rubric,
    question, and submission into a single structured object.
    """
    try:
        console.print(f"[cyan]Building fusion context...[/cyan]")
        console.print(f"  Rubric ID: {rubric_id}")
        console.print(f"  Question ID: {question_id}")
        console.print(f"  Submission ID: {submission_id}")
        
        fusion = build_fusion_context(rubric_id, question_id, submission_id)
        
        console.print(f"[green]✓ Fusion context created: {fusion.id}[/green]")
        console.print(f"  Token estimate: {fusion.token_estimate}")
        console.print(f"  Visual count: {fusion.visual_count}")
        console.print(f"  Text blocks: {fusion.text_block_count}")
        console.print(f"  Rubric items: {len(fusion.rubric_items)}")
        
        if verbose:
            console.print("\n[yellow]Fusion Context Details:[/yellow]")
            summary = fusion.get_summary()
            for key, value in summary.items():
                if key != "metadata":
                    console.print(f"  {key}: {value}")
        
    except KeyError as e:
        console.print(f"[red]✗ Entity not found: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]✗ Validation error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Failed to build fusion context: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_contexts(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Maximum number of contexts to show"),
    rubric_filter: Optional[str] = typer.Option(None, "--rubric", help="Filter by rubric ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information")
):
    """
    List all saved fusion context files.
    
    Shows a table of all available fusion contexts with summary information.
    """
    try:
        contexts = list_fusion_contexts()
        
        if not contexts:
            console.print("[yellow]No fusion contexts found.[/yellow]")
            return
        
        # Apply filters
        if rubric_filter:
            contexts = [ctx for ctx in contexts if ctx.get("rubric_id") == rubric_filter]
        
        if limit:
            contexts = contexts[:limit]
        
        # Create table
        table = Table(title="Fusion Contexts")
        table.add_column("ID", style="cyan")
        table.add_column("Rubric", style="green")
        table.add_column("Question", style="blue")
        table.add_column("Submission", style="magenta")
        table.add_column("Created", style="yellow")
        table.add_column("Tokens", justify="right")
        table.add_column("Visuals", justify="right")
        
        if verbose:
            table.add_column("Status", style="red")
        
        for ctx in contexts:
            if "error" in ctx:
                table.add_row(
                    ctx["id"],
                    "[red]ERROR[/red]",
                    "[red]ERROR[/red]",
                    "[red]ERROR[/red]",
                    ctx.get("created_at", "unknown"),
                    "[red]0[/red]",
                    "[red]0[/red]",
                    f"[red]{ctx['error']}[/red]" if verbose else ""
                )
            else:
                created_at = ctx.get("created_at", "")[:19] if ctx.get("created_at") else "unknown"
                table.add_row(
                    ctx["id"],
                    ctx.get("rubric_id", "unknown"),
                    ctx.get("question_id", "unknown"),
                    ctx.get("submission_id", "unknown"),
                    created_at,
                    str(ctx.get("token_estimate", 0)),
                    str(ctx.get("visual_count", 0)),
                    "[green]OK[/green]" if verbose else ""
                )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(contexts)} contexts[/dim]")
        
    except Exception as e:
        console.print(f"[red]✗ Failed to list fusion contexts: {e}[/red]")
        raise typer.Exit(1)


@app.command("view")
def view(
    fusion_id: str = typer.Argument(..., help="ID of the fusion context to view"),
    format: str = typer.Option("summary", "--format", "-f", help="Output format: summary, full, json"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save to file instead of printing")
):
    """
    View a specific fusion context.
    
    Display detailed information about a fusion context including content,
    metadata, and validation status.
    """
    try:
        fusion = load_fusion_context(fusion_id)
        
        if format == "json":
            # Full JSON output
            content = json.dumps(fusion.model_dump(), indent=2, default=str, ensure_ascii=False)
            
        elif format == "full":
            # Detailed text representation
            lines = []
            lines.append(f"Fusion Context: {fusion.id}")
            lines.append("=" * 50)
            lines.append(f"Created: {fusion.created_at}")
            lines.append(f"Rubric: {fusion.rubric_id}")
            lines.append(f"Question: {fusion.question_id}")
            lines.append(f"Submission: {fusion.submission_id}")
            lines.append(f"Token Estimate: {fusion.token_estimate}")
            lines.append(f"Visual Count: {fusion.visual_count}")
            lines.append(f"Text Blocks: {fusion.text_block_count}")
            lines.append("")
            
            lines.append("QUESTION:")
            lines.append("-" * 20)
            lines.append(fusion.question_text[:500] + ("..." if len(fusion.question_text) > 500 else ""))
            lines.append("")
            
            lines.append("SUBMISSION TEXT:")
            lines.append("-" * 20)
            lines.append(fusion.submission_text[:500] + ("..." if len(fusion.submission_text) > 500 else ""))
            lines.append("")
            
            if fusion.submission_visuals:
                lines.append("VISUAL ELEMENTS:")
                lines.append("-" * 20)
                for i, visual in enumerate(fusion.submission_visuals, 1):
                    lines.append(f"{i}. {visual.type.upper()}: {visual.caption[:100]}...")
                lines.append("")
            
            lines.append("RUBRIC ITEMS:")
            lines.append("-" * 20)
            for i, item in enumerate(fusion.rubric_items, 1):
                title = item.get("title", "Untitled")
                weight = item.get("weight", 0)
                lines.append(f"{i}. {title} (weight: {weight})")
            
            content = "\n".join(lines)
            
        else:  # summary format
            summary = fusion.get_summary()
            content = json.dumps(summary, indent=2, default=str, ensure_ascii=False)
        
        if output:
            # Save to file
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[green]✓ Saved to {output}[/green]")
        else:
            # Print to console
            if format == "json" or format == "summary":
                console.print_json(content)
            else:
                console.print(content)
    
    except FileNotFoundError:
        console.print(f"[red]✗ Fusion context not found: {fusion_id}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Failed to view fusion context: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
def validate(
    fusion_id: str = typer.Argument(..., help="ID of the fusion context to validate"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed validation results")
):
    """
    Validate a fusion context for completeness and correctness.
    
    Checks that the fusion context has all required data and identifies
    potential issues or warnings.
    """
    try:
        result = validate_fusion_context(fusion_id)
        
        # Display validation status
        if result["valid"]:
            console.print(f"[green]✓ Fusion context {fusion_id} is valid[/green]")
        else:
            console.print(f"[red]✗ Fusion context {fusion_id} has validation errors[/red]")
        
        # Show errors
        if result["errors"]:
            console.print("\n[red]Errors:[/red]")
            for error in result["errors"]:
                console.print(f"  • {error}")
        
        # Show warnings
        if result["warnings"]:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in result["warnings"]:
                console.print(f"  • {warning}")
        
        # Show summary if verbose
        if verbose and result["summary"]:
            console.print("\n[cyan]Summary:[/cyan]")
            summary = result["summary"]
            for key, value in summary.items():
                if key not in ["metadata"]:
                    console.print(f"  {key}: {value}")
        
        # Exit with error code if validation failed
        if not result["valid"]:
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]✗ Validation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete(
    fusion_id: str = typer.Argument(..., help="ID of the fusion context to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """
    Delete a fusion context from storage.
    
    Permanently removes the specified fusion context file from the data/fusion directory.
    """
    try:
        fusion_path = f"data/fusion/{fusion_id}.json"
        
        if not os.path.exists(fusion_path):
            console.print(f"[red]✗ Fusion context not found: {fusion_id}[/red]")
            raise typer.Exit(1)
        
        if not force:
            if not typer.confirm(f"Delete fusion context {fusion_id}?"):
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)
        
        os.remove(fusion_path)
        console.print(f"[green]✓ Deleted fusion context: {fusion_id}[/green]")
    
    except Exception as e:
        console.print(f"[red]✗ Failed to delete fusion context: {e}[/red]")
        raise typer.Exit(1)


@app.command("stats")
def stats():
    """
    Show statistics about all fusion contexts.
    
    Displays aggregate information about fusion contexts including
    total counts, token estimates, and distribution by rubric.
    """
    try:
        contexts = list_fusion_contexts()
        
        if not contexts:
            console.print("[yellow]No fusion contexts found.[/yellow]")
            return
        
        # Calculate statistics
        total_contexts = len(contexts)
        valid_contexts = [ctx for ctx in contexts if "error" not in ctx]
        error_contexts = [ctx for ctx in contexts if "error" in ctx]
        
        total_tokens = sum(ctx.get("token_estimate", 0) for ctx in valid_contexts)
        total_visuals = sum(ctx.get("visual_count", 0) for ctx in valid_contexts)
        
        # Group by rubric
        rubric_counts = {}
        for ctx in valid_contexts:
            rubric_id = ctx.get("rubric_id", "unknown")
            rubric_counts[rubric_id] = rubric_counts.get(rubric_id, 0) + 1
        
        # Display statistics
        console.print(Panel.fit(
            f"[bold cyan]Fusion Context Statistics[/bold cyan]\n\n"
            f"Total Contexts: [green]{total_contexts}[/green]\n"
            f"Valid Contexts: [green]{len(valid_contexts)}[/green]\n"
            f"Error Contexts: [red]{len(error_contexts)}[/red]\n"
            f"Total Tokens: [yellow]{total_tokens:,}[/yellow]\n"
            f"Total Visuals: [blue]{total_visuals}[/blue]\n"
            f"Average Tokens: [yellow]{total_tokens // max(len(valid_contexts), 1):,}[/yellow]",
            title="📊 Statistics"
        ))
        
        if rubric_counts:
            console.print("\n[cyan]Contexts by Rubric:[/cyan]")
            for rubric_id, count in sorted(rubric_counts.items()):
                console.print(f"  {rubric_id}: {count}")
    
    except Exception as e:
        console.print(f"[red]✗ Failed to calculate statistics: {e}[/red]")
        raise typer.Exit(1)


@app.command("init")
def init():
    """
    Initialize fusion context storage directory.
    
    Creates the data/fusion directory if it doesn't exist.
    """
    try:
        fusion_dir = "data/fusion"
        os.makedirs(fusion_dir, exist_ok=True)
        console.print(f"[green]✓ Fusion storage directory ready: {fusion_dir}[/green]")
    
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize storage: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()