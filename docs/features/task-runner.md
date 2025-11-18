# Task Runner Feature Specification

## Overview

The task runner feature enables wrknv to execute predefined tasks from `wrknv.toml` configuration files, providing a unified interface for common development operations across all provide.io repositories.

## Goals

1. **Single Command Interface**: Developers run tasks via `wrknv run <task-name>`
2. **TOML-Based Configuration**: Tasks defined in existing `wrknv.toml` files
3. **Simple Syntax**: Both simple string commands and complex task definitions
4. **Composability**: Tasks can depend on or run other tasks
5. **Discoverability**: `wrknv tasks` lists all available tasks

## Features

- **Auto-Detection**: Automatically detects environment and chooses optimal execution strategy
- **Editable Install Preservation**: Detects editable installs and preserves them (no `uv run`)
- **UV Integration**: Automatically uses `uv run` for UV projects when appropriate
- **Process Title Management**: Sets meaningful process titles for better process visibility
- **Flexible Configuration**: Global defaults with per-task overrides

## Non-Goals (Future Work)

- Workspace-level task orchestration (Phase 2)
- Parallel task execution (Phase 2)
- Task result caching (Phase 3)
- Remote task execution (Phase 3)

## Configuration Format

### Simple Tasks

> **Note**: No need to prefix commands with `uv run` - wrknv auto-detects the environment!

```toml
[tasks]
test = "pytest tests/"
lint = "ruff check src/ tests/"
format = "ruff format src/ tests/"
```

### Complex Tasks

```toml
[tasks.build]
run = "python -m build"
description = "Build Python package"
env = { PYTHONPATH = "src" }
working_dir = "."
timeout = 300  # Optional: task timeout in seconds
stream_output = true  # Optional: stream output in real-time

[tasks.test-verbose]
run = "pytest tests/ -vvv --tb=long"
description = "Run tests with verbose output"
depends_on = ["format", "lint"]
process_title_format = "full"  # Optional: "full", "leaf", or "abbreviated"
```

### Advanced Configuration

```toml
# Force UV run for specific task (override auto-detection)
[tasks.build-with-uv]
run = "python -m build"
execution_mode = "uv_run"

# Explicitly disable prefix
[tasks.system-python]
run = "python --version"
command_prefix = ""  # Empty string = no prefix

# Custom prefix
[tasks.docker-test]
run = "pytest tests/"
command_prefix = "docker run myimage"
```

### Composite Tasks

```toml
[tasks.quality]
run = ["lint", "typecheck"]
description = "Run all quality checks"

[tasks.ci]
run = ["quality", "test", "build"]
description = "Complete CI pipeline"
```

## Command Interface

### Run Tasks

```bash
# Run single task
wrknv run test

# Run multiple tasks sequentially
wrknv run lint format typecheck

# Show what would be executed
wrknv run build --dry-run

# Override environment variables
wrknv run test --env PYTEST_WORKERS=4 --env DEBUG=1

# Show task information
wrknv run test --info
```

### List Tasks

```bash
# List all tasks
wrknv tasks

# List with details
wrknv tasks --verbose
```

## Task Execution Model

### Execution Flow

1. Load `wrknv.toml` from current directory
2. Parse `[tasks]` section
3. Resolve task name to `TaskConfig`
4. If composite task, recursively resolve subtasks
5. Execute command(s) in subprocess
6. Capture stdout/stderr
7. Report results

### Environment

- Inherits current shell environment
- Merges task-specific `env` variables
- Supports `--env` CLI overrides

### Working Directory

- Defaults to repository root (directory containing `wrknv.toml`)
- Configurable via `working_dir` in task config

### Error Handling

- Non-zero exit code stops execution
- For composite tasks, first failure stops remaining tasks
- Error output displayed to stderr
- Exit code propagated to shell

## Environment Auto-Detection

wrknv automatically detects the optimal execution strategy for tasks:

### Detection Priority

1. **Environment Variable Override**: `WRKNV_TASK_RUNNER` env var (highest priority)
2. **Editable Install**: If package is installed with `pip install -e .`, use direct execution with PATH modification
3. **UV Project**: If `uv.lock` or `[tool.uv]` in pyproject.toml exists, use `uv run`
4. **Virtual Environment**: If `.venv/`, `venv/`, or `workenv/` exists, use direct execution with PATH
5. **System Python**: Use system Python (lowest priority)

### Why This Matters

**Problem**: `uv run` uninstalls editable installs (UV issue #3843)
**Solution**: Auto-detect editable installs and use direct execution to preserve them

### Virtual Environment Detection

wrknv searches for virtual environments in this order:
1. `workenv/{package}_{os}_{arch}/` (wrknv pattern)
2. `.venv/` (standard)
3. `venv/` (fallback)
4. Current Python's venv (if already in one)

### Configuration Options

**Global Configuration** (wrknv.toml):
```toml
project_name = "myproject"
task_auto_detect = true  # Enable auto-detection (default)
execution_mode = "auto"  # "auto", "uv_run", "direct", or "system"
```

**Per-Task Override**:
```toml
[tasks.build]
run = "python -m build"
execution_mode = "direct"  # Override auto-detection
command_prefix = "uv run"  # Or custom prefix
```

**Environment Variable Override**:
```bash
# Override for all tasks
export WRKNV_TASK_RUNNER="poetry run"
wrknv run test  # Uses "poetry run pytest tests/"

# Disable prefix
export WRKNV_TASK_RUNNER=""
wrknv run test  # Uses "pytest tests/" directly
```

### Migration Guide

**Before** (old pattern with hardcoded `uv run`):
```toml
[tasks]
test = "uv run pytest tests/"
lint = "uv run ruff check src/"
```

**After** (new pattern with auto-detection):
```toml
[tasks]
test = "pytest tests/"
lint = "ruff check src/"
```

wrknv will automatically:
- Use `uv run` if it's a UV project AND not editable
- Use direct execution (with PATH modification) if editable install detected
- Preserve your development workflow

## Data Models

### TaskConfig

```python
@define(frozen=True)
class TaskConfig:
    name: str
    run: str | list[str]  # Command or list of task names
    description: str | None = None
    env: dict[str, str] = field(factory=dict)
    depends_on: list[str] = field(factory=list)
    working_dir: Path | None = None
    namespace: str | None = None  # Parent namespace (e.g., "test" for test.unit)

    # Execution configuration
    timeout: float | None = None  # Task timeout in seconds
    stream_output: bool = False  # Stream output in real-time
    process_title_format: str = "full"  # "full", "leaf", "abbreviated"
    command_prefix: str | None = None  # Optional command prefix override
    execution_mode: str = "auto"  # "auto", "uv_run", "direct", "system"

    @property
    def is_composite(self) -> bool:
        """Check if task runs other tasks."""
        return isinstance(self.run, list)
```

### TaskResult

```python
@define
class TaskResult:
    task: TaskConfig
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
```

## Test Scenarios

### Basic Execution

- ✅ Load simple task from TOML
- ✅ Execute command and capture output
- ✅ Report success/failure
- ✅ Propagate exit codes

### Composite Tasks

- ✅ Execute multiple tasks in sequence
- ✅ Stop on first failure
- ✅ Aggregate results

### Environment Handling

- ✅ Inherit shell environment
- ✅ Merge task-specific environment
- ✅ Apply CLI overrides

### Error Cases

- ✅ Task not found
- ✅ Invalid TOML syntax
- ✅ Command execution failure
- ✅ Missing wrknv.toml file

### CLI Behavior

- ✅ `wrknv run <task>` executes task
- ✅ `wrknv run <task> --dry-run` shows command without executing
- ✅ `wrknv run <task> --info` displays task information
- ✅ `wrknv tasks` lists all tasks
- ✅ Exit codes match command results

## Examples

### Developer Workflow

```bash
# Morning: run tests
wrknv run test

# Before commit: quality checks
wrknv run quality

# Full CI locally
wrknv run ci

# Rebuild
wrknv run clean build
```

### Sample wrknv.toml

```toml
# wrknv/wrknv.toml

project_name = "wrknv"

[tasks]
# Simple tasks (no "uv run" needed - auto-detected!)
test = "pytest tests/ -v"
lint = "ruff check src/ tests/"
format = "ruff format src/ tests/"
typecheck = "mypy src/ --ignore-missing-imports"
clean = "rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache"

# Complex task with environment
[tasks.test-coverage]
run = "pytest tests/ --cov=src/wrknv --cov-report=term-missing"
description = "Run tests with coverage report"
env = { COVERAGE_CORE = "sysmon" }
stream_output = true  # Show output in real-time
timeout = 600  # 10 minute timeout

# Composite tasks
[tasks.quality]
run = ["lint", "typecheck"]
description = "Run all quality checks"

[tasks.ci]
run = ["quality", "test-coverage", "build"]
description = "Complete CI pipeline"

# Demo task
[tasks.hello]
run = "echo '🎉 Hello from wrknv! The work environment is ready to work! 🎉'"
description = "A friendly greeting from your work environment"
```

## Success Criteria

1. **Functional**: Can run simple and composite tasks
2. **Tested**: >90% code coverage with TDD-written tests
3. **Typed**: Passes mypy strict mode
4. **Documented**: Examples in README
5. **Demo**: `wrknv run hello` works and is delightful

## Future Enhancements (Not in MVP)

- Dependency execution (`depends_on` field)
- Parallel execution
- Task result caching
- Watch mode
- Interactive task selection
- Workspace-level coordination
