"""Tests for the swing model."""

from __future__ import annotations

import numpy as np
import pytest

from app.simulation.config import SimulationConfig
from app.simulation.swing_model import (
    compute_district_shares,
    load_district_baselines,
    load_urbanization,
)


class TestSwingModel:
    """Test national-to-district swing translation."""

    def test_zero_swing_returns_baseline(self, data_dir, rng):
        """With zero national swing, district shares should be close to baselines."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")

        # Create national shares that exactly match baseline
        national_shares = np.array([[baseline_national[p] for p in party_names]])  # (1, K)

        config = SimulationConfig(
            sigma_regional=0.0,  # No regional noise
            sigma_district=0.0,  # No district noise
        )

        result = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config, rng
        )

        # Should be very close to baselines (only clipping/renorm may differ slightly)
        np.testing.assert_allclose(result[0], baselines, atol=0.01)

    def test_positive_swing_increases_share(self, data_dir, rng):
        """A +5 point Fidesz swing increases Fidesz in all districts."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")

        # Add 5% to Fidesz, subtract from others proportionally
        shifted = dict(baseline_national)
        shifted["fidesz"] += 0.05
        # Renormalize
        total = sum(shifted.values())
        shifted = {p: v / total for p, v in shifted.items()}

        national_shares = np.array([[shifted[p] for p in party_names]])
        config = SimulationConfig(sigma_regional=0.0, sigma_district=0.0)

        result = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config, rng
        )

        fidesz_idx = party_names.index("fidesz")
        # Fidesz share should increase in most districts
        increases = (result[0, :, fidesz_idx] > baselines[:, fidesz_idx]).sum()
        assert increases > 100  # Should increase in nearly all 106 districts

    def test_output_shape(self, data_dir, rng):
        """Output has correct shape (N, D, K)."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")

        N = 10
        national_shares = np.tile(
            [baseline_national[p] for p in party_names], (N, 1)
        )
        config = SimulationConfig()

        result = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config, rng
        )

        assert result.shape == (N, 106, len(party_names))

    def test_shares_sum_to_one(self, data_dir, rng):
        """District shares sum to 1.0 along party axis."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")

        national_shares = np.tile(
            [baseline_national[p] for p in party_names], (5, 1)
        )
        config = SimulationConfig()

        result = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config, rng
        )

        row_sums = result.sum(axis=2)
        np.testing.assert_allclose(row_sums, 1.0, atol=0.001)

    def test_load_baselines_106_districts(self, data_dir):
        """Loading baselines produces 106 districts."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")

        assert baselines.shape[0] == 106
        assert baselines.shape[1] == len(party_names)
        assert len(region_map) == 106
        assert len(total_votes) == 106
        assert all(p in baseline_national for p in party_names)

    def test_urban_swing_shifts_districts(self, data_dir, rng):
        """Urban swing decreases Fidesz in urban districts, increases in rural."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")
        urbanization, is_budapest = load_urbanization(data_dir)

        national_shares = np.array([[baseline_national[p] for p in party_names]])

        # Without urban swing
        config_base = SimulationConfig(sigma_regional=0.0, sigma_district=0.0)
        result_base = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config_base, rng,
            urbanization=urbanization, is_budapest=is_budapest,
        )

        # With Fidesz losing urban support
        config_urban = SimulationConfig(
            sigma_regional=0.0, sigma_district=0.0,
            urban_swing_fidesz=-0.05,
        )
        result_urban = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config_urban, rng,
            urbanization=urbanization, is_budapest=is_budapest,
        )

        f_idx = party_names.index("fidesz")
        mean_urb = urbanization.mean()
        urban_mask = urbanization > mean_urb
        rural_mask = urbanization < mean_urb

        # Fidesz should decrease in urban districts
        urban_diff = result_urban[0, urban_mask, f_idx] - result_base[0, urban_mask, f_idx]
        assert urban_diff.mean() < 0, "Fidesz should lose in urban districts"

        # Fidesz should increase in rural districts
        rural_diff = result_urban[0, rural_mask, f_idx] - result_base[0, rural_mask, f_idx]
        assert rural_diff.mean() > 0, "Fidesz should gain in rural districts"

    def test_budapest_extra_swing(self, data_dir, rng):
        """Budapest extra swing boosts Tisza and penalizes Fidesz in Budapest only."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")
        urbanization, is_budapest = load_urbanization(data_dir)

        national_shares = np.array([[baseline_national[p] for p in party_names]])

        # Without Budapest swing
        config_base = SimulationConfig(sigma_regional=0.0, sigma_district=0.0)
        result_base = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config_base, rng,
            urbanization=urbanization, is_budapest=is_budapest,
        )

        # With Budapest extra swing
        config_bp = SimulationConfig(
            sigma_regional=0.0, sigma_district=0.0,
            budapest_extra_swing=0.05,
        )
        result_bp = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config_bp, rng,
            urbanization=urbanization, is_budapest=is_budapest,
        )

        t_idx = party_names.index("tisza")
        f_idx = party_names.index("fidesz")

        # Tisza should increase in Budapest
        bp_tisza_diff = result_bp[0, is_budapest, t_idx] - result_base[0, is_budapest, t_idx]
        assert bp_tisza_diff.mean() > 0.03, "Tisza should gain significantly in Budapest"

        # Fidesz should decrease in Budapest
        bp_fidesz_diff = result_bp[0, is_budapest, f_idx] - result_base[0, is_budapest, f_idx]
        assert bp_fidesz_diff.mean() < -0.03, "Fidesz should lose significantly in Budapest"

        # Non-Budapest districts should be unaffected
        non_bp = ~is_budapest
        non_bp_diff = result_bp[0, non_bp, t_idx] - result_base[0, non_bp, t_idx]
        np.testing.assert_allclose(non_bp_diff, 0.0, atol=0.005)

    def test_zero_defaults_no_change(self, data_dir, rng):
        """Zero urban swing defaults produce same output as without urbanization."""
        party_names = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
        baselines, region_map, total_votes, baseline_national = \
            load_district_baselines(data_dir, party_names, "fragmented")
        urbanization, is_budapest = load_urbanization(data_dir)

        national_shares = np.array([[baseline_national[p] for p in party_names]])
        config = SimulationConfig(sigma_regional=0.0, sigma_district=0.0)

        # With urbanization data but all defaults at 0
        result_with = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config, rng,
            urbanization=urbanization, is_budapest=is_budapest,
        )

        # Without urbanization data
        result_without = compute_district_shares(
            national_shares, baseline_national, baselines,
            region_map, party_names, config, rng,
        )

        np.testing.assert_allclose(result_with, result_without, atol=1e-10)
