"""Track planning profile."""

from __future__ import annotations

from typing import Any

from evidence_flow.profiles.base import BaseProfile


class TrackPlannerProfile(BaseProfile):
    """Build a search plan from domain context and explicit tracks."""

    name = "track-planner"
    stage = "discovery"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        domain_context: dict[str, Any] = context["domain_context"]
        tracks: list[dict[str, Any]] = context["tracks"]
        search_plan = []

        for index, track in enumerate(tracks, start=1):
            query_text = self._compose_query(domain_context=domain_context, track=track)
            search_plan.append(
                {
                    "query_id": f"q-{index:03d}",
                    "query_text": query_text,
                    "target_intent": track["target_intent"],
                    "research_track": track["research_track"],
                    "chat_label": track["chat_label"],
                    "research_question": track["research_question"],
                    "task_prompt": track["task_prompt"],
                    "priority": track["priority"],
                    "domain_layer": track["domain_layer"],
                    "hierarchy_level": track["hierarchy_level"],
                    "thematic_axis": track["thematic_axis"],
                    "source_hints": list(track.get("source_hints", [])),
                    "expected_formats": list(track.get("expected_formats", [])),
                    "target_parameters": list(track.get("target_parameters", [])),
                    "coverage_target": dict(track["coverage_target"]),
                }
            )

        return {
            "search_plan": search_plan,
            "planning_meta": {
                "planned_query_count": len(search_plan),
                "profile": self.name,
            },
        }

    @classmethod
    def _compose_query(cls, *, domain_context: dict[str, Any], track: dict[str, Any]) -> str:
        parts: list[str] = []

        question = cls._compact_text(track.get("research_question", ""), 420)
        if question:
            parts.append(f"Primary question: {question}")

        task = cls._compact_text(track.get("task_prompt", ""), 720)
        if task:
            parts.append(f"Task: {task}")

        geo = cls._compact_list(domain_context.get("geographic_scope", []), 2, 260)
        if geo:
            parts.append(f"Scope: {geo}")

        preferred = cls._compact_list(domain_context.get("preferred_sources", []), 6, 320)
        if preferred:
            parts.append(f"Prioritize primary source pages, catalogs, APIs, and downloads from: {preferred}")

        outputs = cls._compact_list(domain_context.get("expected_outputs", []), 3, 220)
        if outputs:
            parts.append(f"Look for evidence that supports: {outputs}")

        exclusions = cls._compact_list(domain_context.get("exclusions", []), 3, 220)
        if exclusions:
            parts.append(f"Avoid: {exclusions}")

        parts.append("Prefer sources exposing metadata, filters, APIs, or direct downloads.")
        return ". ".join(parts)

    @staticmethod
    def _compact_text(value: str, limit: int) -> str:
        cleaned = " ".join(str(value or "").split())
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: max(limit - 3, 0)].rstrip() + "..."

    @classmethod
    def _compact_list(cls, values: list[str], max_items: int, limit: int) -> str:
        items = [" ".join(str(value or "").split()) for value in values if str(value or "").strip()]
        if not items:
            return ""
        return cls._compact_text("; ".join(items[:max_items]), limit)

