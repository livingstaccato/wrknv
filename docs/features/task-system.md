# Task System

The `we` task system provides a powerful, intuitive way to define and run development tasks. Built on provide-foundation's process management, it offers nested task organization, smart resolution, and automatic command detection.

## Overview

Tasks are defined in `wrknv.toml` and can be executed with the `we` command. The system supports:

- **Flat and nested tasks** up to 3 levels deep
- **Automatic command detection** - no need for `run` subcommand
- **Smart task resolution** with hierarchical fallback
- **Argument passthrough** with proper shell quoting
- **Environment variables** and custom working directories
- **Timeouts** per task or executor default
- **Composite tasks** that run other tasks

## Basic Usage

### Defining Tasks

Define tasks in `wrknv.toml`:

```toml
[tasks]
test = "pytest tests/"
lint = "ruff check src/"
format = "ruff format src/"
```

### Running Tasks

Simply use `we` followed by the task name:

```bash
we test                  # Run tests
we lint                  # Run linter
we format               # Format code
```

No `run` subcommand needed! The `we` command automatically detects and executes tasks.

### Listing Tasks

View all available tasks:

```bash
we tasks                 # List all tasks
we tasks --verbose       # Show detailed information
```

## Nested Tasks

Organize related tasks using namespaces up to 3 levels deep:

```toml
[tasks.test]
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"
e2e = "pytest tests/e2e/"

[tasks.test.unit]
fast = "pytest tests/unit/ -x"
coverage = "pytest tests/unit/ --cov"
```

### Running Nested Tasks

Use space-separated syntax:

```bash
we test unit             # Run unit tests
we test integration      # Run integration tests
we test unit fast        # Run fast unit tests
```

The system uses greedy matching to find the longest valid task name.

### Default Tasks

Define a default task with `_default`:

```toml
[tasks.test]
_default = "pytest tests/"
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"
```

Now `we test` runs the default:

```bash
we test                  # Runs pytest tests/
we test unit             # Runs pytest tests/unit/
```

## Task Arguments

Pass arguments directly to task commands:

```bash
we test --verbose        # Passes --verbose to pytest
we test unit -x --pdb    # Multiple arguments
we lint --fix            # Pass to ruffer
```

Arguments are properly quoted using `shlex.quote()` to handle spaces and special characters.

## Environment Variables

### In Task Definition

Set environment variables in the task:

```toml
[tasks.test]
run = "pytest tests/"
env = { PYTEST_WORKERS = "4", DEBUG = "true" }
```

### At Runtime

Override or add environment variables:

```bash
we run test --env PYTEST_WORKERS=8
we run test --env DEBUG=true --env LOG_LEVEL=debug
```

## Working Directory

Run tasks in a specific directory:

```toml
[tasks.docs]
run = "mkdocs serve"
working_dir = "docs"
description = "Serve documentation"
```

## Timeouts

Set per-task or default timeouts:

```toml
[tasks.test]
run = "pytest tests/"
timeout = 600.0  # 10 minutes

[tasks.quick]
run = "pytest tests/unit/ -x"
timeout = 30.0   # 30 seconds
```

Default timeout is 5 minutes (300 seconds).

## Composite Tasks

Run multiple tasks in sequence:

```toml
[tasks.quality]
run = ["lint", "typecheck", "format"]
description = "Run all quality checks"

[tasks.ci]
run = ["quality", "test", "build"]
description = "Complete CI pipeline"
```

Composite tasks stop on first failure.

## Smart Resolution

The task resolver uses intelligent fallback:

### Resolution Priority

Given command: `we test unit fast`

1. **Exact match**: Look for `test.unit.fast`
2. **Parent + args**: Try `test.unit` with args `["fast"]`
3. **Grandparent + args**: Try `test` with args `["unit", "fast"]`
4. **Default tasks**: Check for `_default` in each namespace

### Examples

```toml
[tasks.test]
unit = "pytest tests/unit/"

[tasks.test.unit]
fast = "pytest tests/unit/ -x"
```

Resolution:
- `we test unit fast` → finds `test.unit.fast` (exact match)
- `we test unit --verbose` → finds `test.unit` + passes `--verbose`
- `we test --verbose` → finds `test._default` or `test` + passes `--verbose`

## Task Descriptions

Add descriptions for documentation:

```toml
[tasks.test]
run = "pytest tests/"
description = "Run the full test suite"

[tasks.lint]
run = "ruff check src/"
description = "Check code quality with ruff"
```

Descriptions appear in `we tasks` output.

## Advanced Features

### Complex Task Configuration

Full task configuration example:

```toml
[tasks.deploy]
run = "bash scripts/deploy.sh"
description = "Deploy to staging"
working_dir = "deployment"
timeout = 1800.0  # 30 minutes
env = { ENV = "staging", REGION = "us-west-2" }
```

### Task Dependencies

`depends_on` is defined in the schema but not executed yet. Use composite tasks instead:

```toml
[tasks.deploy]
run = ["test", "build", "push"]
description = "Test, build, and deploy"
```

## Best Practices

### Naming Conventions

- Use **lowercase** task names
- Use **dots** for namespaces: `test.unit`, not `test:unit`
- Use **verbs** for action tasks: `test`, `build`, `deploy`
- Use **nouns** for namespaces: `test.unit`, `docs.build`

### Organization

```toml
# Flat tasks for common operations
[tasks]
lint = "ruff check ."
format = "ruff format ."

# Nested tasks for grouped operations
[tasks.test]
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"

[tasks.docs]
build = "mkdocs build"
serve = "mkdocs serve"
```

### Task Granularity

- **Small tasks** for specific operations
- **Composite tasks** for workflows
- **Namespaces** for logical grouping

### Arguments vs Nested Tasks

Use arguments for variations:
```bash
we test --verbose        # Good: variation of test
```

Use nested tasks for distinct operations:
```toml
[tasks.test]
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"  # Good: distinct operations
```

## Integration with Foundation

Tasks leverage provide-foundation's process management:

- **Command masking**: Secrets in commands are automatically masked in logs
- **Environment scrubbing**: Credentials removed from subprocess environment
- **Structured logging**: Full context with task name, duration, exit code
- **Timeout enforcement**: Hard timeout prevents runaway processes
- **Error handling**: Rich error types with helpful hints

## Examples

### Development Workflow

```toml
[tasks]
format = "ruff format src/ tests/"
lint = "ruff check src/ tests/"
typecheck = "mypy src/"

[tasks.test]
_default = "pytest tests/"
unit = "pytest tests/unit/"
watch = "pytest-watch tests/"

[tasks.quality]
run = ["format", "lint", "typecheck"]
description = "Run all quality checks"

[tasks.dev]
run = ["quality", "test"]
description = "Full development check"
```

Usage:
```bash
we format               # Format code
we test                 # Run all tests
we test unit            # Run unit tests only
we quality              # Run quality checks
we dev                  # Full dev workflow
```

### CI/CD Pipeline

```toml
[tasks.ci]
run = ["quality", "test.unit", "test.integration", "build"]
description = "Complete CI pipeline"

[tasks.deploy]
run = ["ci", "deploy.staging"]
description = "CI and deploy to staging"

[tasks.deploy.staging]
run = "bash scripts/deploy.sh staging"
timeout = 1800.0
```

### Monorepo Tasks

```toml
[tasks.test]
_default = "pytest tests/"
backend = "pytest backend/tests/"
frontend = "cd frontend && npm test"
api = "pytest api/tests/"

[tasks.build]
_default = "bash scripts/build-all.sh"
backend = "python -m build backend/"
frontend = "cd frontend && npm run build"
```

## Troubleshooting

### Task Not Found

If `we test unit` fails:

1. Check task exists: `we tasks`
2. Verify syntax in `wrknv.toml`
3. Check for typos in task name
4. Try explicit: `we run test.unit`

### Timeout Errors

Increase timeout in task definition:

```toml
[tasks.slow-test]
run = "pytest tests/integration/"
timeout = 600.0  # 10 minutes
```

### Environment Issues

Check environment variables are set:

```toml
[tasks.test]
run = "pytest tests/"
env = { DEBUG = "1", LOG_LEVEL = "debug" }
```

Or use runtime override:

```bash
we run test --env DEBUG=1
```

## See Also

- [CLI Reference](we-cli-reference.md) - Complete command documentation
- [Configuration Reference](../reference/configuration.md) - Configuration schema
- [Examples](../../examples/) - Sample projects
