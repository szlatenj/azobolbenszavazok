"""Monte Carlo orchestrator: runs N election simulations and collects results."""

from __future__ import annotations

import csv
import json
import time
from datetime import date
from pathlib import Path

import numpy as np

from .config import PollsterConfig, SimulationConfig
from .correlation import draw_national_shares
from .district_sim import simulate_smds
from .list_allocation import allocate_list_seats
from .poll_aggregator import aggregate_polls, load_polls_csv
from .schemas import PartyResult, SimulationInput, SimulationResult, SimulationSummary
from .swing_model import compute_district_shares, load_district_baselines, load_urbanization


def _load_national_list_totals(data_dir: Path) -> dict[str, int]:
    """Load 2022 national list vote totals."""
    path = data_dir / "national_list_2022.csv"
    totals = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            short = row["short"]
            votes = int(row["list_votes"])
            totals[short] = votes
    return totals


def _get_party_thresholds(
    party_names: list[str],
    config: SimulationConfig,
) -> np.ndarray:
    """Build threshold array from config party definitions."""
    thresholds = np.full(len(party_names), config.single_party_threshold)
    party_config_map = {pc.short: pc for pc in config.parties}

    for i, name in enumerate(party_names):
        pc = party_config_map.get(name)
        if pc:
            thresholds[i] = pc.threshold
        elif name == "fidesz":
            thresholds[i] = config.two_party_threshold  # Fidesz-KDNP = 2 parties
        elif name == "other":
            thresholds[i] = config.single_party_threshold

    return thresholds


def _load_pollster_configs(data_dir: Path) -> dict[str, PollsterConfig]:
    """Load pollster configs from JSON file."""
    pollster_config_path = data_dir / "pollster_config.json"
    if not pollster_config_path.exists():
        return {}
    with open(pollster_config_path, "r", encoding="utf-8") as f:
        pc_data = json.load(f)
    configs = {}
    for name, cfg in pc_data.get("pollsters", {}).items():
        configs[name] = PollsterConfig(
            quality_weight=cfg.get("quality_weight", 1.0),
            house_effects=cfg.get("house_effects", {}),
        )
    return configs


def _apply_input_overrides(
    config: SimulationConfig,
    input_data: SimulationInput,
) -> SimulationConfig:
    """Apply all overrides from SimulationInput to config."""
    updates: dict = {}

    # Simple field overrides
    field_map = {
        "n_simulations": "n_simulations",
        "random_seed": "random_seed",
        "coordination_scenario": "coordination_scenario",
        "sigma_polling_error": "sigma_polling_error",
        "sigma_regional": "sigma_regional",
        "sigma_district": "sigma_district",
        "sigma_turnout": "sigma_turnout",
        "poll_halflife_days": "poll_halflife_days",
        "floor_uncertainty": "floor_uncertainty",
        "fidesz_opposition_correlation": "fidesz_opposition_correlation",
        "small_party_correlation": "small_party_correlation",
        "urban_swing_fidesz": "urban_swing_fidesz",
        "urban_swing_tisza": "urban_swing_tisza",
        "urban_swing_mi_hazank": "urban_swing_mi_hazank",
        "urban_turnout_shift": "urban_turnout_shift",
        "rural_turnout_shift": "rural_turnout_shift",
        "budapest_extra_swing": "budapest_extra_swing",
    }
    for input_field, config_field in field_map.items():
        val = getattr(input_data, input_field, None)
        if val is not None:
            updates[config_field] = val

    if updates:
        config = config.model_copy(update=updates)

    # Pollster weight/house effect overrides
    if input_data.pollster_weights or input_data.pollster_house_effects:
        new_configs = dict(config.pollster_configs)
        if input_data.pollster_weights:
            for name, weight in input_data.pollster_weights.items():
                if name in new_configs:
                    pc = new_configs[name]
                    new_configs[name] = PollsterConfig(
                        quality_weight=weight,
                        house_effects=pc.house_effects,
                    )
                else:
                    new_configs[name] = PollsterConfig(quality_weight=weight)
        if input_data.pollster_house_effects:
            for name, effects in input_data.pollster_house_effects.items():
                if name in new_configs:
                    pc = new_configs[name]
                    new_configs[name] = PollsterConfig(
                        quality_weight=pc.quality_weight,
                        house_effects=effects,
                    )
                else:
                    new_configs[name] = PollsterConfig(house_effects=effects)
        config = config.model_copy(update={"pollster_configs": new_configs})

    return config


def _apply_party_toggles(
    mean_shares: dict[str, float],
    active_parties: dict[str, bool],
) -> dict[str, float]:
    """Remove disabled parties and redistribute their votes proportionally."""
    disabled_share = 0.0
    active_shares = {}
    for party, share in mean_shares.items():
        if active_parties.get(party, True):
            active_shares[party] = share
        else:
            disabled_share += share

    if not active_shares:
        return mean_shares

    # Redistribute disabled votes proportionally
    if disabled_share > 0:
        active_total = sum(active_shares.values())
        if active_total > 0:
            for party in active_shares:
                active_shares[party] += disabled_share * (active_shares[party] / active_total)

    return active_shares


def run_simulation(
    input_data: SimulationInput | None = None,
    config: SimulationConfig | None = None,
) -> SimulationResult:
    """Run the full Monte Carlo election simulation."""
    if config is None:
        config = SimulationConfig()

    # Load pollster configs from JSON if not already set
    if not config.pollster_configs:
        config = config.model_copy(
            update={"pollster_configs": _load_pollster_configs(config.data_dir)}
        )

    # Apply all overrides from input_data
    if input_data:
        config = _apply_input_overrides(config, input_data)

    rng = np.random.default_rng(config.random_seed)
    t0 = time.perf_counter()

    # Step 1: Get national vote shares
    if input_data and input_data.custom_shares:
        mean_shares = input_data.custom_shares
        uncertainty = {p: config.floor_uncertainty for p in mean_shares}
    else:
        polls = load_polls_csv(config.data_dir / "polls.csv")
        party_names_from_polls = sorted(polls[0]["shares"].keys()) if polls else []
        mean_shares, uncertainty = aggregate_polls(
            polls, date.today(), config, party_names_from_polls
        )

    # Step 1b: Apply party toggles (remove disabled parties, redistribute)
    if input_data and input_data.active_parties:
        mean_shares = _apply_party_toggles(mean_shares, input_data.active_parties)
        uncertainty = {p: uncertainty.get(p, config.floor_uncertainty) for p in mean_shares}

    party_names = sorted(mean_shares.keys())
    K = len(party_names)

    # Step 2: Load baseline district data
    district_baselines, region_map, district_total_votes, baseline_national = \
        load_district_baselines(config.data_dir, party_names, config.coordination_scenario)

    # Step 2b: Load urbanization data
    urbanization, is_budapest = load_urbanization(config.data_dir)

    # Step 3: Draw correlated national vote shares
    national_shares, party_names_ordered = draw_national_shares(
        mean_shares, config.n_simulations, config, rng, uncertainty
    )
    party_names = party_names_ordered
    K = len(party_names)

    # Step 4: Translate to district-level shares (with urban/rural differential)
    district_shares = compute_district_shares(
        national_shares, baseline_national, district_baselines,
        region_map, party_names, config, rng,
        urbanization=urbanization, is_budapest=is_budapest,
    )

    # Step 4b: Apply urban/rural turnout differential
    if config.urban_turnout_shift != 0.0 or config.rural_turnout_shift != 0.0:
        turnout_multiplier = (
            1.0
            + config.urban_turnout_shift * urbanization
            + config.rural_turnout_shift * (1.0 - urbanization)
        )
        district_total_votes = district_total_votes * turnout_multiplier

    # Step 5: Simulate SMDs
    smd_seats, fragment_votes = simulate_smds(
        district_shares, district_total_votes, party_names
    )

    # Step 6: Compute list votes
    list_totals_2022 = _load_national_list_totals(config.data_dir)
    total_national_list_votes = sum(list_totals_2022.values())
    raw_list_votes = national_shares * total_national_list_votes

    # Step 7: Get party thresholds
    party_thresholds = _get_party_thresholds(party_names, config)

    # Step 8: Allocate list seats
    list_seats = allocate_list_seats(
        raw_list_votes, fragment_votes, party_thresholds, n_seats=config.list_seats
    )

    # Step 9: Total seats
    total_seats = smd_seats + list_seats

    elapsed = time.perf_counter() - t0

    # Step 10: Build results
    parties_result = {}
    for i, p in enumerate(party_names):
        seats_col = total_seats[:, i]
        parties_result[p] = PartyResult(
            mean_seats=float(np.mean(seats_col)),
            median_seats=int(np.median(seats_col)),
            smd_seats_mean=float(np.mean(smd_seats[:, i])),
            list_seats_mean=float(np.mean(list_seats[:, i])),
            percentile_5=int(np.percentile(seats_col, 5)),
            percentile_25=int(np.percentile(seats_col, 25)),
            percentile_50=int(np.percentile(seats_col, 50)),
            percentile_75=int(np.percentile(seats_col, 75)),
            percentile_95=int(np.percentile(seats_col, 95)),
            win_probability=float(np.mean(seats_col >= config.majority_threshold)),
            supermajority_probability=float(np.mean(seats_col >= config.supermajority_threshold)),
            seat_distribution=seats_col.tolist(),
        )

    # Most likely government
    max_seats_per_sim = total_seats.max(axis=1)
    winner_idx = total_seats.argmax(axis=1)
    has_majority = max_seats_per_sim >= config.majority_threshold
    no_majority_prob = float(1.0 - np.mean(has_majority))

    majority_winners = winner_idx[has_majority]
    if len(majority_winners) > 0:
        counts = np.bincount(majority_winners, minlength=K)
        most_common = int(np.argmax(counts))
        most_likely_govt = f"{party_names[most_common]} majority"
    else:
        most_likely_govt = "No clear majority"

    return SimulationResult(
        party_names=party_names,
        n_simulations=config.n_simulations,
        elapsed_seconds=round(elapsed, 2),
        parties=parties_result,
        most_likely_government=most_likely_govt,
        no_majority_probability=round(no_majority_prob, 4),
        national_shares_input=mean_shares,
    )


def get_summary(result: SimulationResult) -> SimulationSummary:
    """Extract a lightweight summary from full simulation results."""
    return SimulationSummary(
        parties={p: r.mean_seats for p, r in result.parties.items()},
        win_probabilities={p: r.win_probability for p, r in result.parties.items()},
        supermajority_probabilities={
            p: r.supermajority_probability for p, r in result.parties.items()
        },
        no_majority_probability=result.no_majority_probability,
        simulation_count=result.n_simulations,
        elapsed_seconds=result.elapsed_seconds,
    )
