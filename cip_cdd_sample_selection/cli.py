from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd
import typer

from .sampling import SamplingConfig, sample_dataframe

app = typer.Typer(help="CIP/CDD sample selection CLI.")


def _parse_stratify(stratify: List[str]) -> List[str]:
    fields: List[str] = []
    for item in stratify:
        parts = [part.strip() for part in item.split(",") if part.strip()]
        for part in parts:
            if part not in fields:
                fields.append(part)
    return fields


def _read_input(path: Path, sheet: Optional[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    sheet_arg = sheet if sheet is not None else 0
    return pd.read_excel(path, sheet_name=sheet_arg)


def _validate_columns(df: pd.DataFrame, stratify_fields: List[str], id_column: Optional[str]) -> None:
    missing = [col for col in stratify_fields if col not in df.columns]
    if missing:
        raise ValueError(f"Stratify columns not found in input: {', '.join(missing)}")
    if id_column and id_column not in df.columns:
        raise ValueError(f"ID column '{id_column}' not found in input.")


def _print_overview(summary: dict) -> None:
    population_size = summary["population"]["size"]
    sample_size = summary["sample"]["size"]
    stratify_fields = summary.get("stratify_fields") or []
    typer.echo(f"Selected {sample_size} of {population_size} records using method '{summary['methodology']['method']}'.")
    if stratify_fields and summary.get("allocations"):
        typer.echo("Per-stratum sample counts:")
        for alloc in summary["allocations"]:
            stratum_parts = [f"{k}={v if v is not None else 'NULL'}" for k, v in alloc["stratum"].items()]
            desc = ", ".join(stratum_parts) if stratum_parts else "(unstratified)"
            typer.echo(
                f"- {desc}: {alloc['sample_count']} of {alloc['population_count']} "
                f"({alloc['share_of_sample']:.2%} of sample, {alloc['share_of_population']:.2%} of population)"
            )


@app.command()
def sample(
    input: Path = typer.Option(..., "--input", "-i", help="Path to Excel file containing the population."),
    sheet: Optional[str] = typer.Option(None, "--sheet", "-t", help="Sheet name (defaults to the first sheet)."),
    stratify: List[str] = typer.Option(
        [],
        "--stratify",
        "-s",
        help="Columns to stratify by. Comma-separated string or repeat the flag (e.g., --stratify Region,Risk --stratify Product).",
    ),
    method: str = typer.Option(
        "statistical",
        "--method",
        "-m",
        help="Sampling methodology: statistical, simple_random, percentage, or systematic.",
    ),
    confidence: float = typer.Option(0.99, help="Confidence level for statistical sizing (default 0.99)."),
    margin: float = typer.Option(0.05, help="Margin of error for statistical sizing (default 0.05)."),
    expected_error_rate: float = typer.Option(0.01, help="Expected error rate for statistical sizing (default 0.01)."),
    sample_size: Optional[int] = typer.Option(None, help="Fixed sample size (used by simple_random/systematic or overrides)."),
    sample_percentage: Optional[float] = typer.Option(None, help="Percentage of population to sample."),
    systematic_step: Optional[int] = typer.Option(None, help="Step/interval for systematic sampling."),
    id_column: Optional[str] = typer.Option(None, help="Optional ID column to include in the JSON summary."),
    output_dir: Path = typer.Option(Path("outputs"), help="Directory to write outputs."),
    seed: Optional[int] = typer.Option(42, help="Random seed for reproducibility."),
    no_random_start: bool = typer.Option(False, help="Disable random start for systematic sampling."),
) -> None:
    stratify_fields = _parse_stratify(stratify)
    method = method.lower()
    df = _read_input(input, sheet)
    _validate_columns(df, stratify_fields, id_column)

    cfg = SamplingConfig(
        method=method,
        confidence=confidence,
        margin=margin,
        expected_error_rate=expected_error_rate,
        sample_size=sample_size,
        sample_percentage=sample_percentage,
        systematic_step=systematic_step,
        stratify_fields=stratify_fields,
        id_column=id_column,
        seed=seed,
        systematic_random_start=not no_random_start,
    )

    sample_df, summary = sample_dataframe(df, cfg)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_path = output_dir / f"sample_{timestamp}.csv"
    json_path = output_dir / f"sampling_summary_{timestamp}.json"

    sample_df.to_csv(sample_path, index=False)
    summary["source"] = {"input_path": str(input.resolve()), "sheet_name": sheet}
    summary["outputs"] = {"sample_csv": str(sample_path.resolve()), "json_summary": str(json_path.resolve())}

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    _print_overview(summary)
    typer.echo(f"Sample saved to: {sample_path}")
    typer.echo(f"JSON summary saved to: {json_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
