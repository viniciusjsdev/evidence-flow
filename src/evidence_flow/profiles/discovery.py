"""Discovery profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evidence_flow.harness.artifact_store import utc_now
from evidence_flow.harness.io import read_structured
from evidence_flow.profiles.base import BaseProfile


class ZeroResultDiscoveryProfile(BaseProfile):
    """Produce auditable zero-result discovery sessions.

    This profile is useful before a real search adapter is configured. It does
    not fabricate evidence; it records that discovery was intentionally not
    connected to an external source.
    """

    name = "zero-result-discovery"
    stage = "discovery"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        sessions = []
        for query in context["search_plan"]:
            sessions.append(
                {
                    "query_id": query["query_id"],
                    "query_text": query["query_text"],
                    "target_intent": query["target_intent"],
                    "research_track": query["research_track"],
                    "chat_label": query["chat_label"],
                    "collection_status": "zero_result",
                    "collection_method": self.name,
                    "request_endpoint": "",
                    "answer_text": "",
                    "visible_source_count": 0,
                    "links": [],
                    "blockers": ["No discovery adapter configured."],
                    "notes": ["Zero-result profile preserves the run contract without fabricating sources."],
                    "collected_at": utc_now(),
                }
            )
        return {
            "discovery_sessions": sessions,
            "discovery_meta": {
                "profile": self.name,
                "session_count": len(sessions),
                "link_count": 0,
            },
        }


class FixtureDiscoveryProfile(BaseProfile):
    """Load raw discovery sessions from a JSON or YAML fixture."""

    name = "fixture-discovery"
    stage = "discovery"

    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        payload = read_structured(self.fixture_path)
        if not isinstance(payload, list):
            raise ValueError("Discovery fixture must be a list of sessions.")
        return {
            "discovery_sessions": payload,
            "discovery_meta": {
                "profile": self.name,
                "fixture_path": str(self.fixture_path),
                "session_count": len(payload),
                "link_count": sum(len(item.get("links", [])) for item in payload),
            },
        }

