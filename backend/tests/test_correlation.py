"""Tests for correlated vote share drawing."""

from __future__ import annotations

import numpy as np
import pytest

from app.simulation.config import SimulationConfig
from app.simulation.correlation import draw_national_shares


class TestCorrelation:
    """Test correlated national vote share draws."""

    def test_output_shape(self, config, rng):
        """Output has correct shape (N, K)."""
        shares = {"fidesz": 0.45, "tisza": 0.35, "mi_hazank": 0.10, "other": 0.10}
        result, parties = draw_national_shares(shares, 100, config, rng)

        assert result.shape == (100, 4)
        assert len(parties) == 4

    def test_rows_sum_to_one(self, config, rng):
        """Every simulation's shares sum to 1.0."""
        shares = {"fidesz": 0.45, "tisza": 0.35, "other": 0.20}
        result, _ = draw_national_shares(shares, 500, config, rng)

        row_sums = result.sum(axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=0.001)

    def test_shares_positive(self, config, rng):
        """All shares are positive."""
        shares = {"fidesz": 0.45, "tisza": 0.35, "mi_hazank": 0.10, "other": 0.10}
        result, _ = draw_national_shares(shares, 1000, config, rng)

        assert (result > 0).all()

    def test_mean_approximates_input(self, rng):
        """With many draws, mean should be close to input shares."""
        shares = {"fidesz": 0.45, "tisza": 0.35, "other": 0.20}
        config = SimulationConfig(
            n_simulations=10000,
            random_seed=42,
            sigma_polling_error=0.01,  # small error for tighter convergence
        )
        result, parties = draw_national_shares(shares, 10000, config, rng)

        means = result.mean(axis=0)
        for i, p in enumerate(parties):
            assert means[i] == pytest.approx(shares[p], abs=0.03)

    def test_reproducible_with_seed(self, config):
        """Same seed produces same results."""
        shares = {"fidesz": 0.45, "tisza": 0.35, "other": 0.20}
        rng1 = np.random.default_rng(123)
        rng2 = np.random.default_rng(123)

        r1, _ = draw_national_shares(shares, 50, config, rng1)
        r2, _ = draw_national_shares(shares, 50, config, rng2)

        np.testing.assert_array_equal(r1, r2)
