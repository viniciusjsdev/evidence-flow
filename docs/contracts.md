# Contracts

This directory defines the minimum executable contracts for the harness.

## Domain Context

The domain context defines why the run exists and what counts as useful
evidence.

Minimum fields:

- `domain_id`
- `domain_name`
- `objective`
- `primary_question`
- `temporal_scope`
- `thematic_axes`
- `preferred_sources`
- `expected_outputs`
- `success_criteria`

## Tracks

Tracks decompose the context into operational research units.

Each track declares:

- research question
- target intent
- domain layer
- hierarchy level
- thematic axis
- source hints
- expected formats
- target parameters
- coverage target

## Manifest

The manifest records run state and stage outputs.

It should stay small enough to inspect, but complete enough to answer what
happened in the run.

## Handoff

The handoff is the contract between discovery/ranking and collection.

Each target must include at least:

- rank
- source name
- initial URL or access path
- domain layer
- priority
- access type
- expected format
- expected period
- parameters
- suggested collection method
- review status

