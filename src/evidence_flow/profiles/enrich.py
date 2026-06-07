"""Semantic enrichment profile."""

from __future__ import annotations

from typing import Any

from evidence_flow.profiles.base import BaseProfile


INTENT_TO_CATEGORY = {
    "dataset_discovery": "dataset",
    "academic_knowledge": "academic",
    "contextual_intelligence": "contextual",
}


class SemanticEnrichmentProfile(BaseProfile):
    """Add inherited track semantics and heuristic source metadata."""

    name = "semantic-enrichment"
    stage = "enrichment"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        enriched = []
        for source in context.get("filtered_sources", []):
            extracted = self._heuristic_extraction(source)
            enriched.append(
                {
                    **source,
                    "source_category": self._category_from_source(source),
                    "dataset_name": extracted["dataset_name"],
                    "dataset_description": extracted["dataset_description"],
                    "data_format": extracted["data_format"],
                    "temporal_coverage": extracted["temporal_coverage"],
                    "spatial_coverage": extracted["spatial_coverage"],
                    "key_parameters": extracted["key_parameters"],
                    "enrichment_method": "heuristic",
                }
            )

        return {
            "enriched_sources": enriched,
            "enrich_meta": {
                "profile": self.name,
                "enriched_count": len(enriched),
                "execution_mode": "heuristic",
            },
        }

    @staticmethod
    def _category_from_source(source: dict[str, Any]) -> str:
        domain = str(source.get("source_domain", "")).lower()
        if ".gov" in domain or ".mil" in domain:
            return "official_portal"
        if ".edu" in domain or "doi.org" in domain or "openalex" in domain:
            return "academic"
        return INTENT_TO_CATEGORY.get(source.get("track_intent", ""), "contextual")

    @classmethod
    def _heuristic_extraction(cls, source: dict[str, Any]) -> dict[str, Any]:
        text = " ".join([source.get("title", ""), source.get("snippet", ""), source.get("url", "")]).lower()
        title = str(source.get("title") or "Unnamed source").strip()
        parameters = cls._extract_parameters(text, source.get("target_parameters", []))
        return {
            "dataset_name": title[:140],
            "dataset_description": cls._build_description(source),
            "data_format": cls._infer_format(text, source.get("expected_formats", [])),
            "temporal_coverage": None,
            "spatial_coverage": None,
            "key_parameters": parameters,
        }

    @staticmethod
    def _build_description(source: dict[str, Any]) -> str:
        snippet = " ".join(str(source.get("snippet", "")).split())
        if snippet:
            return snippet[:260]
        return "No source description was available in the raw discovery artifact."

    @staticmethod
    def _extract_parameters(text: str, target_parameters: list[str]) -> list[str]:
        matched = [param for param in target_parameters if param.lower() in text]
        return matched or list(target_parameters[:5])

    @staticmethod
    def _infer_format(text: str, expected_formats: list[str]) -> str:
        if any(token in text for token in [".csv", " csv ", "comma-separated"]):
            return "structured"
        if any(token in text for token in [".json", " api ", " endpoint", "rest"]):
            return "structured"
        if any(token in text for token in [".xlsx", ".xls", "excel"]):
            return "structured"
        if any(token in text for token in [".zip", "shapefile", "geotiff", "geospatial"]):
            return "geospatial_platform"
        if ".pdf" in text or "pdf" in expected_formats:
            return "pdf_report"
        if "academic_paper" in expected_formats:
            return "academic_paper"
        if "web_portal" in expected_formats:
            return "semi_structured"
        return "unknown"

