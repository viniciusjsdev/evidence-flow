# Agent Operating Contract

This repository is a generic evidence harness. Treat it as infrastructure for
auditable research workflows, not as a domain-specific analysis workspace.

## Core Rules

- Modify files only inside this repository when working on Evidence Flow.
- Keep the harness generic. Domain specifics belong in contexts, tracks,
  adapters, templates, or domain packages.
- Preserve the stage chain:

```text
external source -> raw/run artifact -> staging -> analytic -> EDA -> report
```

- Do not allow a later stage to erase provenance, blockers, uncertainty, or
  coverage gaps from an earlier stage.
- Prefer small, testable layers with explicit inputs and outputs.
- Validate contracts before moving artifacts between stages.
- Separate `Evidence`, `Inference`, `Assumption`, and `Open question` in any
  human-facing analytical artifact.
- Do not invent sources, URLs, datasets, parameter coverage, or temporal windows.
- Never store secrets, tokens, credentials, private account data, or unapproved
  private extracted text in the repository.

## Architecture

The intended harness flow is:

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

Each layer should be:

- contract-bound
- persistent
- auditable
- replaceable by adapter where external tools are involved

## Data Rules

- `runs/{run-id}/inputs/` stores the exact context and tracks used by a run.
- `runs/{run-id}/discovery/` stores search plans and raw discovery outputs.
- `runs/{run-id}/collection/` stores raw source artifacts.
- `runs/{run-id}/staging/` stores harmonized but still source-close datasets.
- `runs/{run-id}/analytic/` stores analysis-ready derived tables.
- `runs/{run-id}/reports/` stores report contexts and rendered outputs.
- `runs/{run-id}/manifest.json` records stage, status, artifacts, counts,
  coverage, warnings, and blockers.

Generated run outputs should remain ignored by Git unless explicitly promoted
as examples or fixtures.

## Implementation Rules

- Keep contracts in `contracts/` as JSON Schema.
- Keep reusable core behavior under `src/evidence_flow/harness/`.
- Keep adapters behind stable interfaces under `src/evidence_flow/adapters/`.
- Keep optional agent logic under `src/evidence_flow/agents/`.
- Keep prompts declarative and versioned under `prompts/`.
- Add tests when contracts or core run behavior changes.

## Stage Completion Policy

A stage is complete only when its minimum contract exists or its incompleteness
is explicitly recorded.

Examples:

- Discovery is complete when raw sessions or a zero-result note exist.
- Handoff is complete when targets have source, URL or access path, access type,
  expected format, status, and known gaps.
- Collection is complete when each target is `collected`, `partial`, `blocked`,
  or `error`, and raw artifacts or blockers are recorded.
- EDA is complete when figures or declared gaps map back to analytic inputs and
  research questions.
- Report is complete when narrative uses available evidence and keeps gaps
  visible.

