# Testing Guide

This repo follows the playbook rule that unit tests should run after clone with normal language setup only.
The store tests stay in memory and use `mongomock`.

## Why `mongomock` is the default test backing store

The Mongo adapters need real query behavior, sort behavior, projection behavior, and update behavior.
Mocking each driver call would hide too much of that work.
`mongomock` gives a better fit for this repo.

The sync adapter talks to `mongomock` directly.
The async adapter uses a thin async wrapper over the same in-memory collection.
That keeps both adapter test suites close to real behavior and keeps the local test loop fast.

## Test layers in this repo

The test tree follows the package structure.

| Test area | What it proves |
| --- | --- |
| `tests/docport/domain` | Entity rules, metadata rules, and query helper behavior |
| `tests/docport/ports` | Store configuration rules for subclassed ports |
| `tests/docport/adapters` | MongoDB document mapping, adapter behavior, projection reads, and concurrency checks |
| `tests/docport/test_package_exports.py` | Public package exports |

## Concurrency tests

The update path is one of the highest value test areas in this repo.
Each adapter test suite covers two failure modes.

The first failure mode is a missing entity.
That should raise `EntityNotFoundError`.

The second failure mode is a stale entity version.
That should raise `EntityVersionConflictError`.

Those checks keep optimistic concurrency explicit and stable across refactors.

## Boundary telemetry tests

The adapter tests cover context propagation and driver fault mapping.
Each suite records `StoreObservation` rows and checks the `start`, `success`, and `failure` outcomes.
Each suite checks that `PyMongoError` becomes `StoreDependencyError`.
That keeps the public error boundary stable and keeps operator data in the test scope.

## Local command

Run the full suite with:

```bash
make test
```

Run lint and tests together with:

```bash
make check
```
