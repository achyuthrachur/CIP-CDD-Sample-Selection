from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


Method = str
_MISSING_VALUE = "<MISSING>"


@dataclass
class SamplingConfig:
    method: Method = "statistical"
    confidence: float = 0.99
    margin: float = 0.05
    expected_error_rate: float = 0.01
    sample_size: Optional[int] = None
    sample_percentage: Optional[float] = None
    systematic_step: Optional[int] = None
    stratify_fields: List[str] = field(default_factory=list)
    id_column: Optional[str] = None
    seed: Optional[int] = 42
    systematic_random_start: bool = True

    def sanitized_method(self) -> Method:
        allowed = {"statistical", "simple_random", "percentage", "systematic"}
        if self.method not in allowed:
            raise ValueError(f"Unsupported method '{self.method}'. Choose from {sorted(allowed)}.")
        return self.method


def z_score(confidence: float) -> float:
    if confidence <= 0 or confidence >= 1:
        raise ValueError("Confidence must be between 0 and 1 (exclusive).")
    alpha = 1 - confidence
    # One-sided upper bound (z_{1-alpha}) to keep deviation rate under TER.
    return NormalDist().inv_cdf(1 - alpha)


def calculate_statistical_sample_size(
    population_size: int,
    confidence: float,
    margin: float,
    expected_error_rate: float,
) -> int:
    if population_size <= 0:
        return 0
    if margin <= 0 or margin >= 1:
        raise ValueError("Tolerable error rate must be in (0,1).")
    if expected_error_rate < 0 or expected_error_rate >= 1:
        raise ValueError("Expected error rate must be in [0,1).")
    if margin <= expected_error_rate:
        raise ValueError("Tolerable error rate must exceed expected error rate.")
    z = z_score(confidence)
    for n in range(1, population_size + 1):
        # Use expected deviations, rounded up, with a minimum of 1.
        expected_deviations = max(1, math.ceil(n * expected_error_rate))
        phat = expected_deviations / n
        ucl = phat + z * math.sqrt((phat * (1 - phat)) / n)
        if ucl <= margin:
            return n
    return population_size


def resolve_sample_size(population_size: int, cfg: SamplingConfig) -> int:
    method = cfg.sanitized_method()
    if population_size <= 0:
        return 0

    if method == "statistical":
        size = calculate_statistical_sample_size(
            population_size=population_size,
            confidence=cfg.confidence,
            margin=cfg.margin,
            expected_error_rate=cfg.expected_error_rate,
        )
    elif method == "percentage":
        if cfg.sample_percentage is None:
            raise ValueError("sample_percentage is required for percentage sampling.")
        size = math.ceil(population_size * (cfg.sample_percentage / 100))
    elif method == "simple_random":
        if cfg.sample_size is None and cfg.sample_percentage is None:
            raise ValueError("Provide sample_size or sample_percentage for simple_random sampling.")
        if cfg.sample_size is not None:
            size = cfg.sample_size
        else:
            size = math.ceil(population_size * (cfg.sample_percentage / 100))
    elif method == "systematic":
        if cfg.sample_size is not None:
            size = cfg.sample_size
        elif cfg.sample_percentage is not None:
            size = math.ceil(population_size * (cfg.sample_percentage / 100))
        else:
            size = calculate_statistical_sample_size(
                population_size=population_size,
                confidence=cfg.confidence,
                margin=cfg.margin,
                expected_error_rate=cfg.expected_error_rate,
            )
    else:
        raise ValueError(f"Unsupported method {method}")

    size = max(0, min(population_size, int(size)))
    return size


def _normalize_key(values: Tuple[Any, ...]) -> Tuple[Any, ...]:
    normalized = []
    for value in values:
        if pd.isna(value):
            normalized.append(_MISSING_VALUE)
        else:
            normalized.append(value)
    return tuple(normalized)


def proportional_allocation(counts: pd.Series, total_size: int) -> Dict[Tuple, int]:
    """
    Allocate sample counts to strata proportionally, respecting capacity and total size.
    """
    if total_size <= 0 or counts.sum() == 0:
        return {idx: 0 for idx in counts.index}

    raw = counts / counts.sum() * total_size
    base = raw.apply(math.floor).astype(int)

    remainder = total_size - base.sum()
    if remainder > 0:
        fractional = (raw - base).sort_values(ascending=False)
        for idx in fractional.index[:remainder]:
            base[idx] += 1

    # Ensure at least one per stratum when possible.
    if total_size >= len(counts):
        for idx, cnt in counts.items():
            if cnt > 0 and base[idx] == 0:
                base[idx] = 1

    # Cap by stratum capacity.
    capped = base.clip(upper=counts)

    # Adjust downward if we exceeded the total because of caps.
    while capped.sum() > total_size:
        excess = capped.sum() - total_size
        reducible = capped[capped > 0].sort_values(ascending=False)
        for idx in reducible.index:
            if excess <= 0:
                break
            capped[idx] -= 1
            excess -= 1

    # Redistribute any leftover capacity.
    target = min(total_size, int(counts.sum()))
    while capped.sum() < target:
        needed = target - capped.sum()
        available = (counts - capped).sort_values(ascending=False)
        if available.sum() == 0:
            break
        for idx, remaining in available.items():
            if needed <= 0:
                break
            if remaining > 0:
                capped[idx] += 1
                needed -= 1

    return {idx: int(val) for idx, val in capped.items()}


def systematic_sample(df: pd.DataFrame, desired_size: int, cfg: SamplingConfig, rng: np.random.Generator) -> pd.DataFrame:
    if desired_size <= 0 or df.empty:
        return df.iloc[0:0]
    population_size = len(df)
    if desired_size >= population_size:
        return df.copy()

    step = cfg.systematic_step or math.ceil(population_size / desired_size)
    start = rng.integers(0, step) if cfg.systematic_random_start else 0
    indices = list(range(start, population_size, step))[:desired_size]
    return df.iloc[indices]


def random_sample(df: pd.DataFrame, desired_size: int, seed: Optional[int]) -> pd.DataFrame:
    if desired_size <= 0 or df.empty:
        return df.iloc[0:0]
    desired_size = min(len(df), desired_size)
    return df.sample(n=desired_size, random_state=seed)


def stratified_sample(
    df: pd.DataFrame,
    cfg: SamplingConfig,
    rng: np.random.Generator,
    desired_size: Optional[int] = None,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    stratify_fields = cfg.stratify_fields
    total_size = resolve_sample_size(len(df), cfg) if desired_size is None else desired_size
    if total_size <= 0:
        return df.iloc[0:0], []

    group_counts = df.groupby(stratify_fields, dropna=False).size()
    normalized_index = [
        _normalize_key(idx if isinstance(idx, tuple) else (idx,)) for idx in group_counts.index
    ]
    normalized_counts = pd.Series(group_counts.values, index=pd.Index(normalized_index))
    allocations = proportional_allocation(normalized_counts, total_size)
    actual_total = sum(allocations.values())

    samples = []
    allocation_summary: List[Dict[str, Any]] = []
    for idx, group_df in df.groupby(stratify_fields, dropna=False):
        stratum_key = idx if isinstance(idx, tuple) else (idx,)
        allocated = allocations.get(_normalize_key(stratum_key), 0)
        if allocated <= 0:
            continue
        if cfg.method == "systematic":
            sample_df = systematic_sample(group_df, allocated, cfg, rng)
        else:
            sample_df = random_sample(group_df, allocated, cfg.seed)
        samples.append(sample_df)
        allocation_summary.append(
            {
                "stratum": _stratum_dict(stratify_fields, stratum_key),
                "population_count": int(len(group_df)),
                "sample_count": int(len(sample_df)),
                "share_of_population": len(group_df) / len(df) if len(df) else 0,
                "share_of_sample": len(sample_df) / actual_total if actual_total else 0,
            }
        )

    if samples:
        combined = pd.concat(samples, axis=0).reset_index(drop=True)
    else:
        combined = df.iloc[0:0]
    return combined, allocation_summary


def sample_dataframe(df: pd.DataFrame, cfg: SamplingConfig) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    desired_size = resolve_sample_size(len(df), cfg)
    if desired_size <= 0 and len(df) > 0:
        raise ValueError("Calculated sample size is 0. Adjust parameters to select at least one record.")

    rng = np.random.default_rng(cfg.seed)
    if cfg.stratify_fields:
        sample_df, allocation_summary = stratified_sample(df, cfg, rng, desired_size=desired_size)
    else:
        if cfg.method == "systematic":
            sample_df = systematic_sample(df, desired_size, cfg, rng)
        else:
            sample_df = random_sample(df, desired_size, cfg.seed)
        allocation_summary = []

    sample_df = sample_df.reset_index(drop=True)
    summary = build_summary(df, sample_df, allocation_summary, cfg, desired_size)
    return sample_df, summary


def build_summary(
    population_df: pd.DataFrame,
    sample_df: pd.DataFrame,
    allocation_summary: List[Dict[str, Any]],
    cfg: SamplingConfig,
    planned_sample_size: Optional[int],
) -> Dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    stratify_fields = cfg.stratify_fields

    summary: Dict[str, Any] = {
        "generated_at_utc": timestamp,
        "methodology": {
            "method": cfg.method,
            "confidence": cfg.confidence,
            "margin": cfg.margin,
            "expected_error_rate": cfg.expected_error_rate,
            "sample_size_parameter": cfg.sample_size,
            "sample_percentage_parameter": cfg.sample_percentage,
            "systematic_step_parameter": cfg.systematic_step,
            "seed": cfg.seed,
            "systematic_random_start": cfg.systematic_random_start,
            "planned_sample_size": planned_sample_size,
        },
        "stratify_fields": stratify_fields,
        "population": {
            "size": int(len(population_df)),
            "distribution": distribution(population_df, stratify_fields),
        },
        "sample": {
            "size": int(len(sample_df)),
            "distribution": distribution(sample_df, stratify_fields),
        },
        "allocations": allocation_summary,
    }

    if cfg.id_column and cfg.id_column in sample_df.columns:
        summary["sample_ids"] = sample_df[cfg.id_column].tolist()

    return summary


def distribution(df: pd.DataFrame, stratify_fields: Iterable[str]) -> List[Dict[str, Any]]:
    fields = list(stratify_fields)
    if not fields or df.empty:
        return []
    total = len(df)
    grouped = df.groupby(fields, dropna=False).size().reset_index(name="count")
    records: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        stratum_values = tuple(row[field] for field in fields)
        records.append(
            {
                "stratum": _stratum_dict(fields, stratum_values),
                "count": int(row["count"]),
                "share": float(row["count"] / total),
            }
        )
    return records


def _stratum_dict(fields: List[str], values: Tuple[Any, ...]) -> Dict[str, Any]:
    cleaned = {}
    for field, value in zip(fields, values):
        if pd.isna(value):
            cleaned[field] = None
        elif isinstance(value, pd.Timestamp):
            cleaned[field] = value.isoformat()
        elif isinstance(value, np.generic):
            cleaned[field] = value.item()
        else:
            cleaned[field] = value
    return cleaned
