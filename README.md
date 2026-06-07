# Evidence Flow

Evidence Flow is a generic research harness for turning an explicit research
context into auditable evidence, analysis, and narrative.

It is not just a search pipeline and not just a report generator. Its core job
is to preserve the chain:

```text
domain context
  -> tracks
  -> discovery
  -> validation
  -> enrichment
  -> access ranking
  -> handoff
  -> collection
  -> raw artifacts
  -> staging
  -> analytic
  -> EDA
  -> report context
  -> renderer
  -> learning
```

Each stage should produce a persistent artifact with enough provenance to answer:

- where the evidence came from
- when it was collected
- which method or adapter produced it
- which contract validated it
- what coverage gaps or blockers remain

## Principles

- Context drives the pipeline. The harness does not search for generic data
  about a topic; it searches for sources that answer the declared context.
- Tracks are explicit operating units. Domain meaning must be declared in track
  configuration rather than inferred from file names or opaque scores.
- Raw artifacts come before interpretation. Nothing enters staging or analytic
  outputs without a raw source artifact or an explicit blocked/partial note.
- LLMs may extract or summarize, but they do not found truth. Extracted fields
  must carry method, confidence, or review status.
- Handoffs are contracts, not conversations. Each stage must pass auditable
  artifacts downstream.
- Gaps are first-class outputs. Missing coverage, blockers, and uncertainty are
  part of the product.
- EDA serves the research question, not generic chart production.
- Reports consume structured context and final figures; they should not silently
  recompute or invent evidence.

## Repository Layout

```text
contexts/     Example and future domain contexts.
contracts/    JSON Schemas for executable stage contracts.
runs/         Local run outputs; generated runs are ignored by Git.
src/          Harness core, adapters, agents, and CLI.
docs/         Architecture and operating notes.
prompts/      Prompt contracts for optional LLM-assisted stages.
skills/       Versioned procedural workflows for repeated operations.
tests/        Contract and core behavior tests.
```

## Current Scope

This initial scaffold implements the first harness layer:

- JSON Schemas for `domain_context`, `tracks`, `manifest`, and `handoff`
- `ArtifactStore` for run directory creation and JSON/YAML/Markdown writes
- `RunState` for manifest lifecycle updates
- validators for JSON/YAML contracts
- a small CLI to validate inputs and initialize a run

Adapters for search, LLMs, browsers, collectors, staging, EDA, and renderers are
intentionally placeholders until their contracts are formalized.

## Quick Start

Validate the example context and tracks:

```bash
python -m evidence_flow.cli validate-context contexts/examples/generic_research_context.yaml
python -m evidence_flow.cli validate-tracks contexts/examples/generic_tracks.yaml
```

Initialize an auditable run:

```bash
python -m evidence_flow.cli init-run \
  --context contexts/examples/generic_research_context.yaml \
  --tracks contexts/examples/generic_tracks.yaml
```

The command creates a run under `runs/{run-id}/` with copied inputs and a
`manifest.json`.

## Installation

For local development:

```bash
python -m pip install -e .[dev]
```

The core is intentionally small. Runtime dependencies are limited to JSON Schema
validation and YAML parsing.

