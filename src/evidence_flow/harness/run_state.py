"""Run manifest lifecycle helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evidence_flow.harness.artifact_store import ArtifactStore, utc_now
from evidence_flow.harness.io import read_structured, write_json
from evidence_flow.harness.validators import ContractValidator


@dataclass
class RunState:
    """Mutable wrapper around a run manifest."""

    store: ArtifactStore
    validator: ContractValidator
    manifest: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        store: ArtifactStore,
        validator: ContractValidator,
        run_id: str,
        pipeline_name: str,
        domain_id: str,
        inputs: dict[str, Any],
        parent_run_id: str | None = None,
    ) -> "RunState":
        now = utc_now()
        manifest = {
            "schema_version": "1.0",
            "run_id": run_id,
            "pipeline_name": pipeline_name,
            "domain_id": domain_id,
            "stage": "initialized",
            "status": "pending",
            "generated_at": now,
            "updated_at": now,
            "inputs": inputs,
            "outputs": {},
            "artifacts": [],
            "counts": {},
            "coverage": {},
            "blockers": [],
            "warnings": [],
            "parent_run_id": parent_run_id,
        }
        state = cls(store=store, validator=validator, manifest=manifest)
        state.validate()
        return state

    @classmethod
    def load(
        cls,
        *,
        store: ArtifactStore,
        validator: ContractValidator,
        manifest_path: Path,
    ) -> "RunState":
        payload = read_structured(manifest_path)
        state = cls(store=store, validator=validator, manifest=payload)
        state.validate()
        return state

    @property
    def run_id(self) -> str:
        return str(self.manifest["run_id"])

    def validate(self) -> None:
        self.validator.validate_payload(self.manifest, "manifest")

    def save(self) -> Path:
        self.manifest["updated_at"] = utc_now()
        self.validate()
        path = self.store.run_dir(self.run_id) / "manifest.json"
        write_json(path, self.manifest)
        return path

    def set_stage(self, stage: str, status: str = "running") -> None:
        self.manifest["stage"] = stage
        self.manifest["status"] = status
        self.manifest["updated_at"] = utc_now()
        self.validate()

    def add_artifact(
        self,
        *,
        path: Path,
        stage: str,
        artifact_type: str,
        description: str = "",
    ) -> None:
        self.manifest["artifacts"].append(
            {
                "path": str(path),
                "stage": stage,
                "artifact_type": artifact_type,
                "description": description,
                "generated_at": utc_now(),
            }
        )
        self.manifest["updated_at"] = utc_now()
        self.validate()

    def add_warning(self, message: str) -> None:
        self.manifest["warnings"].append(message)
        self.manifest["updated_at"] = utc_now()
        self.validate()

    def add_blocker(self, message: str) -> None:
        self.manifest["blockers"].append(message)
        self.manifest["status"] = "blocked"
        self.manifest["updated_at"] = utc_now()
        self.validate()

    def set_count(self, key: str, value: int) -> None:
        self.manifest["counts"][key] = value
        self.manifest["updated_at"] = utc_now()
        self.validate()

