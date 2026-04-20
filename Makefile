SHELL := /bin/bash

PACKAGE_SOURCE := src
TEST_PATHS := tests
COVERAGE_PACKAGE := docport

.PHONY: setup install-hooks install-pre-commit install-pre-push hooks format lint typecheck test check build clean deps-update bump bump-major bump-minor bump-patch tag tag-push release help

setup:
	@echo "Preparing development environment..."
	uv sync --group dev
	@$(MAKE) install-hooks

install-hooks:
	@$(MAKE) install-pre-commit
	@$(MAKE) install-pre-push

install-pre-commit:
	uv run pre-commit install --hook-type pre-commit

install-pre-push:
	uv run pre-commit install --hook-type pre-push

hooks:
	uv run pre-commit run --all-files

format:
	uv run ruff format $(PACKAGE_SOURCE) $(TEST_PATHS)
	uv run ruff check $(PACKAGE_SOURCE) $(TEST_PATHS) --fix

lint:
	uv run ruff check $(PACKAGE_SOURCE) $(TEST_PATHS)
	uv run ruff format --check $(PACKAGE_SOURCE) $(TEST_PATHS)

typecheck:
	uv run mypy $(PACKAGE_SOURCE)

test:
	uv run pytest -vv --cov=$(COVERAGE_PACKAGE) --cov-branch --cov-fail-under=100

check: lint typecheck test

build: clean
	uv build --no-sources

deps-update:
	uv sync --group dev --upgrade
	uv lock --upgrade

bump:
	uv run python tools/version.py bump $(BUMP)
	$(MAKE) hooks
	$(MAKE) test

bump-patch:
	BUMP=patch $(MAKE) bump

bump-minor:
	BUMP=minor $(MAKE) bump

bump-major:
	BUMP=major $(MAKE) bump

tag:
	@version=$$(uv run python tools/version.py get) && echo "Tagging v$$version" && git tag -a "v$$version" -m "Release v$$version"

tag-push:
	git push origin --tags

release:
	uv run python tools/release.py

clean:
	rm -rf .coverage .coverage.* .pytest_cache .mypy_cache .ruff_cache dist build .venv

help:
	@echo "Available targets:"
	@echo "  setup              - Install dev dependencies and pre-commit hooks"
	@echo "  install-hooks      - Install pre-commit and pre-push hooks"
	@echo "  hooks              - Run all pre-commit hooks"
	@echo "  format             - Format and auto-fix with Ruff"
	@echo "  lint               - Check Ruff lint and formatting"
	@echo "  typecheck          - Run mypy"
	@echo "  test               - Run pytest with coverage gate"
	@echo "  check              - Run lint, typecheck, and tests"
	@echo "  build              - Build source and wheel distributions"
	@echo "  deps-update        - Upgrade uv development dependencies and regenerate lockfile"
	@echo "  bump-major         - Bump MAJOR and reset MINOR/PATCH to 0"
	@echo "  bump-minor         - Bump MINOR and reset PATCH to 0"
	@echo "  bump-patch         - Bump PATCH only"
	@echo "  release            - Interactive version bump"
	@echo "  clean              - Remove generated cache and build artifacts"
