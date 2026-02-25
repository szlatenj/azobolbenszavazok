"""Tests for district simulation and fragment vote calculation."""

from __future__ import annotations

import numpy as np
import pytest

from app.simulation.district_sim import simulate_smds, simulate_smds_deterministic


class TestFragmentVotes:
    """Test fragment vote calculation logic."""

    def test_simple_three_candidate_district(self):
        """Hand-calculated fragment votes for a single district."""
        # One district, 3 parties, 1 simulation
        # Votes: A=50, B=30, C=20
        # Winner: A (50 votes)
        # Second: B (30 votes)
        # Fragment A (winner): 50 - 30 - 1 = 19
        # Fragment B (loser): 30
        # Fragment C (loser): 20
        district_shares = np.array([[[0.5, 0.3, 0.2]]])  # (1, 1, 3)
        district_total_votes = np.array([100.0])

        smd_seats, fragment = simulate_smds(district_shares, district_total_votes, ["A", "B", "C"])

        assert smd_seats[0, 0] == 1  # A wins
        assert smd_seats[0, 1] == 0
        assert smd_seats[0, 2] == 0

        assert fragment[0, 0] == pytest.approx(19.0, abs=0.5)  # winner fragment
        assert fragment[0, 1] == pytest.approx(30.0, abs=0.5)  # loser B
        assert fragment[0, 2] == pytest.approx(20.0, abs=0.5)  # loser C

    def test_two_districts_different_winners(self):
        """Two districts with different winners."""
        # District 1: A=60, B=40 → A wins, frag A=60-40-1=19, frag B=40
        # District 2: A=30, B=70 → B wins, frag B=70-30-1=39, frag A=30
        # Total frag: A=19+30=49, B=40+39=79
        shares = np.array([[[0.6, 0.4], [0.3, 0.7]]])  # (1, 2, 2)
        totals = np.array([100.0, 100.0])

        smd_seats, fragment = simulate_smds(shares, totals, ["A", "B"])

        assert smd_seats[0, 0] == 1  # A wins district 1
        assert smd_seats[0, 1] == 1  # B wins district 2

        assert fragment[0, 0] == pytest.approx(49.0, abs=1.0)
        assert fragment[0, 1] == pytest.approx(79.0, abs=1.0)

    def test_winner_fragment_never_negative(self):
        """Winner fragment is clamped to >= 0 when margin is very tight."""
        # Close race: A=51, B=49 → winner frag = 51-49-1 = 1
        shares = np.array([[[0.51, 0.49]]])
        totals = np.array([100.0])

        _, fragment = simulate_smds(shares, totals, ["A", "B"])
        assert fragment[0, 0] >= 0
        assert fragment[0, 1] >= 0

    def test_total_seats_equals_districts(self):
        """Total SMD seats across all parties = number of districts."""
        N, D, K = 10, 5, 3
        rng = np.random.default_rng(42)
        shares = rng.dirichlet(np.ones(K), size=(N, D))  # random valid shares
        totals = np.full(D, 1000.0)

        smd_seats, _ = simulate_smds(shares, totals, [f"P{i}" for i in range(K)])
        assert (smd_seats.sum(axis=1) == D).all()


class TestDeterministicSMD:
    """Test deterministic SMD simulation for backtesting."""

    def test_simple_case(self):
        """Basic deterministic test."""
        district_votes = {
            1: {"A": 100, "B": 80, "C": 20},
            2: {"A": 60, "B": 90, "C": 50},
        }
        parties = ["A", "B", "C"]

        smd_seats, fragment = simulate_smds_deterministic(district_votes, parties)

        assert smd_seats["A"] == 1
        assert smd_seats["B"] == 1
        assert smd_seats["C"] == 0

        # District 1: A wins. Frag A = 100-80-1=19, Frag B=80, Frag C=20
        # District 2: B wins. Frag B = 90-60-1=29, Frag A=60, Frag C=50
        assert fragment["A"] == 19 + 60  # = 79
        assert fragment["B"] == 80 + 29  # = 109
        assert fragment["C"] == 20 + 50  # = 70
