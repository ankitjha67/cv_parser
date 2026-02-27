#!/usr/bin/env python3
"""
CV-JD Matcher CLI Tool
Production-grade CV matching, gap analysis, and rewriting system.
"""

import typer
from pathlib import Path
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import track

import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.schemas import CV, JD, MatchReport, TailoredCV
from src.ingestion import load_document
from src.parser import parse_cv, parse_jd
from src.scorer import score_cv_jd
from src.gap_analyzer import analyze_gaps
from src.rewriter import rewrite_cv_deterministic
from src.llm.deterministic import DeterministicProvider
from src.llm.openai_adapter import OpenAIProvider
from src.llm.anthropic_adapter import AnthropicProvider
from src.llm.gemini_adapter import GeminiProvider

app = typer.Typer(help="CV-JD Matcher: Zero-hallucination CV matching and rewriting")
console = Console()

@app.command()
def match(
    cv_path: Path = typer.Argument(..., help="Path to CV file (PDF/DOCX/TXT)"),
    jd_path: Path = typer.Argument(..., help="Path to JD file (TXT)"),
    output_dir: Path = typer.Option(Path("./output"), "--output", "-o", help="Output directory"),
    provider: str = typer.Option("deterministic", "--provider", "-p", help="LLM provider (deterministic/openai/anthropic/gemini)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for LLM provider"),
    generate_tailored: bool = typer.Option(True, "--tailored/--no-tailored", help="Generate tailored CV")
):
    """
    Match CV against JD and optionally generate tailored CV.
    
    Example:
        cv_ats match cv.pdf jd.txt
        cv_ats match cv.pdf jd.txt --provider openai --api-key sk-...
    """
    console.print("\n[bold cyan]CV-JD Matcher[/bold cyan] v1.0.0\n", style="bold")
    
    # Validate inputs
    if not cv_path.exists():
        console.print(f"[red]Error:[/red] CV file not found: {cv_path}")
        raise typer.Exit(1)
    if not jd_path.exists():
        console.print(f"[red]Error:[/red] JD file not found: {jd_path}")
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and parse CV
    console.print("[yellow]Loading CV...[/yellow]")
    cv_text = load_document(str(cv_path))
    cv = parse_cv(cv_text)
    console.print(f"[green]✓[/green] Parsed CV: {cv.name}")
    console.print(f"  - {len(cv.experiences)} experiences")
    console.print(f"  - {len(cv.skills)} skills")
    console.print(f"  - {len(cv.education)} education entries\n")
    
    # Load and parse JD
    console.print("[yellow]Loading JD...[/yellow]")
    jd_text = load_document(str(jd_path))
    jd = parse_jd(jd_text)
    console.print(f"[green]✓[/green] Parsed JD: {jd.title}")
    console.print(f"  - {len(jd.requirements)} requirements")
    console.print(f"  - {len(jd.keywords)} keywords\n")
    
    # Run matching
    console.print("[yellow]Computing ATS score...[/yellow]")
    match_report = score_cv_jd(cv, jd)
    
    # Analyze gaps
    hard_gaps, soft_gaps = analyze_gaps(cv, jd, match_report)
    match_report.hard_gaps = hard_gaps
    match_report.soft_gaps = soft_gaps
    
    console.print(f"[green]✓[/green] Matching complete\n")
    
    # Display results
    console.print(f"[bold cyan]ATS Score: {match_report.total_score:.1f}/100[/bold cyan]\n")
    
    # Category breakdown
    table = Table(title="Category Breakdown", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Weight", justify="right", style="dim")
    
    weights = {'skills': 35, 'experience': 30, 'tenure': 15, 'education': 10, 'keywords': 10}
    for category, score in match_report.category_scores.items():
        weight = weights.get(category, 0)
        table.add_row(category.capitalize(), f"{score:.1f}", f"{weight}%")
    
    console.print(table)
    console.print()
    
    # Gaps
    if match_report.hard_gaps:
        console.print(f"[bold red]Hard Gaps ({len(match_report.hard_gaps)}):[/bold red]")
        for gap in match_report.hard_gaps[:5]:
            console.print(f"  • {gap}")
        console.print()
    
    if match_report.soft_gaps:
        console.print(f"[bold yellow]Soft Gaps ({len(match_report.soft_gaps)}):[/bold yellow]")
        for gap in match_report.soft_gaps[:5]:
            console.print(f"  • {gap}")
        console.print()
    
    # Save report
    report_path = output_dir / f"match_report_{cv.name.replace(' ', '_')}.json"
    with open(report_path, 'w') as f:
        json.dump(match_report.model_dump(), f, indent=2, default=str)
    console.print(f"[green]✓[/green] Report saved to {report_path}\n")
    
    # Generate tailored CV
    if generate_tailored:
        console.print("[yellow]Generating tailored CV...[/yellow]")
        
        if provider == "deterministic":
            tailored = rewrite_cv_deterministic(cv, jd, hard_gaps)
        elif provider in ["openai", "anthropic", "gemini"]:
            # For CLI, use deterministic (LLM path is async and more complex)
            console.print("[dim](Using deterministic mode for CLI - LLM requires async environment)[/dim]")
            tailored = rewrite_cv_deterministic(cv, jd, hard_gaps)
        else:
            console.print(f"[red]Unknown provider: {provider}[/red]")
            raise typer.Exit(1)
        
        tailored.match_report_id = match_report.id
        console.print(f"[green]✓[/green] Tailored CV generated with {len(tailored.modifications)} modifications\n")
        
        # Save tailored CV
        tailored_path = output_dir / f"tailored_{cv.name.replace(' ', '_')}.txt"
        with open(tailored_path, 'w') as f:
            tcv = tailored.cv
            f.write(f"{tcv.name}\n\n")
            if tcv.summary:
                f.write(f"SUMMARY\n{tcv.summary}\n\n")
            f.write("EXPERIENCE\n")
            for exp in tcv.experiences:
                f.write(f"\n{exp.role}, {exp.company}, {exp.dates}\n")
                for bullet in exp.bullets:
                    f.write(f"• {bullet}\n")
            f.write(f"\n\nSKILLS\n{', '.join(tcv.skills)}\n\n")
            f.write("EDUCATION\n")
            for edu in tcv.education:
                f.write(f"{edu.get('degree', '')} - {edu.get('institution', '')} ({edu.get('year', '')})\n")
        
        console.print(f"[green]✓[/green] Tailored CV saved to {tailored_path}\n")
    
    console.print("[bold green]Done![/bold green]\n")

@app.command()
def batch(
    cv_path: Path = typer.Argument(..., help="Path to CV file"),
    jds_dir: Path = typer.Argument(..., help="Directory containing JD files"),
    output_dir: Path = typer.Option(Path("./output"), "--output", "-o", help="Output directory")
):
    """
    Batch process: match one CV against multiple JDs.
    
    Example:
        cv_ats batch cv.pdf ./jds/ -o ./results
    """
    console.print("\n[bold cyan]CV-JD Matcher - Batch Mode[/bold cyan]\n")
    
    if not cv_path.exists():
        console.print(f"[red]Error:[/red] CV file not found: {cv_path}")
        raise typer.Exit(1)
    if not jds_dir.is_dir():
        console.print(f"[red]Error:[/red] JDs directory not found: {jds_dir}")
        raise typer.Exit(1)
    
    # Find all JD files
    jd_files = list(jds_dir.glob('*.txt'))
    if not jd_files:
        console.print(f"[red]Error:[/red] No .txt files found in {jds_dir}")
        raise typer.Exit(1)
    
    console.print(f"Found {len(jd_files)} JD files\n")
    
    # Load CV once
    cv_text = load_document(str(cv_path))
    cv = parse_cv(cv_text)
    console.print(f"Loaded CV: {cv.name}\n")
    
    # Process each JD
    results = []
    for jd_file in track(jd_files, description="Processing JDs..."):
        jd_text = load_document(str(jd_file))
        jd = parse_jd(jd_text)
        
        match_report = score_cv_jd(cv, jd)
        hard_gaps, soft_gaps = analyze_gaps(cv, jd, match_report)
        match_report.hard_gaps = hard_gaps
        match_report.soft_gaps = soft_gaps
        
        results.append({
            'jd_file': jd_file.name,
            'jd_title': jd.title,
            'score': match_report.total_score
        })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Display results table
    table = Table(title="Batch Results", show_header=True)
    table.add_column("Rank", style="cyan")
    table.add_column("JD Title", style="white")
    table.add_column("Score", justify="right", style="green")
    
    for i, result in enumerate(results, 1):
        table.add_row(str(i), result['jd_title'], f"{result['score']:.1f}")
    
    console.print("\n")
    console.print(table)
    console.print("\n[bold green]Batch processing complete![/bold green]\n")

@app.command()
def version():
    """Show version information."""
    console.print("\n[bold cyan]CV-JD Matcher[/bold cyan] v1.0.0")
    console.print("Production-grade CV matching with zero hallucinations\n")

if __name__ == "__main__":
    app()
