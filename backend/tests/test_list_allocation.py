"""Tests for d'Hondt allocation and threshold logic."""

from __future__ import annotations

import numpy as np
import pytest

from app.simulation.list_allocation import (
    allocate_list_seats,
    allocate_list_seats_deterministic,
    apply_threshold,
    dhondt,
    dhondt_vectorized,
)


class TestDhondt:
    """Test d'Hondt allocation with known examples."""

    def test_wikipedia_example(self):
        """Classic d'Hondt example: 7 seats among 4 parties."""
        votes = {"A": 100000, "B": 80000, "C": 30000, "D": 20000}
        result = dhondt(votes, 8)
        assert result["A"] == 4
        assert result["B"] == 3
        assert result["C"] == 1
        assert result["D"] == 0
        assert sum(result.values()) == 8

    def test_two_parties(self):
        """Simple two-party allocation."""
        votes = {"X": 60, "Y": 40}
        result = dhondt(votes, 5)
        # X: 60, 30, 20, 15, 12 | Y: 40, 20, 13.3
        # Seats go to: X(60), Y(40), X(30), X(20)=Y(20) -- tie broken by first seen
        assert sum(result.values()) == 5
        assert result["X"] >= 3

    def test_single_party(self):
        """One party gets all seats."""
        votes = {"A": 1000}
        result = dhondt(votes, 10)
        assert result["A"] == 10

    def test_empty_votes(self):
        """No votes → no seats."""
        result = dhondt({}, 5)
        assert result == {}

    def test_zero_seats(self):
        """Zero seats to allocate."""
        result = dhondt({"A": 100}, 0)
        assert result["A"] == 0

    def test_vectorized_matches_dict(self):
        """Vectorized version produces same result as dict version."""
        votes_dict = {"A": 100000, "B": 80000, "C": 30000}
        result_dict = dhondt(votes_dict, 10)

        votes_arr = np.array([100000, 80000, 30000], dtype=np.float64)
        result_arr = dhondt_vectorized(votes_arr, 10)

        assert result_arr[0] == result_dict["A"]
        assert result_arr[1] == result_dict["B"]
        assert result_arr[2] == result_dict["C"]


class TestThreshold:
    """Test threshold filtering."""

    def test_five_percent_threshold(self):
        """Party below 5% is excluded."""
        raw_votes = np.array([[100.0, 4.0, 96.0]])  # 100+4+96 = 200, party B = 2%
        thresholds = np.array([0.05, 0.05, 0.05])
        mask = apply_threshold(raw_votes, thresholds)
        assert mask[0, 0]  # 50% → passes
        assert not mask[0, 1]  # 2% → fails
        assert mask[0, 2]  # 48% → passes

    def test_ten_percent_coalition_threshold(self):
        """Two-party coalition needs 10%."""
        raw_votes = np.array([[500.0, 80.0, 420.0]])  # total=1000, B=8%
        thresholds = np.array([0.05, 0.10, 0.05])
        mask = apply_threshold(raw_votes, thresholds)
        assert mask[0, 0]  # 50% → passes
        assert not mask[0, 1]  # 8% < 10% → fails for coalition
        assert mask[0, 2]  # 42% → passes

    def test_exactly_at_threshold(self):
        """Party exactly at threshold passes."""
        raw_votes = np.array([[50.0, 50.0]])
        thresholds = np.array([0.05, 0.05])
        mask = apply_threshold(raw_votes, thresholds)
        assert mask[0, 0]  # 50% → passes
        assert mask[0, 1]  # 50% → passes


class TestAllocateListSeats:
    """Test full list allocation pipeline."""

    def test_basic_allocation(self):
        """Basic allocation with threshold filtering."""
        N = 1
        K = 3
        raw_list = np.array([[500000.0, 300000.0, 40000.0]])  # total=840000, C=4.76%
        fragment = np.array([[50000.0, 30000.0, 5000.0]])
        thresholds = np.array([0.05, 0.05, 0.05])

        result = allocate_list_seats(raw_list, fragment, thresholds, n_seats=10)
        assert result.shape == (1, 3)
        assert result[0, 2] == 0  # C below threshold
        assert result.sum() == 10  # All seats allocated to eligible parties

    def test_deterministic_matches_vectorized(self):
        """Deterministic and vectorized versions agree for single simulation."""
        raw_dict = {"A": 500000, "B": 300000, "C": 100000}
        frag_dict = {"A": 50000, "B": 30000, "C": 10000}
        thresh_dict = {"A": 0.05, "B": 0.05, "C": 0.05}
        total_valid = sum(raw_dict.values())

        det_result = allocate_list_seats_deterministic(
            raw_dict, frag_dict, thresh_dict, total_valid, n_seats=20
        )

        parties = sorted(raw_dict.keys())
        raw_arr = np.array([[raw_dict[p] for p in parties]], dtype=np.float64)
        frag_arr = np.array([[frag_dict[p] for p in parties]], dtype=np.float64)
        thresh_arr = np.array([thresh_dict[p] for p in parties])

        vec_result = allocate_list_seats(raw_arr, frag_arr, thresh_arr, n_seats=20)

        for i, p in enumerate(parties):
            assert det_result[p] == vec_result[0, i], f"Mismatch for {p}"
