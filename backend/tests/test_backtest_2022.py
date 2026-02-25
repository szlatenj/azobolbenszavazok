"""Backtest: verify that feeding actual 2022 data reproduces the real seat allocation.

Official 2022 results:
- Fidesz-KDNP: 135 seats (87 SMD + 48 list)
- Opposition (Egységben): 57 seats (19 SMD + 38 list)
- Mi Hazánk: 6 seats (0 SMD + 6 list)
- MNOÖ (German minority): 1 seat (nationality list — we ignore this)
Total: 199 seats (we model 199 - 1 minority = 198 via party lists + SMDs)
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.simulation.district_sim import simulate_smds_deterministic
from app.simulation.list_allocation import allocate_list_seats_deterministic

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "simulation" / "data"

# Official 2022 national list results (party lists only, excluding nationality)
NATIONAL_LIST_2022 = {
    "fidesz": 3_060_706,
    "opposition": 1_947_331,
    "mi_hazank": 332_487,
    "mkkp": 185_052,
    "other": 98_649,  # MEMO + Normális Párt
}

PARTY_THRESHOLDS_2022 = {
    "fidesz": 0.10,      # Fidesz-KDNP = 2-party coalition
    "opposition": 0.15,   # 6-party coalition
    "mi_hazank": 0.05,
    "mkkp": 0.05,
    "other": 0.05,
}

# Expected results
EXPECTED_SMD = {"fidesz": 87, "opposition": 19, "mi_hazank": 0, "mkkp": 0, "other": 0}
# Note: official list seats are 48+38+6=92 (+ 1 nationality = 93 total)
# Our model allocates 93 list seats without nationality lists
# so the numbers will be slightly different from official (92 party list + 1 nationality)


def _load_district_votes() -> dict[int, dict[str, int]]:
    """Load 2022 district data in deterministic format."""
    path = DATA_DIR / "districts_2022.csv"
    districts = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            did = int(row["district_id"])
            districts[did] = {
                "fidesz": int(row["fidesz_votes"]),
                "opposition": int(row["opposition_votes"]),
                "mi_hazank": int(row["mi_hazank_votes"]),
                "mkkp": int(row["mkkp_votes"]),
                "other": int(row["other_votes"]),
            }
    return districts


class TestBacktest2022:
    """Verify deterministic allocation matches 2022 actual results."""

    def test_smd_seats_match(self):
        """SMD winners must exactly match 2022 results."""
        district_votes = _load_district_votes()
        party_names = list(EXPECTED_SMD.keys())

        smd_seats, fragment_votes = simulate_smds_deterministic(district_votes, party_names)

        for party, expected in EXPECTED_SMD.items():
            assert smd_seats[party] == expected, \
                f"SMD seats for {party}: got {smd_seats[party]}, expected {expected}"

        # Total SMD seats = 106
        assert sum(smd_seats.values()) == 106

    def test_total_fragment_votes_positive(self):
        """All parties should have non-negative fragment votes."""
        district_votes = _load_district_votes()
        party_names = list(EXPECTED_SMD.keys())

        _, fragment_votes = simulate_smds_deterministic(district_votes, party_names)

        for party, frag in fragment_votes.items():
            assert frag >= 0, f"Negative fragment votes for {party}: {frag}"

    def test_list_allocation_plausible(self):
        """List allocation should produce plausible seat counts.

        Note: Our model allocates all 93 list seats to party lists,
        while in reality 1 goes to nationality (MNOÖ). So our numbers
        will have 1 extra seat distributed among parties compared to official.
        """
        district_votes = _load_district_votes()
        party_names = list(EXPECTED_SMD.keys())

        _, fragment_votes = simulate_smds_deterministic(district_votes, party_names)

        total_valid_list = sum(NATIONAL_LIST_2022.values())
        list_seats = allocate_list_seats_deterministic(
            NATIONAL_LIST_2022, fragment_votes, PARTY_THRESHOLDS_2022,
            total_valid_list, n_seats=93
        )

        # Total list seats should be 93
        assert sum(list_seats.values()) == 93

        # MKKP and other should get 0 (below 5% threshold)
        assert list_seats["mkkp"] == 0
        assert list_seats["other"] == 0

        # Mi Hazánk should get seats (above 5%)
        assert list_seats["mi_hazank"] > 0

        # Fidesz should get the most list seats
        assert list_seats["fidesz"] > list_seats["opposition"]

    def test_total_seats_close_to_official(self):
        """Total seats per party should be close to official results.

        Official (199 total, including 1 nationality):
          Fidesz: 135 (87+48), Opposition: 57 (19+38), Mi Hazánk: 6 (0+6), MNOÖ: 1
        Our model (199 total, no nationality):
          We allocate 93 list seats to parties instead of 92+1.
        """
        district_votes = _load_district_votes()
        party_names = list(EXPECTED_SMD.keys())

        smd_seats, fragment_votes = simulate_smds_deterministic(district_votes, party_names)

        total_valid_list = sum(NATIONAL_LIST_2022.values())
        list_seats = allocate_list_seats_deterministic(
            NATIONAL_LIST_2022, fragment_votes, PARTY_THRESHOLDS_2022,
            total_valid_list, n_seats=93
        )

        total = {p: smd_seats[p] + list_seats[p] for p in party_names}

        # Fidesz: official 135, ours should be 135-136 (±1 for the extra list seat)
        assert 134 <= total["fidesz"] <= 137, f"Fidesz total: {total['fidesz']}"

        # Opposition: official 57, ours ~57-58
        assert 55 <= total["opposition"] <= 59, f"Opposition total: {total['opposition']}"

        # Mi Hazánk: official 6, ours ~6-7
        assert 5 <= total["mi_hazank"] <= 8, f"Mi Hazánk total: {total['mi_hazank']}"

        # Grand total = 199
        grand_total = sum(total.values())
        assert grand_total == 106 + 93, f"Grand total: {grand_total}"
