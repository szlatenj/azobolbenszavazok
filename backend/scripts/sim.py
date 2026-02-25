#!/usr/bin/env python3
"""Election simulator CLI — easy management and simulation runner.

Usage:
    python scripts/sim.py run                  # Run with defaults (20k sims)
    python scripts/sim.py run --sims 5000      # Quick run
    python scripts/sim.py run --seed 123       # Reproducible run

    python scripts/sim.py polls                # Show current poll averages
    python scripts/sim.py polls --add          # Add a new poll interactively
    python scripts/sim.py polls --list         # List all polls

    python scripts/sim.py config               # Show current config
    python scripts/sim.py config --edit        # Open pollster_config.json location

    python scripts/sim.py backtest             # Run 2022 backtest validation
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "simulation" / "data"


def cmd_run(args):
    """Run the Monte Carlo simulation."""
    from app.simulation.config import SimulationConfig
    from app.simulation.monte_carlo import run_simulation
    from app.simulation.schemas import SimulationInput

    config = SimulationConfig(
        n_simulations=args.sims,
        random_seed=args.seed,
    )

    # Custom shares override
    input_data = None
    if args.fidesz and args.tisza:
        shares = {
            "fidesz": args.fidesz / 100,
            "tisza": args.tisza / 100,
            "mi_hazank": (args.mi_hazank or 6) / 100,
            "dk": (args.dk or 4) / 100,
            "mkkp": (args.mkkp or 3) / 100,
            "other": (args.other or 2) / 100,
        }
        # Normalize
        total = sum(shares.values())
        shares = {k: v / total for k, v in shares.items()}
        input_data = SimulationInput(
            custom_shares=shares,
            n_simulations=args.sims,
            random_seed=args.seed,
        )

    print(f"Running {args.sims:,} simulations...")
    result = run_simulation(input_data=input_data, config=config)

    print()
    print("=" * 70)
    print("  HUNGARIAN PARLIAMENTARY ELECTION 2026 FORECAST")
    print(f"  {result.n_simulations:,} simulations | {result.elapsed_seconds:.1f}s")
    print("=" * 70)
    print()
    print(f"{'Party':>12s} | {'Mean':>6s} | {'Median':>6s} | {'90% CI':>12s} | {'P(maj)':>7s} | {'P(2/3)':>7s}")
    print("-" * 70)
    for p, r in sorted(result.parties.items(), key=lambda x: -x[1].mean_seats):
        ci = f"[{r.percentile_5}-{r.percentile_95}]"
        print(f"{p:>12s} | {r.mean_seats:6.1f} | {r.median_seats:6d} | {ci:>12s} | {r.win_probability:6.1%} | {r.supermajority_probability:6.1%}")
    print("-" * 70)
    print()
    print(f"Most likely outcome: {result.most_likely_government}")
    print(f"No majority: {result.no_majority_probability:.1%}")
    print()
    print("Seat breakdown (mean):")
    print(f"{'Party':>12s} | {'SMD':>6s} | {'List':>6s} | {'Total':>6s}")
    print("-" * 42)
    for p, r in sorted(result.parties.items(), key=lambda x: -x[1].mean_seats):
        print(f"{p:>12s} | {r.smd_seats_mean:6.1f} | {r.list_seats_mean:6.1f} | {r.mean_seats:6.1f}")
    print()
    print("Input poll averages:")
    for p, s in sorted(result.national_shares_input.items(), key=lambda x: -x[1]):
        print(f"  {p}: {s:.1%}")


def cmd_polls(args):
    """Manage polling data."""
    polls_path = DATA_DIR / "polls.csv"

    if args.add:
        _add_poll_interactive(polls_path)
    elif args.list:
        _list_polls(polls_path)
    else:
        _show_poll_averages(polls_path)


def _show_poll_averages(polls_path: Path):
    """Show weighted poll averages."""
    from app.simulation.config import SimulationConfig
    from app.simulation.monte_carlo import run_simulation
    from app.simulation.poll_aggregator import aggregate_polls, load_polls_csv

    config = SimulationConfig()
    # Load pollster config
    pc_path = DATA_DIR / "pollster_config.json"
    if pc_path.exists():
        from app.simulation.config import PollsterConfig
        with open(pc_path, "r", encoding="utf-8") as f:
            pc_data = json.load(f)
        pollster_configs = {}
        for name, cfg in pc_data.get("pollsters", {}).items():
            pollster_configs[name] = PollsterConfig(
                quality_weight=cfg.get("quality_weight", 1.0),
                house_effects=cfg.get("house_effects", {}),
            )
        config = config.model_copy(update={"pollster_configs": pollster_configs})

    polls = load_polls_csv(polls_path)
    means, uncertainty = aggregate_polls(polls, date.today(), config)

    print("Weighted poll averages (with house effect corrections):")
    print("-" * 40)
    for p, s in sorted(means.items(), key=lambda x: -x[1]):
        unc = uncertainty.get(p, 0)
        print(f"  {p:>12s}: {s:5.1%}  (±{unc:.1%})")
    print(f"\n  Based on {len(polls)} polls")
    print(f"  Most recent: {max(p['date'] for p in polls)}")


def _list_polls(polls_path: Path):
    """List all polls in the CSV."""
    with open(polls_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    party_cols = [c for c in reader.fieldnames if c not in ("date", "pollster", "sample_size", "population")]

    print(f"{'Date':>12s} | {'Pollster':>25s} | {'N':>5s} | ", end="")
    print(" | ".join(f"{p:>8s}" for p in party_cols))
    print("-" * (50 + 11 * len(party_cols)))

    for row in rows:
        print(f"{row['date']:>12s} | {row['pollster']:>25s} | {row['sample_size']:>5s} | ", end="")
        print(" | ".join(f"{float(row.get(p, 0)):8.1%}" for p in party_cols))

    print(f"\nTotal: {len(rows)} polls")


def _add_poll_interactive(polls_path: Path):
    """Add a new poll interactively."""
    print("Add a new poll")
    print("-" * 40)

    poll_date = input(f"Date (YYYY-MM-DD) [{date.today().isoformat()}]: ").strip()
    if not poll_date:
        poll_date = date.today().isoformat()

    pollster = input("Pollster name: ").strip()
    if not pollster:
        print("Pollster name is required.")
        return

    sample_size = input("Sample size [1000]: ").strip()
    sample_size = sample_size or "1000"

    print("\nEnter vote shares as percentages (e.g., 42 for 42%):")
    parties = ["fidesz", "tisza", "mi_hazank", "dk", "mkkp", "other"]
    shares = {}
    for p in parties:
        val = input(f"  {p}: ").strip()
        shares[p] = round(float(val) / 100, 4) if val else 0.0

    total = sum(shares.values())
    if abs(total - 1.0) > 0.05:
        print(f"\nWarning: shares sum to {total:.1%}, not 100%. Normalizing...")
        shares = {k: round(v / total, 4) for k, v in shares.items()}

    # Append to CSV
    with open(polls_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            poll_date, pollster, sample_size, "certain_voters",
            shares["fidesz"], shares["tisza"], shares["mi_hazank"],
            shares["dk"], shares["mkkp"], shares["other"],
        ])

    print(f"\nAdded: {pollster} ({poll_date})")
    print("Shares:", {k: f"{v:.1%}" for k, v in shares.items()})


def cmd_config(args):
    """Show or edit configuration."""
    pc_path = DATA_DIR / "pollster_config.json"

    if args.edit:
        print(f"Pollster config file: {pc_path}")
        print(f"Polls CSV file:       {DATA_DIR / 'polls.csv'}")
        print(f"Party metadata:       {DATA_DIR / 'party_metadata.json'}")
        print(f"\nEdit these files directly to configure the simulation.")
        return

    with open(pc_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("Pollster Configuration:")
    print("-" * 60)
    print(f"{'Pollster':>25s} | {'Weight':>6s} | {'Lean':>18s} | House Effects")
    print("-" * 60)
    for name, cfg in config["pollsters"].items():
        effects = cfg.get("house_effects", {})
        effects_str = ", ".join(f"{k}:{v:+.0f}" for k, v in effects.items()) if effects else "none"
        # Handle Unicode safely on Windows
        safe_name = name.encode("ascii", "replace").decode("ascii")
        print(f"{safe_name:>25s} | {cfg['quality_weight']:6.2f} | {cfg['lean']:>18s} | {effects_str}")


def cmd_backtest(args):
    """Run 2022 backtest."""
    from app.simulation.district_sim import simulate_smds_deterministic
    from app.simulation.list_allocation import allocate_list_seats_deterministic

    districts_path = DATA_DIR / "districts_2022.csv"
    districts = {}
    with open(districts_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            did = int(row["district_id"])
            districts[did] = {
                "fidesz": int(row["fidesz_votes"]),
                "opposition": int(row["opposition_votes"]),
                "mi_hazank": int(row["mi_hazank_votes"]),
                "mkkp": int(row["mkkp_votes"]),
                "other": int(row["other_votes"]),
            }

    parties = ["fidesz", "opposition", "mi_hazank", "mkkp", "other"]
    smd_seats, fragments = simulate_smds_deterministic(districts, parties)

    national = {"fidesz": 3060706, "opposition": 1947331, "mi_hazank": 332487, "mkkp": 185052, "other": 98649}
    thresholds = {"fidesz": 0.10, "opposition": 0.15, "mi_hazank": 0.05, "mkkp": 0.05, "other": 0.05}
    total_valid = sum(national.values())

    list_seats = allocate_list_seats_deterministic(national, fragments, thresholds, total_valid, 93)

    print("2022 BACKTEST RESULTS")
    print("=" * 55)
    print(f"{'Party':>12s} | {'SMD':>5s} | {'List':>5s} | {'Total':>5s} | {'Official':>8s}")
    print("-" * 55)

    official = {"fidesz": (87, 48, 135), "opposition": (19, 38, 57), "mi_hazank": (0, 6, 6), "mkkp": (0, 0, 0), "other": (0, 0, 0)}
    for p in parties:
        s, l = smd_seats[p], list_seats[p]
        off = official.get(p, (0, 0, 0))
        print(f"{p:>12s} | {s:5d} | {l:5d} | {s + l:5d} | {off[2]:8d}")

    print("-" * 55)
    total = sum(smd_seats[p] + list_seats[p] for p in parties)
    print(f"{'TOTAL':>12s} | {sum(smd_seats.values()):5d} | {sum(list_seats.values()):5d} | {total:5d} |      199")
    print(f"\nNote: Our model allocates 93 list seats to parties (official: 92 + 1 nationality)")


def main():
    parser = argparse.ArgumentParser(
        description="Hungarian Election Monte Carlo Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/sim.py run                    Run with defaults (20k sims)
  python scripts/sim.py run --sims 5000        Quick run
  python scripts/sim.py run --fidesz 42 --tisza 38  Custom vote shares
  python scripts/sim.py polls                  Show weighted poll averages
  python scripts/sim.py polls --add            Add a new poll interactively
  python scripts/sim.py polls --list           List all polls in CSV
  python scripts/sim.py config                 Show pollster config
  python scripts/sim.py backtest               Validate against 2022 results
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # run
    run_p = sub.add_parser("run", help="Run Monte Carlo simulation")
    run_p.add_argument("--sims", type=int, default=20000, help="Number of simulations (default: 20000)")
    run_p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    run_p.add_argument("--fidesz", type=float, help="Override Fidesz %% (e.g., 42)")
    run_p.add_argument("--tisza", type=float, help="Override Tisza %% (e.g., 38)")
    run_p.add_argument("--mi-hazank", type=float, dest="mi_hazank", help="Override Mi Hazánk %%")
    run_p.add_argument("--dk", type=float, help="Override DK %%")
    run_p.add_argument("--mkkp", type=float, help="Override MKKP %%")
    run_p.add_argument("--other", type=float, help="Override Other %%")

    # polls
    polls_p = sub.add_parser("polls", help="Manage polling data")
    polls_p.add_argument("--add", action="store_true", help="Add a poll interactively")
    polls_p.add_argument("--list", action="store_true", help="List all polls")

    # config
    config_p = sub.add_parser("config", help="Show/edit configuration")
    config_p.add_argument("--edit", action="store_true", help="Show config file paths")

    # backtest
    sub.add_parser("backtest", help="Validate against 2022 actual results")

    args = parser.parse_args()
    if args.command == "run":
        cmd_run(args)
    elif args.command == "polls":
        cmd_polls(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "backtest":
        cmd_backtest(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
