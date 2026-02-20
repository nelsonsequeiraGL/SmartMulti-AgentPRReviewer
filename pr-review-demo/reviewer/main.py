"""CLI: review a diff with multi-agent PR review, merge, and write outputs."""

import asyncio
import json
import sys
from pathlib import Path

import typer
from reviewer.agents import run_all
from reviewer.merge import merge
from reviewer.render import render_to_markdown
from reviewer.schema import IssueSeverity
from dotenv import load_dotenv
load_dotenv()

app = typer.Typer()


def _read_diff(diff_path: str) -> str:
    """Read diff from file or stdin (path '-' or missing)."""
    if not diff_path or diff_path == "-":
        return sys.stdin.read()
    path = Path(diff_path)
    if not path.exists():
        typer.echo(f"Error: file not found: {diff_path}", err=True)
        raise typer.Exit(1)
    return path.read_text(encoding="utf-8", errors="replace")


@app.callback(invoke_without_command=True)
def review(
    ctx: typer.Context,
    diff_path: str = typer.Argument(
        "-",
        help="Path to diff file, or '-' for stdin.",
    ),
    out: str = typer.Option(
        "output",
        "--out",
        help="Output directory for review.json and review.md.",
    ),
    show_agents: bool = typer.Option(
        False,
        "--show-agents",
        help="Print each agent's summary.",
    ),
    print_json: bool = typer.Option(
        False,
        "--json",
        help="Print merged issues as JSON to stdout.",
    ),
) -> None:
    """
    Run AI PR review: read diff, run agents, merge, write review.json + review.md.
    """
    if ctx.invoked_subcommand is not None:
        return
    diff_text = _read_diff(diff_path)
    if not diff_text.strip():
        typer.echo("Error: empty diff.", err=True)
        raise typer.Exit(1)

    # Run agents (async)
    reviews = asyncio.run(run_all(diff_text))

    if show_agents:
        for name, r in reviews.items():
            typer.echo(f"\n[{name}] {r.summary}")

    # Merge
    merged = merge(reviews)

    # Output dir
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "review.json"
    md_path = out_dir / "review.md"

    # Write review.json (list of issue dicts)
    issues_json = [i.model_dump(mode="json") for i in merged]
    json_path.write_text(json.dumps(issues_json, indent=2), encoding="utf-8")

    # Write review.md
    md_path.write_text(render_to_markdown(merged), encoding="utf-8")

    # Print locations
    typer.echo(f"\nWrote: {json_path}")
    typer.echo(f"Wrote: {md_path}")

    # Quick summary
    counts = {s: sum(1 for i in merged if i.severity == s) for s in IssueSeverity}
    typer.echo(
        f"Summary: #{counts[IssueSeverity.high]} high | "
        f"#{counts[IssueSeverity.med]} med | #{counts[IssueSeverity.low]} low"
    )

    if print_json:
        typer.echo(json.dumps(issues_json, indent=2))


if __name__ == "__main__":
    app()
