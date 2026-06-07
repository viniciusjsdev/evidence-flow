"""Handoff builder profile."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from evidence_flow.profiles.base import BaseProfile


class HandoffBuilderProfile(BaseProfile):
    """Build the collection handoff from ranked sources."""

    name = "handoff-builder"
    stage = "handoff"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        domain_context: dict[str, Any] = context["domain_context"]
        ranked_sources: list[dict[str, Any]] = context.get("ranked_sources", [])
        targets = [self._target_from_source(source) for source in ranked_sources]
        ready_count = sum(1 for item in targets if item["review_status"] == "ready")
        needs_review_count = sum(1 for item in targets if item["review_status"] == "needs_review")
        known_gaps = self._known_gaps(context)

        handoff = {
            "handoff_id": f"handoff-{uuid4().hex[:8]}",
            "from_stage": "discovery",
            "to_stage": "collection",
            "domain_id": domain_context["domain_id"],
            "targets": targets,
            "required_fields": [
                "target_id",
                "source_name",
                "initial_url",
                "access_type",
                "expected_format",
                "review_status",
            ],
            "coverage_contract": {
                "target_years": domain_context.get("temporal_scope", {}).get("target_years", 0),
                "preserve_shortfall": True,
            },
            "known_gaps": known_gaps,
            "ready_count": ready_count,
            "needs_review_count": needs_review_count,
        }
        return {
            "handoff": handoff,
            "handoff_meta": {
                "profile": self.name,
                "target_count": len(targets),
                "ready_count": ready_count,
                "needs_review_count": needs_review_count,
                "known_gap_count": len(known_gaps),
            },
        }

    @staticmethod
    def _target_from_source(source: dict[str, Any]) -> dict[str, Any]:
        coverage = source.get("coverage_target", {"years": 0, "required": False})
        return {
            "target_id": f"target-{source.get('rank', 0):03d}",
            "rank": source.get("rank", 0),
            "source_name": source.get("dataset_name") or source.get("title", ""),
            "initial_url": source.get("url", ""),
            "domain_layer": source.get("domain_layer", ""),
            "priority": source.get("track_priority", "medium"),
            "access_type": source.get("access_type", "unknown"),
            "expected_format": source.get("data_format", "unknown"),
            "expected_period": {
                "target_years": int(coverage.get("years", 0)),
                "actual_start": None,
                "actual_end": None,
            },
            "parameters": list(source.get("key_parameters", [])),
            "suggested_collection_method": HandoffBuilderProfile._collection_method(source),
            "review_status": source.get("review_status", "needs_review"),
            "known_gaps": HandoffBuilderProfile._source_gaps(source),
            "notes": list(source.get("filter_notes", [])),
        }

    @staticmethod
    def _collection_method(source: dict[str, Any]) -> str:
        access_type = source.get("access_type", "unknown")
        if access_type == "api_access":
            return "http_api"
        if access_type == "direct_download":
            return "http_download"
        if access_type == "pdf_extraction":
            return "pdf_extraction"
        if access_type == "web_portal":
            return "portal_review"
        if access_type == "geospatial_platform":
            return "geospatial_export"
        return "manual_review"

    @staticmethod
    def _source_gaps(source: dict[str, Any]) -> list[str]:
        gaps = []
        if source.get("temporal_coverage") is None:
            gaps.append("Actual temporal coverage is unknown until collection.")
        if source.get("access_type") == "unknown":
            gaps.append("Access type requires manual review.")
        if source.get("needs_review"):
            gaps.append("Source was flagged during technical filtering.")
        return gaps

    @staticmethod
    def _known_gaps(context: dict[str, Any]) -> list[str]:
        gaps = []
        filter_meta = context.get("filter_meta", {})
        if filter_meta.get("zero_result_sessions", 0):
            gaps.append("One or more tracks produced zero-result discovery sessions.")
        if not context.get("ranked_sources"):
            gaps.append("No ranked sources are ready for collection.")
        return gaps

