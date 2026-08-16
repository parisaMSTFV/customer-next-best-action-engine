from __future__ import annotations

import argparse
from pathlib import Path

from next_best_action.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the next-best-action engine")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--customers", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing a versioned upstream manifest and score artifacts",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output root for generated data and reports in either run mode",
    )
    args = parser.parse_args()
    if args.input_dir is not None and (args.customers is not None or args.seed is not None):
        parser.error("--customers and --seed are only valid for synthetic runs")
    metadata = run_pipeline(
        args.project_root.resolve(),
        customers=args.customers,
        seed=args.seed,
        input_dir=args.input_dir.resolve() if args.input_dir else None,
        output_dir=args.output_dir.resolve() if args.output_dir else None,
    )
    if metadata.get("input_mode") == "external":
        print(
            "External next-best-action run complete: "
            f"contacts={metadata['engine_contacts']}, "
            "predicted_value="
            f"{metadata['engine_predicted_incremental_net_value']:.2f}, "
            f"constraints_pass={metadata['all_constraints_pass']}"
        )
    else:
        print(
            "Synthetic next-best-action run complete: "
            f"contacts={metadata['engine_contacts']}, "
            f"true_value={metadata['engine_true_incremental_net_value']:.2f}, "
            f"regret={metadata['engine_regret_vs_oracle']:.1%}"
        )


if __name__ == "__main__":
    main()
