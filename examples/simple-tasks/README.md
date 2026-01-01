# Simple Tasks Example

This example demonstrates basic flat task definitions in `wrknv.toml`.

## Tasks Defined

- `test` - Run tests with pytest
- `lint` - Check code quality
- `format` - Format code
- `typecheck` - Type check with mypy
- `build` - Build distribution
- `docs` - Serve documentation
- `quality` - Run lint + typecheck (composite)
- `ci` - Run quality + test + build (composite)

## Usage

```bash
# Run individual tasks
we test
we lint
we format

# Run composite workflows
we quality          # Runs lint + typecheck
we ci               # Runs quality + test + build

# Pass arguments
we test --verbose
we lint --fix
```

## Task Organization

All tasks are at the top level (flat structure). This is ideal for:
- Small projects
- Simple workflows
- Quick prototyping

For more complex organization, see the [nested-tasks example](../nested-tasks/).

## List Tasks

View all available tasks:

```bash
we tasks

# Output:
# Available tasks:
#
# Flat tasks:
#   • build
#   • ci  Complete CI pipeline
#   • docs
#   • format
#   • lint
#   • quality  Run all quality checks
#   • test
#   • typecheck
```

## Modify Tasks

Edit `wrknv.toml` to add new tasks:

```toml
[tasks]
deploy = "bash scripts/deploy.sh"
clean = "rm -rf dist/ build/"
```

Then run:

```bash
we deploy
we clean
```

## See Also

- [Task System Documentation](../../docs/features/task-system.md)
- [Nested Tasks Example](../nested-tasks/)
- [Configuration Reference](../../docs/reference/configuration.md)
