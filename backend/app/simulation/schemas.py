"""Pydantic models for simulation API input/output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SimulationInput(BaseModel):
    """Input for custom simulation runs — all parameters controllable."""
    # Vote shares
    custom_shares: dict[str, float] | None = None
    n_simulations: int = Field(default=20_000, ge=100, le=100_000)
    random_seed: int | None = None
    coordination_scenario: str | None = None

    # Error structure (Nate Silver-style sigmas)
    sigma_polling_error: float | None = None
    sigma_regional: float | None = None
    sigma_district: float | None = None
    sigma_turnout: float | None = None

    # Poll aggregation
    poll_halflife_days: float | None = None
    floor_uncertainty: float | None = None

    # Voter behavior change (urban/rural differential)
    urban_swing_fidesz: float | None = None
    urban_swing_tisza: float | None = None
    urban_swing_mi_hazank: float | None = None
    urban_turnout_shift: float | None = None
    rural_turnout_shift: float | None = None
    budapest_extra_swing: float | None = None

    # Ticket splitting: {"from_party": {"to": "target_party", "pct": 0.05}}
    ticket_splits: dict[str, dict] | None = None

    # Correlations
    fidesz_opposition_correlation: float | None = None
    small_party_correlation: float | None = None

    # Pollster overrides: pollster_name -> quality_weight (0.0-1.0)
    pollster_weights: dict[str, float] | None = None
    # Pollster house effect overrides: pollster_name -> {party: adjustment_in_pct_points}
    pollster_house_effects: dict[str, dict[str, float]] | None = None

    # Party toggles: party_short -> enabled (true/false)
    active_parties: dict[str, bool] | None = None


class PartyResult(BaseModel):
    """Per-party simulation results."""
    mean_seats: float
    median_seats: int
    smd_seats_mean: float
    list_seats_mean: float
    percentile_5: int
    percentile_25: int
    percentile_50: int
    percentile_75: int
    percentile_95: int
    win_probability: float
    supermajority_probability: float
    seat_distribution: list[int]


class SimulationResult(BaseModel):
    """Full simulation output."""
    party_names: list[str]
    n_simulations: int
    elapsed_seconds: float
    parties: dict[str, PartyResult]
    most_likely_government: str
    no_majority_probability: float
    national_shares_input: dict[str, float]


class SimulationSummary(BaseModel):
    """Lightweight summary for quick display."""
    parties: dict[str, float]
    win_probabilities: dict[str, float]
    supermajority_probabilities: dict[str, float]
    no_majority_probability: float
    simulation_count: int
    elapsed_seconds: float


class PollsterInfo(BaseModel):
    """Pollster details for config endpoint."""
    name: str
    quality_weight: float
    lean: str
    house_effects: dict[str, float]


class PartyInfo(BaseModel):
    """Party details for config endpoint."""
    short: str
    name: str
    color: str
    threshold: float
    coalition_members: int


class SimulationDefaults(BaseModel):
    """Full config defaults returned by GET /simulation/config."""
    n_simulations: int
    sigma_polling_error: float
    sigma_regional: float
    sigma_district: float
    sigma_turnout: float
    poll_halflife_days: float
    floor_uncertainty: float
    fidesz_opposition_correlation: float
    small_party_correlation: float
    urban_swing_fidesz: float
    urban_swing_tisza: float
    urban_swing_mi_hazank: float
    urban_turnout_shift: float
    rural_turnout_shift: float
    budapest_extra_swing: float
    ticket_splits: dict[str, dict]
    majority_threshold: int
    supermajority_threshold: int
    single_party_threshold: float
    two_party_threshold: float
    three_plus_threshold: float
    pollsters: dict[str, PollsterInfo]
    parties: list[PartyInfo]


class PollRecord(BaseModel):
    """Single poll for the polls endpoint."""
    date: str
    pollster: str
    sample_size: int
    fidesz: float
    tisza: float
    mi_hazank: float
    dk: float
    mkkp: float
    other: float
