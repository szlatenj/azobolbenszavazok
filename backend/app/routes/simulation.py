"""FastAPI endpoints for the election Monte Carlo simulator."""

from __future__ import annotations

import csv
import json
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.simulation.config import SimulationConfig
from app.simulation.monte_carlo import get_summary, run_simulation
from app.simulation.schemas import (
    PartyInfo,
    PollRecord,
    PollsterInfo,
    SimulationDefaults,
    SimulationInput,
    SimulationResult,
    SimulationSummary,
)

router = APIRouter(tags=["simulation"])

_cached_result: SimulationResult | None = None
_simulation_lock = threading.Lock()

DATA_DIR = Path(__file__).resolve().parent.parent / "simulation" / "data"


@router.get("/simulation/config", response_model=SimulationDefaults)
async def get_simulation_config():
    """Return all default configuration values, pollster info, and party list."""
    config = SimulationConfig()

    # Load pollster config
    pollsters: dict[str, PollsterInfo] = {}
    pc_path = DATA_DIR / "pollster_config.json"
    if pc_path.exists():
        with open(pc_path, "r", encoding="utf-8") as f:
            pc_data = json.load(f)
        for name, cfg in pc_data.get("pollsters", {}).items():
            pollsters[name] = PollsterInfo(
                name=name,
                quality_weight=cfg.get("quality_weight", 1.0),
                lean=cfg.get("lean", "unknown"),
                house_effects=cfg.get("house_effects", {}),
            )

    # Load party metadata
    parties: list[PartyInfo] = []
    meta_path = DATA_DIR / "party_metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        for short, info in meta.get("parties_2026", {}).items():
            parties.append(PartyInfo(
                short=short,
                name=info["name"],
                color=info["color"],
                threshold=info["threshold"],
                coalition_members=info["coalition_members"],
            ))

    return SimulationDefaults(
        n_simulations=config.n_simulations,
        sigma_polling_error=config.sigma_polling_error,
        sigma_regional=config.sigma_regional,
        sigma_district=config.sigma_district,
        sigma_turnout=config.sigma_turnout,
        poll_halflife_days=config.poll_halflife_days,
        floor_uncertainty=config.floor_uncertainty,
        fidesz_opposition_correlation=config.fidesz_opposition_correlation,
        small_party_correlation=config.small_party_correlation,
        urban_swing_fidesz=config.urban_swing_fidesz,
        urban_swing_tisza=config.urban_swing_tisza,
        urban_swing_mi_hazank=config.urban_swing_mi_hazank,
        urban_turnout_shift=config.urban_turnout_shift,
        rural_turnout_shift=config.rural_turnout_shift,
        budapest_extra_swing=config.budapest_extra_swing,
        majority_threshold=config.majority_threshold,
        supermajority_threshold=config.supermajority_threshold,
        single_party_threshold=config.single_party_threshold,
        two_party_threshold=config.two_party_threshold,
        three_plus_threshold=config.three_plus_threshold,
        pollsters=pollsters,
        parties=parties,
    )


@router.get("/simulation/polls", response_model=list[PollRecord])
async def get_polls():
    """Return all polling data."""
    polls_path = DATA_DIR / "polls.csv"
    records = []
    with open(polls_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(PollRecord(
                date=row["date"],
                pollster=row["pollster"],
                sample_size=int(row["sample_size"]),
                fidesz=float(row.get("fidesz", 0)),
                tisza=float(row.get("tisza", 0)),
                mi_hazank=float(row.get("mi_hazank", 0)),
                dk=float(row.get("dk", 0)),
                mkkp=float(row.get("mkkp", 0)),
                other=float(row.get("other", 0)),
            ))
    return records


@router.get("/simulation/summary", response_model=SimulationSummary)
async def get_simulation_summary():
    """Get a lightweight summary of the latest simulation."""
    global _cached_result
    if _cached_result is None:
        if not _simulation_lock.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="A simulation is already running")
        try:
            _cached_result = await run_in_threadpool(run_simulation)
        finally:
            _simulation_lock.release()
    return get_summary(_cached_result)


@router.get("/simulation/default", response_model=SimulationResult)
async def run_default_simulation():
    """Run a simulation with default settings and latest poll data."""
    global _cached_result
    if not _simulation_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="A simulation is already running")
    try:
        _cached_result = await run_in_threadpool(run_simulation)
    finally:
        _simulation_lock.release()
    return _cached_result


@router.post("/simulation/run", response_model=SimulationResult)
async def run_custom_simulation(input_data: SimulationInput):
    """Run a simulation with custom parameters."""
    if not _simulation_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="A simulation is already running")
    try:
        result = await run_in_threadpool(run_simulation, input_data=input_data)
    finally:
        _simulation_lock.release()
    return result
