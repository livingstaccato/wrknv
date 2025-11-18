# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`wrknv` (Work Environment) is a Python tool that generates standardized development environment scripts (`env.sh` and `env.ps1`) for the provide.io ecosystem. It manages tool versions, sibling package integration, and containerized development environments.

## Development Commands

### Running Tests
```bash
# Run all tests with coverage
uv sync
python -m pytest tests/ -v --cov=src/wrknv --cov-report=term-missing

# Run specific test file
python -m pytest tests/path/to/test_file.py -xvs

# Run tests with specific markers
python -m pytest -m unit  # Unit tests only
python -m pytest -m cli   # CLI tests only
```

### Code Quality
```bash
# Linting and formatting
uv run ruff check src tests
uv run ruff format src tests

# Type checking
uv run mypy src --ignore-missing-imports
```

### Building and Installing
```bash
# Build distribution
uv build

# Install in development mode (uses workenv/ not .venv/)
uv sync
uv pip install -e .
```

## Architecture

### Core Components

**CLI Hub (`src/wrknv/cli/hub_cli.py`)**: Main entry point using `provide.foundation.hub` for command registration. Commands are loaded via decorators from separate command modules.

**Config System (`src/wrknv/wenv/config.py`, `schema.py`)**: Uses TOML configuration with `WorkenvConfig` schema. Supports tool version management, sibling patterns, and container settings.

**Environment Generation (`src/wrknv/wenv/env_generator.py`)**: Jinja2-based template system that generates `env.sh` and `env.ps1` scripts from templates in `src/wrknv/templates/env/`.

**Tool Managers (`src/wrknv/wenv/managers/`)**: Abstract base class pattern for tool installation/management. Implementations for UV, Terraform, OpenTofu, Go, etc. Each manager handles platform-specific download URLs and verification.

**Container Management (`src/wrknv/container/`)**: Experimental Docker-based development environment management with runtime abstraction and operations (build, exec, lifecycle, volumes).

### Key Design Patterns

- **Hub Pattern**: Commands are registered via decorators to a central hub, avoiding large monolithic CLI files
- **Manager Pattern**: Each tool (UV, Terraform, etc.) has its own manager class inheriting from `ToolManager` base
- **Operation Pattern**: Complex operations (download, verify, install) are separated into focused modules
- **Schema-driven Config**: All configuration uses typed schemas via `cattrs` for serialization/validation

## Important Notes

- **Python 3.11+ only**: Uses modern type hints (`str | None`), native TOML support via `tomllib`
- **No hardcoded defaults**: Configuration must be explicit - never assume default values
- **Virtual environment location**: Always use `workenv/` directory, never `.venv/`
- **Testing**: Comprehensive test coverage with TDD approach - tests in `tests/` mirror `src/` structure
- **No backward compatibility**: Project prioritizes clean, modern code over migration support