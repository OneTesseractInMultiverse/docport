# ADR 0001 Store Observation and Error Boundary

## Status

Accepted on 2026-04-13.

## Context

`docport` sits at a service boundary.
Callers need stable error types, stable correlation data, and safe telemetry fields.
MongoDB driver faults should not escape as raw driver errors.
Partial or private payload data should stay out of error text and hook data.

## Decision

The public store methods accept `StoreOperationContext`.
The context holds `correlation_id`, `causation_id`, and `actor`.
The adapter creates a new `correlation_id` when the caller omits one.

The adapter emits `StoreObservation` records at start and finish through an opt-in hook.
The record keeps stable field names and safe values.
The adapter omits raw filters, raw document payloads, secrets, and driver text.

Domain rule failures use domain errors.
Driver, transport, and dependency faults use `StoreDependencyError`.
The adapter maps raw `PyMongoError` values into that safe public error.

## Consequences

Callers keep one contract across sync and async stores.
Transport layers can map error codes to safe replies.
Operators can join logs, metrics, traces, and audit events with the same correlation fields.
Service teams keep control of hook wiring and alert routing.

## Ownership

Service owners create or receive the context at the first edge.
Transport owners map public errors to replies.
Platform owners keep the observation field set stable.
Operations owners decide where the hook data lands and who reviews alerts.

## Evidence

See [../observability-and-error-handling.md](../observability-and-error-handling.md), [../../src/docport/domain/observability.py](../../src/docport/domain/observability.py), [../../src/docport/adapters/mongo_store.py](../../src/docport/adapters/mongo_store.py), and [../../tests/docport/adapters/test_mongo_store.py](../../tests/docport/adapters/test_mongo_store.py).
