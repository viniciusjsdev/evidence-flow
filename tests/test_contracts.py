from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evidence_flow.harness.artifact_store import ArtifactStore
from evidence_flow.harness.io import read_structured
from evidence_flow.harness.orchestrator import HarnessOrchestrator
from evidence_flow.harness.validators import ContractValidator


REPO_ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = ContractValidator(contracts_dir=REPO_ROOT / "contracts")

    def test_example_context_validates(self) -> None:
        payload = self.validator.validate_file(
            REPO_ROOT / "contexts" / "examples" / "generic_research_context.yaml",
            "domain_context",
        )
        self.assertEqual(payload["domain_id"], "example-water-quality")

    def test_example_tracks_validate(self) -> None:
        payload = self.validator.validate_file(
            REPO_ROOT / "contexts" / "examples" / "generic_tracks.yaml",
            "tracks",
        )
        self.assertEqual(len(payload), 3)

    def test_example_handoff_validates(self) -> None:
        payload = self.validator.validate_file(
            REPO_ROOT / "contexts" / "examples" / "generic_handoff.yaml",
            "handoff",
        )
        self.assertEqual(payload["needs_review_count"], 1)

    def test_example_discovery_sessions_validate(self) -> None:
        payload = self.validator.validate_file(
            REPO_ROOT / "contexts" / "examples" / "generic_discovery_sessions.yaml",
            "discovery_sessions",
        )
        self.assertEqual(len(payload), 3)

    def test_init_run_creates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = HarnessOrchestrator(
                store=ArtifactStore(root_dir=Path(tmpdir)),
                validator=self.validator,
            )
            result = orchestrator.init_run(
                context_path=REPO_ROOT / "contexts" / "examples" / "generic_research_context.yaml",
                tracks_path=REPO_ROOT / "contexts" / "examples" / "generic_tracks.yaml",
                run_id="run-test-001",
            )

            manifest = read_structured(result.manifest_path)
            self.validator.validate_payload(manifest, "manifest")
            self.assertEqual(manifest["run_id"], "run-test-001")
            self.assertEqual(manifest["domain_id"], "example-water-quality")
            self.assertEqual(manifest["counts"]["track_count"], 3)
            self.assertEqual(len(manifest["artifacts"]), 2)

    def test_discovery_to_handoff_creates_contract_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = HarnessOrchestrator(
                store=ArtifactStore(root_dir=Path(tmpdir)),
                validator=self.validator,
            )
            result = orchestrator.discovery_to_handoff(
                context_path=REPO_ROOT / "contexts" / "examples" / "generic_research_context.yaml",
                tracks_path=REPO_ROOT / "contexts" / "examples" / "generic_tracks.yaml",
                discovery_fixture_path=REPO_ROOT
                / "contexts"
                / "examples"
                / "generic_discovery_sessions.yaml",
                run_id="run-flow-001",
            )

            manifest = read_structured(result.manifest_path)
            handoff = read_structured(result.handoff_path)
            ranked_sources = read_structured(result.ranked_sources_path)

            self.validator.validate_payload(manifest, "manifest")
            self.validator.validate_payload(handoff, "handoff")
            self.validator.validate_payload(ranked_sources, "source_inventory")
            self.assertEqual(manifest["stage"], "handoff")
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(manifest["counts"]["search_plan_count"], 3)
            self.assertEqual(manifest["counts"]["filtered_source_count"], 4)
            self.assertEqual(handoff["ready_count"], 3)
            self.assertEqual(handoff["needs_review_count"], 1)


if __name__ == "__main__":
    unittest.main()
