"""Command line interface for Evidence Flow."""

from __future__ import annotations

import argparse
from pathlib import Path

from evidence_flow.harness.artifact_store import ArtifactStore
from evidence_flow.harness.orchestrator import HarnessOrchestrator
from evidence_flow.harness.validators import ContractValidationError, ContractValidator


REPO_ROOT = Path(__file__).resolve().parents[2]


def _default_repo_path(name: str) -> Path:
    cwd_candidate = Path.cwd() / name
    if cwd_candidate.exists():
        return cwd_candidate
    return REPO_ROOT / name


DEFAULT_CONTRACTS_DIR = _default_repo_path("contracts")
DEFAULT_RUNS_DIR = _default_repo_path("runs")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evidence-flow")
    parser.add_argument(
        "--contracts-dir",
        default=str(DEFAULT_CONTRACTS_DIR),
        help="Directory containing JSON Schema contracts.",
    )
    parser.add_argument(
        "--runs-dir",
        default=str(DEFAULT_RUNS_DIR),
        help="Directory where run artifacts are created.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    context_parser = subparsers.add_parser("validate-context", help="Validate a domain context file.")
    context_parser.add_argument("path", help="Path to a JSON or YAML domain context.")

    tracks_parser = subparsers.add_parser("validate-tracks", help="Validate a tracks file.")
    tracks_parser.add_argument("path", help="Path to a JSON or YAML tracks file.")

    handoff_parser = subparsers.add_parser("validate-handoff", help="Validate a handoff file.")
    handoff_parser.add_argument("path", help="Path to a JSON or YAML handoff.")

    manifest_parser = subparsers.add_parser("validate-manifest", help="Validate a run manifest file.")
    manifest_parser.add_argument("path", help="Path to a JSON or YAML manifest.")

    init_parser = subparsers.add_parser("init-run", help="Initialize a run from context and tracks.")
    init_parser.add_argument("--context", required=True, help="Path to domain context YAML/JSON.")
    init_parser.add_argument("--tracks", required=True, help="Path to tracks YAML/JSON.")
    init_parser.add_argument("--run-id", help="Optional explicit run id.")
    init_parser.add_argument("--pipeline-name", default="evidence-flow", help="Manifest pipeline name.")
    init_parser.add_argument("--parent-run-id", help="Optional parent run id.")

    flow_parser = subparsers.add_parser(
        "discovery-to-handoff",
        help="Run context + tracks through planning, discovery, validation, enrichment, ranking, and handoff.",
    )
    flow_parser.add_argument("--context", required=True, help="Path to domain context YAML/JSON.")
    flow_parser.add_argument("--tracks", required=True, help="Path to tracks YAML/JSON.")
    flow_parser.add_argument(
        "--discovery-fixture",
        help="Optional JSON/YAML fixture containing raw discovery sessions.",
    )
    flow_parser.add_argument("--run-id", help="Optional explicit run id.")
    flow_parser.add_argument("--pipeline-name", default="evidence-flow-discovery", help="Manifest pipeline name.")
    flow_parser.add_argument("--parent-run-id", help="Optional parent run id.")
    flow_parser.add_argument("--limit", type=int, default=40, help="Maximum ranked sources to hand off.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    validator = ContractValidator(contracts_dir=Path(args.contracts_dir))

    try:
        if args.command == "validate-context":
            validator.validate_file(Path(args.path), "domain_context")
            print(f"OK domain_context: {args.path}")
            return 0
        if args.command == "validate-tracks":
            validator.validate_file(Path(args.path), "tracks")
            print(f"OK tracks: {args.path}")
            return 0
        if args.command == "validate-handoff":
            validator.validate_file(Path(args.path), "handoff")
            print(f"OK handoff: {args.path}")
            return 0
        if args.command == "validate-manifest":
            validator.validate_file(Path(args.path), "manifest")
            print(f"OK manifest: {args.path}")
            return 0
        if args.command == "init-run":
            orchestrator = HarnessOrchestrator(
                store=ArtifactStore(root_dir=Path(args.runs_dir)),
                validator=validator,
            )
            result = orchestrator.init_run(
                context_path=Path(args.context),
                tracks_path=Path(args.tracks),
                run_id=args.run_id,
                pipeline_name=args.pipeline_name,
                parent_run_id=args.parent_run_id,
            )
            print(f"Run ID: {result.run_id}")
            print(f"Run dir: {result.run_dir}")
            print(f"Manifest: {result.manifest_path}")
            return 0
        if args.command == "discovery-to-handoff":
            orchestrator = HarnessOrchestrator(
                store=ArtifactStore(root_dir=Path(args.runs_dir)),
                validator=validator,
            )
            result = orchestrator.discovery_to_handoff(
                context_path=Path(args.context),
                tracks_path=Path(args.tracks),
                discovery_fixture_path=Path(args.discovery_fixture) if args.discovery_fixture else None,
                run_id=args.run_id,
                pipeline_name=args.pipeline_name,
                limit=args.limit,
                parent_run_id=args.parent_run_id,
            )
            print(f"Run ID: {result.run_id}")
            print(f"Run dir: {result.run_dir}")
            print(f"Manifest: {result.manifest_path}")
            print(f"Ranked sources: {result.ranked_sources_path}")
            print(f"Handoff: {result.handoff_path}")
            return 0
    except (ContractValidationError, FileNotFoundError, ValueError) as exc:
        print(f"Erro: {exc}")
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
