"""Minimal orchestration helpers for the scaffolded harness."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from evidence_flow.harness.artifact_store import ArtifactStore
from evidence_flow.harness.run_state import RunState
from evidence_flow.harness.validators import ContractValidator
from evidence_flow.profiles import (
    FilterValidateProfile,
    FixtureDiscoveryProfile,
    HandoffBuilderProfile,
    RankAccessProfile,
    SemanticEnrichmentProfile,
    TrackPlannerProfile,
    ZeroResultDiscoveryProfile,
)


@dataclass(frozen=True)
class InitRunResult:
    run_id: str
    run_dir: Path
    manifest_path: Path


@dataclass(frozen=True)
class DiscoveryHandoffResult:
    run_id: str
    run_dir: Path
    manifest_path: Path
    handoff_path: Path
    ranked_sources_path: Path


@dataclass(frozen=True)
class HarnessOrchestrator:
    """Initialize auditable runs from validated context and tracks."""

    store: ArtifactStore
    validator: ContractValidator

    def init_run(
        self,
        *,
        context_path: Path,
        tracks_path: Path,
        run_id: str | None = None,
        pipeline_name: str = "evidence-flow",
        parent_run_id: str | None = None,
    ) -> InitRunResult:
        context = self.validator.validate_file(context_path, "domain_context")
        tracks = self.validator.validate_file(tracks_path, "tracks")

        resolved_run_id = run_id or f"run-{uuid4().hex[:8]}"
        run_dir = self.store.init_run(resolved_run_id)
        copied_context = self.store.copy_input(resolved_run_id, context_path, "domain_context.yaml")
        copied_tracks = self.store.copy_input(resolved_run_id, tracks_path, "tracks.yaml")

        state = RunState.create(
            store=self.store,
            validator=self.validator,
            run_id=resolved_run_id,
            pipeline_name=pipeline_name,
            domain_id=context["domain_id"],
            inputs={
                "domain_context": str(copied_context),
                "tracks": str(copied_tracks),
            },
            parent_run_id=parent_run_id,
        )
        state.set_count("track_count", len(tracks))
        state.add_artifact(
            path=copied_context,
            stage="initialized",
            artifact_type="domain_context",
            description="Validated domain context used to initialize the run.",
        )
        state.add_artifact(
            path=copied_tracks,
            stage="initialized",
            artifact_type="tracks",
            description="Validated research tracks used to initialize the run.",
        )
        manifest_path = state.save()

        return InitRunResult(
            run_id=resolved_run_id,
            run_dir=run_dir,
            manifest_path=manifest_path,
        )

    def discovery_to_handoff(
        self,
        *,
        context_path: Path,
        tracks_path: Path,
        discovery_fixture_path: Path | None = None,
        run_id: str | None = None,
        pipeline_name: str = "evidence-flow-discovery",
        limit: int = 40,
        parent_run_id: str | None = None,
    ) -> DiscoveryHandoffResult:
        init_result = self.init_run(
            context_path=context_path,
            tracks_path=tracks_path,
            run_id=run_id,
            pipeline_name=pipeline_name,
            parent_run_id=parent_run_id,
        )
        state = RunState.load(
            store=self.store,
            validator=self.validator,
            manifest_path=init_result.manifest_path,
        )
        domain_context = self.validator.validate_file(context_path, "domain_context")
        tracks = self.validator.validate_file(tracks_path, "tracks")
        context: dict[str, object] = {
            "domain_context": domain_context,
            "tracks": tracks,
        }

        state.set_stage("discovery", "running")
        planner = TrackPlannerProfile()
        context.update(planner.run(context))
        self.validator.validate_payload(context["search_plan"], "search_plan")
        search_plan_path = self.store.write_json(
            state.run_id,
            "discovery/search-plan.json",
            context["search_plan"],
        )
        state.add_artifact(
            path=search_plan_path,
            stage="discovery",
            artifact_type="search_plan",
            description="Track-derived search plan.",
        )

        discovery = (
            FixtureDiscoveryProfile(discovery_fixture_path)
            if discovery_fixture_path is not None
            else ZeroResultDiscoveryProfile()
        )
        context.update(discovery.run(context))
        self.validator.validate_payload(context["discovery_sessions"], "discovery_sessions")
        raw_sessions_path = self.store.write_json(
            state.run_id,
            "discovery/raw-sessions.json",
            context["discovery_sessions"],
        )
        state.add_artifact(
            path=raw_sessions_path,
            stage="discovery",
            artifact_type="discovery_sessions",
            description="Raw discovery sessions before interpretation.",
        )
        state.set_count("search_plan_count", len(context["search_plan"]))
        state.set_count("discovery_session_count", len(context["discovery_sessions"]))
        state.set_count(
            "raw_link_count",
            sum(len(item.get("links", [])) for item in context["discovery_sessions"]),
        )

        state.set_stage("validation", "running")
        filter_profile = FilterValidateProfile()
        context.update(filter_profile.run(context))
        filtered_path = self.store.write_json(
            state.run_id,
            "validation/01-filtered-sources.json",
            context["filtered_sources"],
        )
        state.add_artifact(
            path=filtered_path,
            stage="validation",
            artifact_type="filtered_sources",
            description="Deduplicated and technically validated sources.",
        )
        state.set_count("filtered_source_count", len(context["filtered_sources"]))
        state.set_count("needs_review_count", context["filter_meta"]["needs_review_count"])

        state.set_stage("enrichment", "running")
        enrich_profile = SemanticEnrichmentProfile()
        context.update(enrich_profile.run(context))
        enriched_path = self.store.write_json(
            state.run_id,
            "enrichment/02-enriched-sources.json",
            context["enriched_sources"],
        )
        state.add_artifact(
            path=enriched_path,
            stage="enrichment",
            artifact_type="enriched_sources",
            description="Sources enriched with inherited track semantics and heuristic metadata.",
        )
        state.set_count("enriched_source_count", len(context["enriched_sources"]))

        state.set_stage("handoff", "running")
        rank_profile = RankAccessProfile(limit=limit)
        context.update(rank_profile.run(context))
        self.validator.validate_payload(context["ranked_sources"], "source_inventory")
        ranked_sources_path = self.store.write_json(
            state.run_id,
            "handoff/03-ranked-sources.json",
            context["ranked_sources"],
        )
        state.add_artifact(
            path=ranked_sources_path,
            stage="handoff",
            artifact_type="source_inventory",
            description="Ranked source inventory prepared for handoff.",
        )
        state.set_count("ranked_source_count", len(context["ranked_sources"]))

        handoff_profile = HandoffBuilderProfile()
        context.update(handoff_profile.run(context))
        self.validator.validate_payload(context["handoff"], "handoff")
        handoff_path = self.store.write_json(
            state.run_id,
            "handoff/handoff.json",
            context["handoff"],
        )
        state.add_artifact(
            path=handoff_path,
            stage="handoff",
            artifact_type="handoff",
            description="Collection handoff contract.",
        )
        state.set_count("handoff_target_count", len(context["handoff"]["targets"]))
        state.set_count("handoff_ready_count", context["handoff"]["ready_count"])
        state.set_count("handoff_needs_review_count", context["handoff"]["needs_review_count"])
        state.manifest["outputs"] = {
            "search_plan": str(search_plan_path),
            "raw_sessions": str(raw_sessions_path),
            "filtered_sources": str(filtered_path),
            "enriched_sources": str(enriched_path),
            "ranked_sources": str(ranked_sources_path),
            "handoff": str(handoff_path),
        }
        state.set_stage("handoff", "complete")
        manifest_path = state.save()

        return DiscoveryHandoffResult(
            run_id=state.run_id,
            run_dir=self.store.run_dir(state.run_id),
            manifest_path=manifest_path,
            handoff_path=handoff_path,
            ranked_sources_path=ranked_sources_path,
        )
