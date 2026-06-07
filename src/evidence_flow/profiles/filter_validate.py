"""Filter and validate raw discovery links."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from evidence_flow.profiles.base import BaseProfile


class FilterValidateProfile(BaseProfile):
    """Deduplicate and technically validate raw sources without LLMs."""

    name = "filter-validate"
    stage = "validation"
    min_snippet_len = 20

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        sessions: list[dict[str, Any]] = context.get("discovery_sessions", [])
        search_plan: list[dict[str, Any]] = context.get("search_plan", [])
        plan_by_query = {item["query_id"]: item for item in search_plan}

        seen_urls: set[str] = set()
        filtered: list[dict[str, Any]] = []
        skipped_malformed = 0
        skipped_short_snippet = 0
        skipped_duplicate = 0
        review_count = 0

        for session in sessions:
            if session.get("collection_status") != "ok":
                continue
            query = plan_by_query.get(session.get("query_id", ""), {})

            for link in session.get("links", []):
                normalized = self._normalize_url(str(link.get("url", "")))
                if not normalized:
                    skipped_malformed += 1
                    continue
                if normalized in seen_urls:
                    skipped_duplicate += 1
                    continue
                seen_urls.add(normalized)

                notes: list[str] = []
                needs_review = False
                snippet = str(link.get("snippet", "")).strip()
                if len(snippet) < self.min_snippet_len:
                    skipped_short_snippet += 1
                    needs_review = True
                    notes.append("short_snippet")

                if needs_review:
                    review_count += 1

                filtered.append(
                    {
                        "url": normalized,
                        "title": str(link.get("title") or link.get("domain") or normalized).strip(),
                        "snippet": snippet,
                        "source_domain": self._extract_domain(normalized),
                        "track_origin": session.get("research_track", ""),
                        "track_priority": query.get("priority", "medium"),
                        "track_intent": session.get("target_intent", "dataset_discovery"),
                        "domain_layer": query.get("domain_layer", ""),
                        "hierarchy_level": query.get("hierarchy_level", "custom"),
                        "thematic_axis": query.get("thematic_axis", ""),
                        "source_hints": list(query.get("source_hints", [])),
                        "expected_formats": list(query.get("expected_formats", [])),
                        "target_parameters": list(query.get("target_parameters", [])),
                        "coverage_target": dict(query.get("coverage_target", {"years": 0, "required": False})),
                        "needs_review": needs_review,
                        "filter_notes": notes,
                    }
                )

        return {
            "filtered_sources": filtered,
            "filter_meta": {
                "profile": self.name,
                "total_sessions": len(sessions),
                "ok_sessions": sum(1 for item in sessions if item.get("collection_status") == "ok"),
                "error_sessions": sum(1 for item in sessions if item.get("collection_status") == "error"),
                "zero_result_sessions": sum(
                    1 for item in sessions if item.get("collection_status") == "zero_result"
                ),
                "total_links_seen": len(seen_urls) + skipped_duplicate + skipped_malformed,
                "filtered_source_count": len(filtered),
                "skipped_malformed": skipped_malformed,
                "skipped_short_snippet": skipped_short_snippet,
                "skipped_duplicate": skipped_duplicate,
                "needs_review_count": review_count,
            },
        }

    @staticmethod
    def _normalize_url(url: str) -> str:
        try:
            parsed = urlparse(url.strip())
        except Exception:
            return ""
        if not parsed.scheme or not parsed.netloc:
            return ""
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            return urlparse(url).netloc.replace("www.", "").strip().lower()
        except Exception:
            return ""

