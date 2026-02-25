"""Tests for poll aggregation logic."""

from __future__ import annotations

from datetime import date

import pytest

from app.simulation.config import PollsterConfig, SimulationConfig
from app.simulation.poll_aggregator import aggregate_polls


def _make_poll(
    d: str, pollster: str, sample_size: int, shares: dict[str, float]
) -> dict:
    return {
        "date": date.fromisoformat(d),
        "pollster": pollster,
        "sample_size": sample_size,
        "population": "certain_voters",
        "shares": shares,
    }


class TestPollAggregator:
    """Test poll weighting and aggregation."""

    def test_single_poll(self):
        """Single poll returns its own shares (normalized)."""
        polls = [
            _make_poll("2026-02-15", "Test", 1000, {"fidesz": 0.45, "tisza": 0.35, "other": 0.20})
        ]
        config = SimulationConfig()
        means, unc = aggregate_polls(polls, date(2026, 2, 15), config)

        assert means["fidesz"] == pytest.approx(0.45, abs=0.01)
        assert means["tisza"] == pytest.approx(0.35, abs=0.01)

    def test_recent_poll_weighted_higher(self):
        """More recent polls should have higher influence."""
        polls = [
            _make_poll("2026-02-14", "A", 1000, {"fidesz": 0.50, "tisza": 0.50}),
            _make_poll("2026-01-01", "B", 1000, {"fidesz": 0.30, "tisza": 0.70}),
        ]
        config = SimulationConfig(poll_halflife_days=14.0)
        means, _ = aggregate_polls(polls, date(2026, 2, 15), config)

        # Recent poll says 50/50, old poll says 30/70
        # With 14-day halflife, the old poll (45 days) has much less weight
        # Result should be much closer to 50/50
        assert means["fidesz"] > 0.45

    def test_larger_sample_weighted_higher(self):
        """Larger sample sizes get more weight."""
        polls = [
            _make_poll("2026-02-15", "A", 2000, {"fidesz": 0.50, "tisza": 0.50}),
            _make_poll("2026-02-15", "B", 500, {"fidesz": 0.30, "tisza": 0.70}),
        ]
        config = SimulationConfig()
        means, _ = aggregate_polls(polls, date(2026, 2, 15), config)

        # Larger sample poll says 50/50, should dominate
        assert means["fidesz"] > 0.40

    def test_house_effect_correction(self):
        """Pollster house effects are applied before averaging."""
        polls = [
            _make_poll("2026-02-15", "Biased", 1000, {"fidesz": 0.50, "tisza": 0.30, "other": 0.20})
        ]
        config = SimulationConfig(
            pollster_configs={
                "Biased": PollsterConfig(
                    quality_weight=1.0,
                    house_effects={"fidesz": -5.0}  # subtract 5 points
                )
            }
        )
        means, _ = aggregate_polls(polls, date(2026, 2, 15), config)

        # After correction: fidesz = 0.50 - 0.05 = 0.45, but normalization shifts it
        # Original: 0.45 + 0.30 + 0.20 = 0.95, normalized fidesz = 0.45/0.95 ≈ 0.474
        assert means["fidesz"] < 0.50  # Correction reduced it from 0.50

    def test_shares_sum_to_one(self):
        """Output shares always sum to 1.0."""
        polls = [
            _make_poll("2026-02-15", "A", 1000, {"a": 0.4, "b": 0.3, "c": 0.2, "d": 0.1})
        ]
        config = SimulationConfig()
        means, _ = aggregate_polls(polls, date(2026, 2, 15), config)
        assert sum(means.values()) == pytest.approx(1.0, abs=0.001)

    def test_no_polls_raises(self):
        """Empty poll list raises ValueError."""
        config = SimulationConfig()
        with pytest.raises(ValueError):
            aggregate_polls([], date(2026, 2, 15), config)
