# Contributing to DocPort

This project welcomes clear, tested, and review-ready changes.
Use this guide before opening a pull request.

## Standards

`DocPort` follows open-source practices used in Python packages.
We focus on readable design, strong typing, and stable tests.

## Setup

Use `uv` to install dependencies.
All tools live in the dev group.

```bash
uv sync --group dev
```

Install hooks for commit checks and push checks.

```bash
make install-hooks
```

## Branching and contributions

Open an issue before large changes.
Use one issue per behavior or bug.

Create a topic branch from the main branch.
Name branches with the pattern `type/short-summary`.
Examples:

- `feature/add-typed-float-env`
- `fix/missing-default-handling`
- `docs/improve-contribution-guide`

Open a pull request when work is ready for review.
Keep changes small and focused.

## Code quality rules

All contributions must pass local checks before review.
Run this command before requesting review.

```bash
make hooks
```

This project uses:

- Ruff for linting and formatting
- Mypy for static type checks
- Pytest and Coverage for tests with 100 percent minimum

These checks are the minimum for PR acceptance.

## Testing expectations

All tests must be self contained.
No test may depend on host environment variables or hidden setup.

All test methods should use one assertion per method.
If one method needs multiple outcomes, split cases into helper checks or separate methods in one class.

Test files should mirror the package layout.
For a module `src/docport/foo.py`, write tests in `tests/docport/test_foo.py`.

Run the full suite locally:

```bash
uv run pytest
```

Run coverage with the repo gate:

```bash
uv run pytest --cov=docport --cov-branch --cov-fail-under=100
```

## Code style and architecture

Write focused classes with one responsibility each.
Prefer simple coordinators and computation methods.
Keep class methods short and clear.

Each public function and class should include docstrings.
Use direct names and explicit types.

Avoid hard-coded values inside modules.
Put defaults and environment names in class field definitions.

## Documentation and API changes

Update docs when behavior or public API changes.
Add README examples for each public feature.
Keep API docs tied to class and function intent.

If you change exported symbols, update:

- [README.md](README.md)
- Any module exports in [src/docport/__init__.py](src/docport/__init__.py)
- Existing tests that cover old behavior

## Commit and PR hygiene

Use clear, descriptive commit messages.
Write one logical change per commit.

Before opening a PR, include:

- Summary of problem and fix
- Files changed
- Tests run and outcomes
- Any backward compatibility notes

## Security and dependencies

Do not check in secrets.
Use environment values only in docs or tests that mock values.

Review dependency changes in `pyproject.toml` for license and stability.
Prefer stable, maintained packages with low risk.

For security concerns, follow [SECURITY.md](SECURITY.md).

## Review process

A maintainer will check style, behavior, and test coverage.
If needed, ask for follow-up tests or docs.
After review, squash commits when requested.

Thank you for helping keep this project clean and usable.
