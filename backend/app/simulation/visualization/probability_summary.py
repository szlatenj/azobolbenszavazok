"""Probability summary and dashboard data generation."""

from __future__ import annotations

from ..schemas import SimulationResult


def compute_probability_summary(result: SimulationResult) -> dict:
    """Compute a human-readable probability summary.

    Returns:
        Dict with narrative text, party stats, and key probabilities.
    """
    parties = result.parties
    n = result.n_simulations

    # Find parties with non-trivial win probability
    significant = {
        p: r for p, r in parties.items()
        if r.win_probability > 0.001
    }

    # Build narrative
    lines = []
    for party, r in sorted(significant.items(), key=lambda x: -x[1].win_probability):
        pct = r.win_probability * 100
        lines.append(f"{party} wins a majority in {pct:.1f}% of simulations.")

    if result.no_majority_probability > 0.001:
        lines.append(
            f"No party wins a majority in {result.no_majority_probability * 100:.1f}% of simulations."
        )

    # Supermajority text
    for party, r in parties.items():
        if r.supermajority_probability > 0.001:
            pct = r.supermajority_probability * 100
            lines.append(f"{party} achieves a supermajority (133+) in {pct:.1f}% of simulations.")

    # Per-party credible intervals
    party_stats = {}
    for party, r in parties.items():
        party_stats[party] = {
            "mean_seats": r.mean_seats,
            "median_seats": r.median_seats,
            "ci_80": [r.percentile_5, r.percentile_95],  # actually 90% CI
            "ci_50": [r.percentile_25, r.percentile_75],
            "win_probability": r.win_probability,
            "supermajority_probability": r.supermajority_probability,
        }

    return {
        "narrative": " ".join(lines),
        "party_stats": party_stats,
        "most_likely_government": result.most_likely_government,
        "no_majority_probability": result.no_majority_probability,
        "n_simulations": n,
    }
