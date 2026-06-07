"""Access ranking profile."""

from __future__ import annotations

from typing import Any

from evidence_flow.profiles.base import BaseProfile


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FORMAT_ORDER = {
    "structured": 0,
    "semi_structured": 1,
    "geospatial_platform": 2,
    "academic_paper": 3,
    "pdf_report": 4,
    "unknown": 5,
}
EXT_ACCESS = {
    ".csv": "direct_download",
    ".xlsx": "direct_download",
    ".xls": "direct_download",
    ".zip": "direct_download",
    ".json": "api_access",
    ".pdf": "pdf_extraction",
}
FORMAT_TO_ACCESS = {
    "structured": "direct_download",
    "semi_structured": "web_portal",
    "geospatial_platform": "geospatial_platform",
    "pdf_report": "pdf_extraction",
    "academic_paper": "pdf_extraction",
    "unknown": "unknown",
}


class RankAccessProfile(BaseProfile):
    """Rank sources by priority and accessibility."""

    name = "rank-access"
    stage = "handoff"

    def __init__(self, *, limit: int = 40) -> None:
        self.limit = limit

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        sources: list[dict[str, Any]] = list(context.get("enriched_sources", []))
        ranked_input = sorted(
            sources,
            key=lambda item: (
                PRIORITY_ORDER.get(item.get("track_priority", "medium"), 9),
                FORMAT_ORDER.get(item.get("data_format", "unknown"), 9),
            ),
        )
        if self.limit:
            ranked_input = ranked_input[: self.limit]

        ranked = []
        for rank, source in enumerate(ranked_input, start=1):
            access_type, access_notes = self._classify_access(source)
            review_status = "needs_review" if source.get("needs_review") else "ready"
            if access_type in {"restricted", "unknown"}:
                review_status = "needs_review"
            ranked.append(
                {
                    **source,
                    "rank": rank,
                    "access_type": access_type,
                    "access_notes": access_notes,
                    "review_status": review_status,
                }
            )

        return {
            "ranked_sources": ranked,
            "rank_meta": {
                "profile": self.name,
                "ranked_count": len(ranked),
                "access_summary": self._count_by(ranked, "access_type"),
                "format_summary": self._count_by(ranked, "data_format"),
                "layer_summary": self._count_by(ranked, "domain_layer"),
            },
        }

    @staticmethod
    def _classify_access(source: dict[str, Any]) -> tuple[str, str]:
        url = str(source.get("url", "")).lower()
        for ext, access_type in EXT_ACCESS.items():
            if url.endswith(ext) or f"{ext}?" in url:
                return access_type, ""
        if "api" in url or "query" in url:
            return "api_access", "URL suggests queryable API access."
        access_type = FORMAT_TO_ACCESS.get(source.get("data_format", "unknown"), "unknown")
        return access_type, ""

    @staticmethod
    def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = str(item.get(key, "unknown"))
            counts[value] = counts.get(value, 0) + 1
        return counts

