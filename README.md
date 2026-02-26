# Statistical Sample Calculator

A browser-based statistical sampling tool for audit and compliance testing. Load any Excel file, configure your sampling methodology, and generate a defensible, reproducible sample with a full JSON audit trail.

## Features

- **Multiple sampling methods** — Statistical (confidence-interval based), simple random, systematic, and percentage.
- **Stratification** — Sample proportionally across one or more columns (e.g., Region, Risk Band, Jurisdiction).
- **GCI jurisdiction expansion** — When an ID column is a GCI field, expand the sample to include all population rows for each sampled GCI, with automatic detection and a one-click offer.
- **Custom requirements** — Define minimum unique GCI rules per column value (e.g., "at least 10 unique GCIs per jurisdiction"). The engine iteratively adds GCIs until all minimums are met, or caps with infeasibility warnings.
- **Override tracking** — Any deviation from the calculated sample (size override, expansion, requirements) is flagged as an override and requires a written justification before downloading.
- **Reproducible results** — Seeded RNG means the same inputs always produce the same sample.
- **No install required** — The HTML app runs entirely in the browser. No server, no Python, no dependencies.

## Quick start (HTML app)

Open `docs/export.html` directly in a browser (double-click, or serve statically). Then:

1. Drag and drop an Excel file onto the upload area, or click to browse.
2. Configure method, confidence, margin of error, stratification, and ID column.
3. Click **Plan sample** to preview stratum allocations, then **Generate sample** to run.
4. Optionally apply **GCI expansion** or **custom requirements** via the offer panels.
5. Download the sample (Excel) and JSON summary.

## Sampling methods

| Method | Description |
|---|---|
| `statistical` | Uses the standard proportion formula with finite population correction at the specified confidence level, tolerable error rate, and expected error rate. |
| `simple_random` | Random draw without stratification. Use `--sample-size` or `--sample-percentage` to fix the size. |
| `percentage` | Draw a fixed percentage of the population. |
| `systematic` | Every *k*-th record. Step is computed automatically or overridden with `--systematic-step`. |

## GCI jurisdiction expansion

When the ID column contains GCI identifiers, sampled GCIs may map to multiple rows in the population (e.g., multi-jurisdiction entities). After sampling, the tool detects this automatically and offers a one-click expansion to include all population rows for every sampled GCI. Expansion is recorded as an override in the JSON summary.

## Custom requirements

Accessible via the "Custom requirements" toggle in the form. Add rules of the form:

> *Column* — minimum unique GCIs: *N*

For example: "Jurisdiction = at least 10 unique GCIs." After generating a sample, click **Apply requirements** to run the constraint-satisfaction engine. It:

1. Derives the current set of selected GCIs from the sample.
2. Iteratively adds GCIs (seeded RNG, highest-deficit-first) until all minimums are met.
3. If a minimum is impossible given the population (insufficient distinct GCIs for a value), it caps and records a warning.
4. Expands the final sample to all population rows for the resolved GCI set.

Requirements are treated as overrides — a justification is required before downloading.

## JSON summary

Every download includes a `sampling_summary.json` with:

- **sample_source** — file name and sheet.
- **define_population** — total size, stratification fields, and per-stratum distribution.
- **sampling_rationale** — method, confidence level, error rates, and plain-language rationale notes.
- **sample_selection_method** — method, seed, calculated and final sizes, allocations by stratum, `id_expansion` block, and `requirements` block (rules, GCI counts added, warnings).
- **overrides** — flag, justification text, and details of every override applied.

## Python CLI (optional)

A command-line interface is also available for pipeline use:

```bash
cd "CIP CDD Sample Selection"
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

python -m cip_cdd_sample_selection ^
  --input path\to\data.xlsx ^
  --sheet Sheet1 ^
  --stratify Region,CustomerType ^
  --method statistical ^
  --confidence 0.99 ^
  --margin 0.05 ^
  --expected-error-rate 0.01 ^
  --seed 42 ^
  --output-dir outputs
```

### Key CLI options

| Option | Description |
|---|---|
| `--input` | Excel file (`.xlsx`, `.xls`, `.xlsm`, `.xlsb`). |
| `--sheet` | Sheet name (defaults to first sheet). |
| `--stratify` | Comma-separated columns to stratify by. |
| `--method` | `statistical` (default), `simple_random`, `percentage`, `systematic`. |
| `--confidence` | Confidence level, e.g. `0.99`. |
| `--margin` | Tolerable error rate, e.g. `0.05`. |
| `--expected-error-rate` | Expected error rate, e.g. `0.01`. |
| `--sample-size` | Fixed sample size override. |
| `--sample-percentage` | Percentage of population to sample. |
| `--systematic-step` | Interval for systematic sampling. |
| `--id-column` | Column used to identify rows in the output. |
| `--seed` | RNG seed for reproducibility. |
| `--output-dir` | Output folder for sample CSV and JSON summary. |

### Outputs

- `outputs/sample_<timestamp>.csv` — sampled rows.
- `outputs/sampling_summary_<timestamp>.json` — full audit trail.

## Limitations

- Expects Excel inputs with a header row.
- Statistical sizing uses a standard proportion formula with finite population correction; results are capped at the population size.
- The requirements engine runs in-browser; very large populations with many high-cardinality requirement columns may be slow.
