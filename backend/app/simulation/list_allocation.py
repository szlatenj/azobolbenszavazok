"""d'Hondt list seat allocation with Hungarian threshold rules."""

from __future__ import annotations

import numpy as np


def dhondt(votes: dict[str, int], n_seats: int) -> dict[str, int]:
    """Allocate seats using the d'Hondt method.

    Args:
        votes: Party name → total votes (must be > 0 for eligible parties).
        n_seats: Number of seats to allocate.

    Returns:
        Party name → seats won.
    """
    if not votes or n_seats <= 0:
        return {p: 0 for p in votes}

    parties = list(votes.keys())
    v = np.array([votes[p] for p in parties], dtype=np.float64)
    seats = np.zeros(len(parties), dtype=np.int32)

    for _ in range(n_seats):
        quotients = v / (seats + 1)
        winner = int(np.argmax(quotients))
        seats[winner] += 1

    return {p: int(seats[i]) for i, p in enumerate(parties)}


def dhondt_vectorized(votes_array: np.ndarray, n_seats: int) -> np.ndarray:
    """Vectorized d'Hondt for a single simulation.

    Args:
        votes_array: Shape (K,) — votes per party (eligible only, zeros excluded).
        n_seats: Number of seats to allocate.

    Returns:
        Shape (K,) integer array of seats.
    """
    K = len(votes_array)
    seats = np.zeros(K, dtype=np.int32)

    for _ in range(n_seats):
        quotients = votes_array / (seats + 1).astype(np.float64)
        winner = int(np.argmax(quotients))
        seats[winner] += 1

    return seats


def apply_threshold(
    raw_list_votes: np.ndarray,
    party_thresholds: np.ndarray,
) -> np.ndarray:
    """Determine which parties pass the threshold.

    Threshold is applied to raw list votes (before adding fragment votes).

    Args:
        raw_list_votes: Shape (N, K) — raw party list votes per simulation.
        party_thresholds: Shape (K,) — threshold fraction per party (0.05, 0.10, 0.15).

    Returns:
        Shape (N, K) boolean mask — True if party passes threshold.
    """
    total_valid = raw_list_votes.sum(axis=1, keepdims=True)  # (N, 1)
    # Avoid division by zero
    total_valid = np.maximum(total_valid, 1.0)
    party_pct = raw_list_votes / total_valid  # (N, K)
    return party_pct >= party_thresholds[np.newaxis, :]  # (N, K)


def allocate_list_seats(
    raw_list_votes: np.ndarray,
    fragment_votes: np.ndarray,
    party_thresholds: np.ndarray,
    n_seats: int = 93,
) -> np.ndarray:
    """Allocate national list seats for all simulations.

    Args:
        raw_list_votes: Shape (N, K) — raw party list votes.
        fragment_votes: Shape (N, K) — fragment votes from SMD results.
        party_thresholds: Shape (K,) — threshold fraction per party.
        n_seats: Number of list seats to allocate (93).

    Returns:
        Shape (N, K) integer array — list seats per party per simulation.
    """
    N, K = raw_list_votes.shape
    mask = apply_threshold(raw_list_votes, party_thresholds)  # (N, K)

    # Effective votes = raw list votes + fragment votes, but only for eligible parties
    effective_votes = (raw_list_votes + fragment_votes) * mask  # (N, K)

    list_seats = np.zeros((N, K), dtype=np.int32)
    for sim in range(N):
        ev = effective_votes[sim]
        if ev.sum() > 0:
            list_seats[sim] = dhondt_vectorized(ev, n_seats)

    return list_seats


def allocate_list_seats_deterministic(
    raw_list_votes: dict[str, int],
    fragment_votes: dict[str, int],
    party_thresholds: dict[str, float],
    total_valid_list_votes: int,
    n_seats: int = 93,
) -> dict[str, int]:
    """Deterministic list allocation for a single election (e.g., backtesting).

    Args:
        raw_list_votes: Party → raw list vote count.
        fragment_votes: Party → fragment vote count.
        party_thresholds: Party → threshold fraction.
        total_valid_list_votes: Total valid list votes for threshold calc.
        n_seats: Number of list seats.

    Returns:
        Party → list seats.
    """
    # Apply threshold
    eligible = {}
    for party, votes in raw_list_votes.items():
        threshold = party_thresholds.get(party, 0.05)
        if total_valid_list_votes > 0 and votes / total_valid_list_votes >= threshold:
            eligible[party] = votes + fragment_votes.get(party, 0)

    result = dhondt(eligible, n_seats)

    # Add zero seats for non-eligible parties
    for party in raw_list_votes:
        if party not in result:
            result[party] = 0

    return result
