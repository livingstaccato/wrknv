# Repository Guidelines

## Project Structure & Module Organization
- `src/wrknv/` holds the package; `cli/hub_cli.py` exposes the entry point, `wenv/` manages environment generation, `managers/` wrap tool installers, and `templates/env/` stores the Jinja2 templates used for generated scripts.
- `tests/` mirrors those modules (`cli/`, `managers/`, `container/`, etc.) and provides fixtures in `conftest.py`; add new specs beside the code under test.
- `docs/` powers the MkDocs site, while `dist/`, `workenv/`, and `htmlcov/` are build artefacts—avoid committing changes there.
- Configuration anchors include `wrknv.toml`, `pyproject.toml`, and helper scripts in `scripts/`.

## Build, Test, and Development Commands
- Install dependencies with `uv sync`; this primes the `workenv/` directory and pulls dev extras.
- Run the CLI via `uv run wrknv status`, `generate`, or other subcommands to confirm changes interact correctly.
- Execute the default suite using `uv run pytest`, which filters out `integration`, `slow`, and `benchmark`; add `-m integration` when those paths matter.
- Produce release artefacts with `uv build` or the bundled `uv run wrknv build`.

## Coding Style & Naming Conventions
- Use 4-space indentation, double quotes, and a 111-character line limit as enforced by Ruff.
- Format and lint prior to review with `uv run ruff format src tests` and `uv run ruff check`.
- Keep strict typing: `uv run mypy src` should pass locally; prefer dataclasses and TypedDicts over untyped dicts.
- Name managers `<tool>_manager.py`, CLI commands `<feature>_command.py`, and expose them through hub decorators to keep discovery consistent.

## Testing Guidelines
- Tests use pytest; leverage the markers in `pyproject.toml` (`unit`, `integration`, `cli`, etc.) and guard expensive scenarios with the right marker.
- Keep coverage above the configured 70% threshold by running `uv run pytest --cov=src/wrknv --cov-report=term-missing`.
- Integration and Docker-dependent cases must opt in with `@pytest.mark.integration` or `@pytest.mark.requires_docker` to keep CI green.
- Reuse fixtures in `tests/conftest.py` and shared helpers under `tests/utils/` to avoid duplicating setup logic.

## Commit & Pull Request Guidelines
- Use short, imperative commit titles; behavioural changes follow the observed `fix:`/`feat:` prefixing pattern from the history.
- Reference issues with `#123` and include a brief body describing context, risk, and rollout notes when needed.
- Pull requests should summarise intent, list `uv run pytest` (and any targeted markers) in the testing section, and call out docs/template updates when behaviour changes.
- Request reviews early for large refactors and link architecture notes when touching core workflows (CLI hub, managers, or template rendering).
