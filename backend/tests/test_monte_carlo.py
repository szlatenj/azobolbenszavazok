"""Integration tests for the Monte Carlo orchestrator."""

from __future__ import annotations

import pytest

from app.simulation.config import SimulationConfig
from app.simulation.monte_carlo import get_summary, run_simulation
from app.simulation.schemas import SimulationInput


class TestMonteCarlo:
    """Test the full simulation pipeline."""

    def test_basic_run(self):
        """Full simulation completes without errors."""
        config = SimulationConfig(n_simulations=100, random_seed=42)
        result = run_simulation(config=config)

        assert result.n_simulations == 100
        assert result.elapsed_seconds > 0
        assert len(result.party_names) > 0
        assert len(result.parties) > 0

    def test_total_seats_always_199(self):
        """Every simulation should produce exactly 199 total seats."""
        config = SimulationConfig(n_simulations=100, random_seed=42)
        result = run_simulation(config=config)

        for party_name, party_result in result.parties.items():
            n_sims = len(party_result.seat_distribution)
            assert n_sims == 100
            break  # just check first party for count

        # Check that total across all parties = 199 for each sim
        n_sims = config.n_simulations
        for sim_idx in range(n_sims):
            total = sum(
                pr.seat_distribution[sim_idx]
                for pr in result.parties.values()
            )
            assert total == 199, f"Simulation {sim_idx}: total seats = {total}"

    def test_probabilities_sum_reasonable(self):
        """Win probabilities should be between 0 and 1."""
        config = SimulationConfig(n_simulations=100, random_seed=42)
        result = run_simulation(config=config)

        for party_result in result.parties.values():
            assert 0 <= party_result.win_probability <= 1
            assert 0 <= party_result.supermajority_probability <= 1

    def test_reproducibility(self):
        """Same seed produces same results."""
        config = SimulationConfig(n_simulations=100, random_seed=123)
        r1 = run_simulation(config=config)
        r2 = run_simulation(config=config)

        for p in r1.party_names:
            assert r1.parties[p].mean_seats == r2.parties[p].mean_seats

    def test_custom_shares(self):
        """Custom vote shares override poll data."""
        input_data = SimulationInput(
            custom_shares={
                "fidesz": 0.45,
                "tisza": 0.35,
                "mi_hazank": 0.08,
                "dk": 0.04,
                "mkkp": 0.03,
                "other": 0.05,
            },
            n_simulations=100,
            random_seed=42,
        )
        result = run_simulation(input_data=input_data)
        assert result.n_simulations == 100
        assert "fidesz" in result.parties

    def test_summary_extraction(self):
        """Summary can be extracted from full result."""
        config = SimulationConfig(n_simulations=100, random_seed=42)
        result = run_simulation(config=config)
        summary = get_summary(result)

        assert summary.simulation_count == 100
        assert len(summary.parties) > 0
        assert len(summary.win_probabilities) > 0
