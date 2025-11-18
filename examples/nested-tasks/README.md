# Nested Tasks Example

This example demonstrates hierarchical task organization with nested namespaces (up to 3 levels deep).

## Task Organization

### Flat Tasks (Top Level)
- `lint`, `format`, `typecheck` - Code quality tools
- `quality` - Composite quality workflow
- `ci` - Complete CI pipeline

### Test Namespace (2 levels)
```
test/
├── _default      → pytest tests/
├── unit          → pytest tests/unit/
├── integration   → pytest tests/integration/
└── e2e           → pytest tests/e2e/
```

### Test.Unit Namespace (3 levels)
```
test.unit/
├── fast          → pytest tests/unit/ -x
├── watch         → pytest-watch tests/unit/
└── coverage      → pytest with coverage report
```

### Docs Namespace
```
docs/
├── _default      → mkdocs serve
├── build         → mkdocs build
└── deploy        → mkdocs gh-deploy
```

### Build Namespace
```
build/
├── _default      → python -m build
├── wheel         → build wheel only
├── sdist         → build source dist
└── docker        → docker build
```

### Deploy Namespace
```
deploy/
├── staging       → deploy to staging
└── production    → deploy to production
```

## Usage

### Run Default Tasks

When a namespace has `_default`, you can run it directly:

```bash
we test                  # Runs test._default (pytest tests/)
we docs                  # Runs docs._default (mkdocs serve)
we build                 # Runs build._default (python -m build)
```

### Run Specific Nested Tasks

Use space-separated syntax:

```bash
# 2-level tasks
we test unit             # Run unit tests
we test integration      # Run integration tests
we docs build            # Build documentation

# 3-level tasks
we test unit fast        # Fast unit tests
we test unit coverage    # Unit tests with coverage
```

### Pass Arguments

Arguments work with any task:

```bash
we test --verbose        # Pass to default test task
we test unit --pdb       # Pass to unit tests
we lint --fix            # Pass to lint
```

### Hierarchical Display

View the task hierarchy:

```bash
we tasks

# Output:
# Available tasks:
#
# build
# ├── _default (default)
# ├── docker
# ├── sdist
# └── wheel
#
# deploy
# ├── production
# └── staging
#
# docs
# ├── _default (default)
# ├── build
# └── deploy
#
# test
# ├── _default (default)
# ├── e2e
# ├── integration
# └── unit
#
# test.unit
# ├── coverage  Unit tests with coverage report
# ├── fast
# └── watch
#
# Flat tasks:
#   • ci  Complete CI pipeline
#   • format
#   • lint
#   • quality  Run all quality checks
#   • typecheck
```

## Smart Resolution

The task resolver uses intelligent fallback:

```bash
# Example: we test unit debug

# Resolution attempts:
# 1. Exact match: test.unit.debug
# 2. Parent + args: test.unit with ["debug"]
# 3. Grandparent + args: test with ["unit", "debug"]
# 4. Default tasks: test._default with ["unit", "debug"]
```

This means if `test.unit` accepts a `debug` flag, it will receive it!

## Best Practices

### When to Use Nesting

**Good use cases:**
- Related operations: `test.unit`, `test.integration`
- Different targets: `build.docker`, `build.wheel`
- Environment variations: `deploy.staging`, `deploy.production`

**Avoid nesting for:**
- Unrelated operations
- Simple projects with few tasks
- Tasks that are run independently

### Naming Conventions

- **Namespaces**: Use nouns (`test`, `docs`, `build`, `deploy`)
- **Tasks**: Use verbs or descriptive nouns (`unit`, `fast`, `coverage`)
- **Defaults**: Use `_default` for the most common operation in a namespace

### Maximum Depth

Tasks support up to 3 levels:
```
level1.level2.level3     ✅ Supported
level1.level2.level3.level4     ❌ Too deep
```

Use composite tasks or arguments instead of excessive nesting.

## Composite Workflows

Combine multiple tasks:

```bash
we quality               # Runs: lint → typecheck → format
we ci                    # Runs: quality → test.unit → test.integration → build
```

Define in `wrknv.toml`:

```toml
[tasks.quality]
run = ["lint", "typecheck", "format"]
description = "Run all quality checks"

[tasks.ci]
run = ["quality", "test.unit", "test.integration", "build"]
description = "Complete CI pipeline"
```

## Environment-Specific Configuration

Tasks can have environment settings:

```toml
[tasks.deploy.staging]
run = "bash scripts/deploy.sh staging"
description = "Deploy to staging environment"
timeout = 1800.0
env = { ENV = "staging", REGION = "us-west-2" }
```

Run with:

```bash
we deploy staging        # Uses ENV=staging, REGION=us-west-2
```

## See Also

- [Task System Documentation](../../docs/features/task-system.md)
- [Simple Tasks Example](../simple-tasks/) - Flat task organization
- [wrknv.toml Reference](../../docs/reference/wrknv-toml.md)
