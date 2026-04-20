# Setting Up Pre-Commit Hooks

This page shows how to install the local hooks after cloning the repo.

## Sync development dependencies

From the repo root, install the managed development environment:

```bash
uv sync --group dev
```

This installs `pre-commit` and the rest of the local tooling used by the repo.

## Enable the hooks

Run this command from the repo root:

```bash
make install-hooks
```

This installs both the `.git/hooks/pre-commit` and `.git/hooks/pre-push` scripts.

## Run all hooks once

You can run the full hook set across the repo:

```bash
make hooks
```

## Confirm the setup

Make a small commit.
The hygiene hooks should run before the commit.
The repo should run the coverage hook before push.
