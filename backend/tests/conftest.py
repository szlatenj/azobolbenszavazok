"""Shared test fixtures for the election simulator."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure backend/app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.simulation.config import SimulationConfig


@pytest.fixture
def config() -> SimulationConfig:
    """Default simulation config with fixed seed."""
    return SimulationConfig(
        n_simulations=100,
        random_seed=42,
    )


@pytest.fixture
def rng() -> np.random.Generator:
    """Seeded random generator for reproducible tests."""
    return np.random.default_rng(42)


@pytest.fixture
def data_dir() -> Path:
    """Path to simulation data directory."""
    return Path(__file__).resolve().parent.parent / "app" / "simulation" / "data"
