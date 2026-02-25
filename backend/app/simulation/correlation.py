"""Correlated national vote share draws using multivariate normal in logit space."""

from __future__ import annotations

import numpy as np

from .config import SimulationConfig


def _logit(p: float) -> float:
    """Logit transform: log(p / (1 - p)). Clamps p to (0.001, 0.999)."""
    p = max(0.001, min(0.999, p))
    return np.log(p / (1 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Inverse logit (sigmoid)."""
    return 1.0 / (1.0 + np.exp(-x))


def build_covariance_matrix(
    party_names: list[str],
    uncertainty: dict[str, float],
    config: SimulationConfig,
) -> np.ndarray:
    """Build covariance matrix in logit space.

    The main parties (fidesz and the largest opposition) are negatively correlated.
    Small parties are mildly positively correlated with each other.

    Args:
        party_names: List of party short names.
        uncertainty: Per-party uncertainty (std dev in probability space).
        config: Simulation config.

    Returns:
        Shape (K, K) covariance matrix in logit space.
    """
    K = len(party_names)

    # Convert probability-space uncertainty to logit-space uncertainty
    # Using delta method: σ_logit ≈ σ_p / (p * (1-p))
    # But we'll use a simpler approach: just scale by the polling error sigma
    logit_sigma = np.array([
        max(uncertainty.get(p, config.floor_uncertainty), config.floor_uncertainty)
        + config.sigma_polling_error
        for p in party_names
    ])

    # Build correlation matrix
    corr = np.eye(K)

    # Find indices for key parties
    fidesz_idx = None
    main_opposition_idx = None
    for i, p in enumerate(party_names):
        if p == "fidesz":
            fidesz_idx = i
        elif p in ("tisza", "opposition"):
            main_opposition_idx = i

    for i in range(K):
        for j in range(i + 1, K):
            if (i == fidesz_idx and j == main_opposition_idx) or \
               (j == fidesz_idx and i == main_opposition_idx):
                # Fidesz and main opposition: strong negative correlation
                corr[i, j] = config.fidesz_opposition_correlation
                corr[j, i] = config.fidesz_opposition_correlation
            elif party_names[i] not in ("fidesz",) and party_names[j] not in ("fidesz",):
                # Small parties mildly positively correlated
                corr[i, j] = config.small_party_correlation
                corr[j, i] = config.small_party_correlation
            else:
                # Fidesz vs small parties: mild negative
                corr[i, j] = -0.2
                corr[j, i] = -0.2

    # Convert correlation to covariance: Σ = diag(σ) @ R @ diag(σ)
    cov = np.outer(logit_sigma, logit_sigma) * corr

    return cov


def draw_national_shares(
    mean_shares: dict[str, float],
    n_simulations: int,
    config: SimulationConfig,
    rng: np.random.Generator,
    uncertainty: dict[str, float] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Draw correlated national vote shares for N simulations.

    Works in logit space to ensure shares stay in (0, 1), then normalizes.

    Args:
        mean_shares: Party → mean vote share (sums to ~1.0).
        n_simulations: Number of simulation draws.
        config: Simulation config.
        rng: Numpy random generator.
        uncertainty: Per-party uncertainty (optional, uses config defaults).

    Returns:
        (shares_array, party_names):
        - shares_array: Shape (N, K) — vote shares, each row sums to 1.0.
        - party_names: Ordered list of party names matching columns.
    """
    party_names = sorted(mean_shares.keys())
    K = len(party_names)

    # Default uncertainty if not provided
    if uncertainty is None:
        uncertainty = {p: config.floor_uncertainty for p in party_names}

    # Transform means to logit space
    logit_means = np.array([_logit(mean_shares[p]) for p in party_names])

    # Build covariance matrix
    cov = build_covariance_matrix(party_names, uncertainty, config)

    # Draw in logit space
    logit_draws = rng.multivariate_normal(logit_means, cov, size=n_simulations)  # (N, K)

    # Add systematic polling error (shifts Fidesz up ↔ opposition down)
    polling_error = rng.normal(0, config.sigma_polling_error, size=n_simulations)  # (N,)
    for i, p in enumerate(party_names):
        if p == "fidesz":
            logit_draws[:, i] += polling_error
        elif p in ("tisza", "opposition"):
            logit_draws[:, i] -= polling_error
        # Small parties: minimal systematic error effect

    # Transform back to probability space
    shares = _sigmoid(logit_draws)  # (N, K)

    # Normalize rows to sum to 1.0
    shares /= shares.sum(axis=1, keepdims=True)

    return shares, party_names
