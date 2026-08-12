from __future__ import annotations

import argparse
from pathlib import Path

from next_best_action.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic next-best-action engine")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--customers", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    metadata = run_pipeline(args.project_root.resolve(), customers=args.customers, seed=args.seed)
    print(
        "Next-best-action run complete: "
        f"contacts={metadata['engine_contacts']}, "
        f"true_value={metadata['engine_true_incremental_net_value']:.2f}, "
        f"regret={metadata['engine_regret_vs_oracle']:.1%}"
    )


if __name__ == "__main__":
    main()
