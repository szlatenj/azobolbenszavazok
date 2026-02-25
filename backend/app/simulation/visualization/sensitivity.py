"""Sensitivity analysis: vary parameters and observe impact on outcomes."""

from __future__ import annotations

from ..config import SimulationConfig
from ..monte_carlo import run_simulation
from ..schemas import SimulationInput


def run_sensitivity_analysis(
    base_config: SimulationConfig | None = None,
    target_party: str = "fidesz",
    n_simulations: int = 5000,
) -> list[dict]:
    """Run sensitivity analysis by varying key parameters.

    For each parameter, run the simulation at (base - delta) and (base + delta),
    then measure the change in win probability for the target party.

    Returns:
        List of dicts with 'parameter', 'low_value', 'high_value',
        'low_win_prob', 'high_win_prob', 'impact'.
    """
    if base_config is None:
        base_config = SimulationConfig(n_simulations=n_simulations, random_seed=42)

    # Parameters to vary with their deltas
    params = [
        ("sigma_polling_error", 0.01, 0.05),
        ("sigma_regional", 0.01, 0.04),
        ("sigma_district", 0.01, 0.03),
        ("poll_halflife_days", 7.0, 28.0),
    ]

    # Baseline
    baseline = run_simulation(config=base_config)
    baseline_prob = baseline.parties.get(target_party)
    if not baseline_prob:
        return []
    base_win = baseline_prob.win_probability

    results = []
    for param_name, low_val, high_val in params:
        # Low variant
        low_config = base_config.model_copy(update={param_name: low_val})
        low_result = run_simulation(config=low_config)
        low_prob = low_result.parties[target_party].win_probability

        # High variant
        high_config = base_config.model_copy(update={param_name: high_val})
        high_result = run_simulation(config=high_config)
        high_prob = high_result.parties[target_party].win_probability

        results.append({
            "parameter": param_name,
            "low_value": low_val,
            "high_value": high_val,
            "baseline_win_prob": base_win,
            "low_win_prob": low_prob,
            "high_win_prob": high_prob,
            "impact": abs(high_prob - low_prob),
        })

    # Sort by impact descending
    results.sort(key=lambda x: -x["impact"])
    return results
