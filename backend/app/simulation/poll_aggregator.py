"""Poll aggregation with recency, sample size, and pollster quality weighting."""

from __future__ import annotations

import csv
import math
from datetime import date
from pathlib import Path

import numpy as np

from .config import SimulationConfig


def load_polls_csv(path: Path) -> list[dict]:
    """Load polling data from CSV.

    Expected columns: date, pollster, sample_size, population,
    then one column per party short name with vote share (0-1).

    Returns:
        List of poll dicts with keys: date, pollster, sample_size, population, shares.
    """
    polls = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        party_columns = [
            c for c in reader.fieldnames or []
            if c not in ("date", "pollster", "sample_size", "population")
        ]
        for row in reader:
            shares = {}
            for col in party_columns:
                val = row.get(col, "")
                if val:
                    shares[col] = float(val)
            polls.append({
                "date": date.fromisoformat(row["date"]),
                "pollster": row["pollster"],
                "sample_size": int(row["sample_size"]),
                "population": row.get("population", "certain_voters"),
                "shares": shares,
            })
    return polls


def aggregate_polls(
    polls: list[dict],
    reference_date: date,
    config: SimulationConfig,
    party_names: list[str] | None = None,
) -> tuple[dict[str, float], dict[str, float]]:
    """Compute weighted average national vote shares from polling data.

    Args:
        polls: List of poll dicts from load_polls_csv.
        reference_date: Date to compute recency from.
        config: Simulation configuration with weighting params.
        party_names: If provided, only aggregate these parties.

    Returns:
        (mean_shares, uncertainty) — both are dict[party_short → float].
    """
    if not polls:
        raise ValueError("No polls provided")

    # Determine party names from first poll if not specified
    if party_names is None:
        party_names = sorted(polls[0]["shares"].keys())

    # Get pollster configs
    pollster_configs = config.pollster_configs

    # Compute weights and collect data
    decay_rate = math.log(2) / config.poll_halflife_days

    weights = []
    share_matrix = []  # each row = poll, each col = party

    for poll in polls:
        # Filter by population preference
        if poll["population"] not in ("certain_voters", "likely_voters"):
            continue

        # Recency weight
        days_old = (reference_date - poll["date"]).days
        if days_old < 0:
            continue  # future poll
        weight_time = math.exp(-decay_rate * days_old)

        # Sample size weight
        weight_n = math.sqrt(poll["sample_size"] / 1000.0)

        # Pollster quality weight
        pc = pollster_configs.get(poll["pollster"])
        weight_quality = pc.quality_weight if pc else 1.0

        total_weight = weight_time * weight_n * weight_quality

        # Apply house effect corrections
        shares = dict(poll["shares"])
        if pc and pc.house_effects:
            for party, effect in pc.house_effects.items():
                if party in shares:
                    shares[party] += effect / 100.0  # effect is in percentage points

        # Build share vector for this poll
        share_vec = [shares.get(p, 0.0) for p in party_names]

        weights.append(total_weight)
        share_matrix.append(share_vec)

    if not weights:
        raise ValueError("No valid polls after filtering")

    weights_arr = np.array(weights)
    shares_arr = np.array(share_matrix)  # (n_polls, K)

    # Normalize weights
    weights_arr /= weights_arr.sum()

    # Weighted mean
    mean_shares = (weights_arr[:, np.newaxis] * shares_arr).sum(axis=0)  # (K,)

    # Weighted standard deviation
    diff = shares_arr - mean_shares[np.newaxis, :]  # (n_polls, K)
    weighted_var = (weights_arr[:, np.newaxis] * diff ** 2).sum(axis=0)
    uncertainty = np.sqrt(weighted_var)

    # Apply floor uncertainty
    uncertainty = np.maximum(uncertainty, config.floor_uncertainty)

    # Normalize mean shares to sum to 1
    total = mean_shares.sum()
    if total > 0:
        mean_shares = mean_shares / total

    mean_dict = {p: float(mean_shares[i]) for i, p in enumerate(party_names)}
    unc_dict = {p: float(uncertainty[i]) for i, p in enumerate(party_names)}

    return mean_dict, unc_dict
