# Architecture

Evidence Flow is organized around contracts between persistent stages.

## Stage Chain

```text
Domain Context
  -> Track Planner
  -> Search / Discovery Adapter
  -> Filter + Validate
  -> Semantic Enrichment
  -> Access Ranking
  -> Handoff Builder
  -> Operational Collection
  -> Raw Artifact Store
  -> Staging Builder
  -> Analytic Builder
  -> EDA Generator
  -> Report Context Builder
  -> Renderer
  -> Learning + Memory Update
```

## Generic Core

The core owns:

- run directory creation
- artifact writing
- manifest lifecycle
- schema validation
- stage completion checks
- adapter interfaces
- CLI orchestration

The core should not own domain taxonomies, source lists, parameter units,
visual templates, or narrative assumptions.

## Domain Configuration

Domain configuration owns:

- objective
- primary question
- spatial, temporal, institutional, or conceptual scope
- thematic axes
- preferred sources
- exclusions
- expected outputs
- success criteria
- tracks and coverage contracts

## Adapter Boundary

External tools enter through adapters:

- `SearchAdapter`
- `LLMAdapter`
- `BrowserAdapter`
- `CollectionAdapter`
- `RendererAdapter`

The stage contract should be more stable than the external provider used to
execute it.

## Artifact Policy

Every artifact should carry enough context to be traced back to:

- run id
- stage
- source or parent artifact
- method
- generated timestamp
- validation status
- known gaps or blockers

