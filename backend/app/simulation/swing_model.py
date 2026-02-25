"""National-to-district swing model with regional and district-level noise."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from .config import SimulationConfig


# Region name → integer ID mapping
REGION_IDS = {
    "budapest": 0,
    "pest": 1,
    "northwestern": 2,
    "central_transdanubia": 3,
    "southern_transdanubia": 4,
    "northern_hungary": 5,
    "northern_great_plain": 6,
    "southern_great_plain": 7,
}
N_REGIONS = len(REGION_IDS)


def load_urbanization(data_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load urbanization scores and is_budapest flags for each district.

    Returns:
        (urbanization, is_budapest):
        - urbanization: Shape (D,) float array, 0 = rural, 1 = urban.
        - is_budapest: Shape (D,) bool array.
    """
    path = data_dir / "district_urbanization.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    D = len(data)
    urbanization = np.zeros(D, dtype=np.float64)
    is_budapest = np.zeros(D, dtype=bool)

    for district_id_str, info in data.items():
        idx = int(district_id_str) - 1  # 0-indexed
        urbanization[idx] = info["urbanization"]
        is_budapest[idx] = info["is_budapest"]

    return urbanization, is_budapest


def load_district_baselines(
    data_dir: Path,
    party_names: list[str],
    coordination_scenario: str = "fragmented",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, float]]:
    """Load 2022 district results as baseline data.

    For the 'fragmented' scenario, splits the 2022 united opposition vote
    among individual parties using the split ratios from party_metadata.json.

    Args:
        data_dir: Path to the data directory.
        party_names: List of party short names to produce columns for.
        coordination_scenario: 'coordinated' or 'fragmented'.

    Returns:
        (district_baselines, region_map, district_total_votes, baseline_national):
        - district_baselines: Shape (D, K) — vote share per party per district.
        - region_map: Shape (D,) — integer region ID per district.
        - district_total_votes: Shape (D,) — total votes per district.
        - baseline_national: dict[party → national vote share in 2022].
    """
    # Load district data
    districts_path = data_dir / "districts_2022.csv"
    with open(districts_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Load party metadata for opposition split ratios
    meta_path = data_dir / "party_metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    opposition_split = metadata.get("opposition_2022_to_2026_split", {})

    D = len(rows)
    K = len(party_names)

    # 2022 column mapping
    col_map_2022 = {
        "fidesz": "fidesz_votes",
        "opposition": "opposition_votes",
        "mi_hazank": "mi_hazank_votes",
        "mkkp": "mkkp_votes",
        "other": "other_votes",
    }

    district_baselines = np.zeros((D, K), dtype=np.float64)
    region_map = np.zeros(D, dtype=np.int32)
    district_total_votes = np.zeros(D, dtype=np.float64)

    for d, row in enumerate(rows):
        total = int(row["valid_votes"])
        district_total_votes[d] = total
        region_map[d] = REGION_IDS.get(row["region"], 0)

        if coordination_scenario == "coordinated":
            # Use 2022 structure directly: fidesz, opposition, mi_hazank, mkkp, other
            for k, party in enumerate(party_names):
                col = col_map_2022.get(party, "other_votes")
                votes = int(row.get(col, 0))
                district_baselines[d, k] = votes / total if total > 0 else 0.0
        else:
            # Fragmented: split opposition votes
            opp_votes = int(row["opposition_votes"])
            for k, party in enumerate(party_names):
                if party in col_map_2022 and party != "opposition":
                    col = col_map_2022[party]
                    votes = int(row.get(col, 0))
                    district_baselines[d, k] = votes / total if total > 0 else 0.0
                elif party in opposition_split:
                    # Split the opposition vote
                    split_ratio = opposition_split[party]
                    votes = opp_votes * split_ratio
                    district_baselines[d, k] = votes / total if total > 0 else 0.0
                elif party == "other":
                    # Other votes + remaining opposition split
                    other_votes = int(row.get("other_votes", 0))
                    opp_other = opp_votes * opposition_split.get("other", 0.0)
                    votes = other_votes + opp_other
                    district_baselines[d, k] = votes / total if total > 0 else 0.0

    # Normalize rows to sum to 1.0
    row_sums = district_baselines.sum(axis=1, keepdims=True)
    row_sums = np.maximum(row_sums, 1e-10)
    district_baselines /= row_sums

    # Compute national baseline shares (weighted by district total votes)
    total_national = district_total_votes.sum()
    baseline_national = {}
    for k, party in enumerate(party_names):
        weighted_sum = (district_baselines[:, k] * district_total_votes).sum()
        baseline_national[party] = float(weighted_sum / total_national) if total_national > 0 else 0.0

    return district_baselines, region_map, district_total_votes, baseline_national


def compute_district_shares(
    national_shares: np.ndarray,
    baseline_national: dict[str, float],
    district_baselines: np.ndarray,
    region_map: np.ndarray,
    party_names: list[str],
    config: SimulationConfig,
    rng: np.random.Generator,
    urbanization: np.ndarray | None = None,
    is_budapest: np.ndarray | None = None,
) -> np.ndarray:
    """Translate national vote shares into district-level vote shares.

    district_result[party] = baseline + national_swing + urban_differential
                           + regional_noise + district_noise

    Args:
        national_shares: Shape (N, K) — drawn national vote shares.
        baseline_national: Party → 2022 national vote share.
        district_baselines: Shape (D, K) — 2022 district vote shares.
        region_map: Shape (D,) — region ID per district.
        party_names: List of party names matching K columns.
        config: Simulation configuration.
        rng: Random generator.
        urbanization: Shape (D,) — urbanization score 0-1 per district.
        is_budapest: Shape (D,) — boolean mask for Budapest districts.

    Returns:
        Shape (N, D, K) — district-level vote shares.
    """
    N, K = national_shares.shape
    D = district_baselines.shape[0]

    # National swing: current draw - 2022 baseline
    baseline_arr = np.array([baseline_national[p] for p in party_names])  # (K,)
    swing = national_shares - baseline_arr[np.newaxis, :]  # (N, K)

    # Regional noise: shared within each region
    regional_noise = rng.normal(
        0, config.sigma_regional, size=(N, N_REGIONS, K)
    )  # (N, R, K)

    # District noise: idiosyncratic per district
    district_noise = rng.normal(
        0, config.sigma_district, size=(N, D, K)
    )  # (N, D, K)

    # Apply: district_share = baseline + swing + regional_noise[region] + district_noise
    district_shares = (
        district_baselines[np.newaxis, :, :]        # (1, D, K)
        + swing[:, np.newaxis, :]                    # (N, 1, K)
        + regional_noise[:, region_map, :]           # (N, D, K)
        + district_noise                             # (N, D, K)
    )

    # Urban/rural differential swing
    if urbanization is not None:
        mean_urb = urbanization.mean()
        centered_urb = urbanization - mean_urb  # (D,) — zero-sum nationally

        urban_swings = {
            "fidesz": config.urban_swing_fidesz,
            "tisza": config.urban_swing_tisza,
            "mi_hazank": config.urban_swing_mi_hazank,
        }
        for party, swing_val in urban_swings.items():
            if swing_val != 0.0 and party in party_names:
                k = party_names.index(party)
                district_shares[:, :, k] += swing_val * centered_urb[np.newaxis, :]

        # Budapest extra swing (opposition boost / Fidesz penalty)
        if config.budapest_extra_swing != 0.0 and is_budapest is not None and is_budapest.any():
            bp_mask = is_budapest  # (D,) bool
            if "tisza" in party_names:
                t_idx = party_names.index("tisza")
                district_shares[:, bp_mask, t_idx] += config.budapest_extra_swing
            if "fidesz" in party_names:
                f_idx = party_names.index("fidesz")
                district_shares[:, bp_mask, f_idx] -= config.budapest_extra_swing

    # Clip to [0.005, 0.95] and renormalize
    district_shares = np.clip(district_shares, 0.005, 0.95)
    district_shares /= district_shares.sum(axis=2, keepdims=True)

    return district_shares
