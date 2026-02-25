"""Simulation configuration with all tunable parameters."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class PollsterConfig(BaseModel):
    """Per-pollster quality weight and house effect adjustments."""
    quality_weight: float = 1.0
    house_effects: dict[str, float] = Field(default_factory=dict)


class PartyConfig(BaseModel):
    """Party definition."""
    name: str
    short: str
    color: str = "#888888"
    threshold: float = 0.05
    coalition_members: int = 1


class SimulationConfig(BaseModel):
    """All tunable parameters for the Monte Carlo simulation."""

    # Simulation control
    n_simulations: int = Field(default=20_000, ge=100, le=100_000)
    random_seed: int | None = Field(default=42)

    # Electoral system constants
    total_seats: int = 199
    smd_seats: int = 106
    list_seats: int = 93
    majority_threshold: int = 100
    supermajority_threshold: int = 133

    # Threshold rules
    single_party_threshold: float = 0.05
    two_party_threshold: float = 0.10
    three_plus_threshold: float = 0.15

    # Poll aggregation
    poll_halflife_days: float = 14.0
    min_sample_size: int = 500
    floor_uncertainty: float = 0.02
    pollster_configs: dict[str, PollsterConfig] = Field(default_factory=dict)

    # Correlation / national draw
    sigma_polling_error: float = 0.03
    fidesz_opposition_correlation: float = -0.7
    small_party_correlation: float = 0.3

    # Swing model
    sigma_regional: float = 0.025
    sigma_district: float = 0.020

    # Turnout variation
    sigma_turnout: float = 0.02

    # Voter behavior change (urban/rural differential)
    urban_swing_fidesz: float = 0.0
    urban_swing_tisza: float = 0.0
    urban_swing_mi_hazank: float = 0.0
    urban_turnout_shift: float = 0.0
    rural_turnout_shift: float = 0.0
    budapest_extra_swing: float = 0.0

    # Ticket splitting (list vs SMD divergence)
    # Format: {"from_party": {"to": "target_party", "pct": 0.05}}
    # e.g. 5% of mi_hazank SMD voters vote for "other" on the list
    ticket_splits: dict[str, dict] = Field(default_factory=dict)

    # Coordination scenario
    coordination_scenario: str = "fragmented"

    # Party definitions
    parties: list[PartyConfig] = Field(default_factory=list)

    # Data directory
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent / "data"
    )

    model_config = {"arbitrary_types_allowed": True}
