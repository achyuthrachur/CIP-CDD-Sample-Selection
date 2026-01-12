# CIP CDD Sample Selection

Command-line sampler for CIP/CDD testing. It ingests an Excel file, lets you pick a sampling methodology (default statistical with 99% confidence, 5% tolerable error rate, 1% expected error rate), stratify by one or more columns, and produces:
- A sampled file (CSV).
- A JSON summary with methodology, parameters, and population vs. sample distributions for report-ready rationale.

## Quick start
```bash
cd "CIP CDD Sample Selection"
python -m venv .venv
.venv\Scripts\activate  # on Windows
pip install -r requirements.txt
```

### Zero-install HTML app
- Open `docs/index.html` in a browser (double-click locally or serve statically). Everything runs client-side—no Python needed.
- Drag and drop an Excel file, choose methodology/stratification, click “Generate sample,” then download the sample CSV and JSON summary.

## Usage
```bash
python -m cip_cdd_sample_selection ^
  --input path\to\data.xlsx ^
  --sheet Sheet1 ^
  --stratify Region,CustomerType ^
  --method statistical ^
  --confidence 0.99 ^
  --margin 0.05 ^
  --expected-error-rate 0.01 ^
  --output-dir outputs
```

### Key options
- `--input`: Excel file to read. Supports `.xlsx`, `.xls`, `.xlsm`, `.xlsb` (via `pandas`).
- `--sheet`: Optional sheet name (defaults to first sheet).
- `--stratify`: Comma-separated column names to stratify the sample.
- `--method`: `statistical` (default), `simple_random`, `percentage`, or `systematic`.
- `--confidence`, `--margin`, `--expected-error-rate`: Used for `statistical` sample sizing (defaults 0.99/0.05/0.01). `--margin` is the tolerable error rate (TER).
- `--sample-size`: Fixed sample size (use with `simple_random` or `systematic`, optional with others).
- `--sample-percentage`: Percentage of population to sample (e.g., `10` for 10%).
- `--systematic-step`: Interval for systematic sampling (defaults to a computed interval).
- `--id-column`: Optional column name to identify rows in the output.
- `--seed`: RNG seed for reproducible sampling.
- `--output-dir`: Folder for outputs (sample CSV and JSON summary).

### Outputs
- Sampled data: `outputs/sample_<timestamp>.csv`
- JSON summary: `outputs/sampling_summary_<timestamp>.json`

The JSON includes:
- Methodology and parameters used.
- Population size and stratification distributions.
- Sample size and stratification distributions.
- Strata-level allocations and metadata sufficient to document rationale.

## Example
Simple random sample with stratification on `Region` and `RiskBand`:
```bash
python -m cip_cdd_sample_selection ^
  --input data.xlsx ^
  --stratify Region,RiskBand ^
  --method simple_random ^
  --sample-size 150
```

Systematic sample taking ~10% of the population with stratification:
```bash
python -m cip_cdd_sample_selection ^
  --input data.xlsx ^
  --method systematic ^
  --sample-percentage 10 ^
  --stratify Country
```

## Repository notes
A local Git repository can be initialized with:
```bash
git init
git add .
git commit -m "Initialize CIP CDD Sample Selection sampler"
```
Create a GitHub repo named `CIP CDD Sample Selection`, then:
```bash
git remote add origin https://github.com/<your-account>/CIP-CDD-Sample-Selection.git
git push -u origin main
```

## Limitations and assumptions
- Designed for Excel inputs with a header row.
- Statistical sizing uses a one-sided upper confidence bound on the deviation rate (attribute sampling); values are capped at the population size.
- Large samples will make the JSON sizable; adjust as needed.
