"""Single-member district simulation and fragment vote calculation."""

from __future__ import annotations

import numpy as np


def simulate_smds(
    district_shares: np.ndarray,
    district_total_votes: np.ndarray,
    party_names: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate all SMDs for N simulations.

    Args:
        district_shares: Shape (N, D, K) — vote share per party per district.
        district_total_votes: Shape (D,) — total valid votes per district.
        party_names: List of K party names (for reference only).

    Returns:
        smd_seats: Shape (N, K) — SMD seats won per party.
        fragment_votes: Shape (N, K) — fragment votes per party.
    """
    N, D, K = district_shares.shape

    # Compute vote counts: (N, D, K)
    votes = district_shares * district_total_votes[np.newaxis, :, np.newaxis]

    # Winner in each district: argmax over parties axis
    winners = np.argmax(votes, axis=2)  # (N, D)

    # SMD seats: count wins per party
    smd_seats = np.zeros((N, K), dtype=np.int32)
    for k in range(K):
        smd_seats[:, k] = (winners == k).sum(axis=1)

    # Fragment vote calculation (vectorized)
    fragment_votes = _compute_fragment_votes(votes, winners, N, D, K)

    return smd_seats, fragment_votes


def _compute_fragment_votes(
    votes: np.ndarray,
    winners: np.ndarray,
    N: int,
    D: int,
    K: int,
) -> np.ndarray:
    """Compute fragment votes using vectorized operations.

    Fragment rules:
    - Losing candidates: ALL their votes become fragment votes.
    - Winning candidate: (winner_votes - second_place_votes - 1) become fragment votes.

    Args:
        votes: Shape (N, D, K) — vote counts.
        winners: Shape (N, D) — winning party index per district.
        N, D, K: Dimensions.

    Returns:
        Shape (N, K) — total fragment votes per party across all districts.
    """
    # Start by assuming all votes are fragment votes (loser assumption)
    all_fragment = votes.copy()  # (N, D, K)

    # Find winner votes and second-place votes per district
    # Sort votes descending along party axis
    sorted_votes = np.sort(votes, axis=2)[:, :, ::-1]  # (N, D, K) descending
    winner_votes = sorted_votes[:, :, 0]   # (N, D)
    second_votes = sorted_votes[:, :, 1]   # (N, D)

    # Winner fragment = winner_votes - second_votes - 1, clamped to >= 0
    winner_fragments = np.maximum(winner_votes - second_votes - 1, 0)  # (N, D)

    # Override winner's contribution with their fragment amount
    sim_idx = np.arange(N)[:, np.newaxis]   # (N, 1)
    dist_idx = np.arange(D)[np.newaxis, :]  # (1, D)
    all_fragment[sim_idx, dist_idx, winners] = winner_fragments

    # Sum across all districts to get per-party totals
    fragment_votes = all_fragment.sum(axis=1)  # (N, K)

    return fragment_votes


def simulate_smds_deterministic(
    district_votes: dict[int, dict[str, int]],
    party_names: list[str],
) -> tuple[dict[str, int], dict[str, int]]:
    """Deterministic SMD simulation for backtesting with exact vote counts.

    Args:
        district_votes: district_id → {party: votes}
        party_names: List of party names.

    Returns:
        smd_seats: party → SMD seats won.
        fragment_votes: party → total fragment votes.
    """
    smd_seats = {p: 0 for p in party_names}
    fragment_votes = {p: 0 for p in party_names}

    for _did, votes in sorted(district_votes.items()):
        # Sort candidates by votes descending
        sorted_candidates = sorted(votes.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_candidates) < 2:
            if sorted_candidates:
                winner_party = sorted_candidates[0][0]
                smd_seats[winner_party] += 1
            continue

        winner_party, winner_v = sorted_candidates[0]
        _second_party, second_v = sorted_candidates[1]

        # Winner gets a seat
        smd_seats[winner_party] += 1

        # Fragment votes
        # Winner: winner_votes - second_votes - 1
        winner_frag = max(winner_v - second_v - 1, 0)
        fragment_votes[winner_party] = fragment_votes.get(winner_party, 0) + winner_frag

        # Losers: all their votes
        for party, v in sorted_candidates[1:]:
            fragment_votes[party] = fragment_votes.get(party, 0) + v

    return smd_seats, fragment_votes
