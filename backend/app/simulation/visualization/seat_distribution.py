"""Seat distribution histogram data generation."""

from __future__ import annotations

import numpy as np

from ..schemas import SimulationResult


def compute_seat_histogram(
    result: SimulationResult,
    party: str,
    bin_width: int = 1,
) -> dict:
    """Compute histogram data for a party's seat distribution.

    Returns:
        Dict with 'bins', 'counts', 'mean', 'median', 'majority_line', 'supermajority_line'.
    """
    seats = np.array(result.parties[party].seat_distribution)
    bins = np.arange(seats.min(), seats.max() + bin_width + 1, bin_width)
    counts, bin_edges = np.histogram(seats, bins=bins)

    return {
        "party": party,
        "bins": bin_edges[:-1].tolist(),
        "counts": counts.tolist(),
        "mean": float(np.mean(seats)),
        "median": int(np.median(seats)),
        "std": float(np.std(seats)),
        "min": int(seats.min()),
        "max": int(seats.max()),
        "majority_line": 100,
        "supermajority_line": 133,
        "n_simulations": len(seats),
    }


def compute_all_histograms(result: SimulationResult) -> list[dict]:
    """Compute histograms for all parties."""
    return [
        compute_seat_histogram(result, party)
        for party in result.party_names
    ]
