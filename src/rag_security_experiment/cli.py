from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_settings
from .experiment import GROUPS, run_experiment
from .metrics import summarize_results, write_extended_summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG indirect prompt injection experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run G0-G4 experiment pipeline")
    run_parser.add_argument("--all", action="store_true", help="Run all experiment groups")
    run_parser.add_argument("--groups", default="", help="Comma-separated groups, e.g. G1,G3,G4")
    run_parser.add_argument("--output", default="", help="Output CSV path")
    run_parser.add_argument("--dataset", default="", help="Dataset version: legacy, v1, v2, or another data/<version> directory")
    run_parser.add_argument("--offline-embeddings", action="store_true", help="Use local hashing embeddings for smoke tests")

    summarize_parser = subparsers.add_parser("summarize", help="Summarize a result CSV")
    summarize_parser.add_argument("--input", default="", help="Input result CSV path")
    summarize_parser.add_argument("--output", default="", help="Output summary CSV path")
    summarize_parser.add_argument("--extended", action="store_true", help="Write group, attack-type, filter, and manual-review summaries")
    summarize_parser.add_argument("--prefix", default="", help="Prefix for --extended summary files")

    args = parser.parse_args()
    settings = load_settings()

    if args.command == "run":
        groups = list(GROUPS) if args.all or not args.groups else [group.strip() for group in args.groups.split(",") if group.strip()]
        invalid = [group for group in groups if group not in GROUPS]
        if invalid:
            raise SystemExit(f"Unknown groups: {', '.join(invalid)}")
        output = Path(args.output) if args.output else None
        dataset = args.dataset or None
        result_path = run_experiment(settings, groups=groups, output=output, offline_embeddings=args.offline_embeddings, dataset_version=dataset)
        print(f"Experiment results written to: {result_path}")
        return

    if args.command == "summarize":
        input_path = Path(args.input) if args.input else settings.results_dir / "experiment_results.csv"
        output_path = Path(args.output) if args.output else settings.summary_dir / "summary.csv"
        summary = summarize_results(input_path, output_path)
        print(summary.to_string(index=False))
        print(f"Summary written to: {output_path}")
        if args.extended:
            paths = write_extended_summaries(input_path, settings.summary_dir, prefix=args.prefix or input_path.stem)
            for name, path in paths.items():
                print(f"Extended summary ({name}) written to: {path}")
        return


if __name__ == "__main__":
    main()
