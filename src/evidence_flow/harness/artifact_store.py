"""Persistent artifact storage for Evidence Flow runs."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_flow.harness.io import write_json, write_markdown, write_yaml


RUN_SUBDIRS = (
    "inputs",
    "discovery",
    "validation",
    "enrichment",
    "handoff",
    "collection",
    "staging",
    "analytic",
    "eda",
    "reports",
    "learning",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ArtifactStore:
    """Create and write artifacts inside a run directory."""

    root_dir: Path

    def run_dir(self, run_id: str) -> Path:
        return self.root_dir / run_id

    def init_run(self, run_id: str) -> Path:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=False)
        for subdir in RUN_SUBDIRS:
            (run_dir / subdir).mkdir(parents=True, exist_ok=True)
        return run_dir

    def copy_input(self, run_id: str, source_path: Path, name: str | None = None) -> Path:
        destination = self.run_dir(run_id) / "inputs" / (name or source_path.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        return destination

    def write_json(self, run_id: str, relative_path: str, payload: Any) -> Path:
        path = self.run_dir(run_id) / relative_path
        write_json(path, payload)
        return path

    def write_yaml(self, run_id: str, relative_path: str, payload: Any) -> Path:
        path = self.run_dir(run_id) / relative_path
        write_yaml(path, payload)
        return path

    def write_markdown(self, run_id: str, relative_path: str, content: str) -> Path:
        path = self.run_dir(run_id) / relative_path
        write_markdown(path, content)
        return path

