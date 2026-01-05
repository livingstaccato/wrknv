# Configuration Reference

Complete reference for the `wrknv.toml` configuration file.

## Overview

The `wrknv.toml` file configures your work environment, including:

- **Project metadata** - Name, version
- **Tool versions** - Terraform, OpenTofu, Go, UV, etc.
- **Environment variables** - Project-specific settings
- **Tasks** - Development and CI/CD tasks
- **Profiles** - Different tool configurations for different environments
- **Workenv settings** - Behavior configuration

## File Location

Place `wrknv.toml` in your project root:

```
myproject/
├── wrknv.toml          ← Configuration file
├── src/
├── tests/
└── README.md
```

## Basic Structure

```toml
# Project metadata
project_name = "myproject"
version = "1.0.0"

# Tool versions
[tools]
terraform = ["1.6.x"]
go = ["1.21.x"]

# Environment variables
[env]
DEBUG = "false"

# Tasks
[tasks]
test = "pytest tests/"
lint = "ruff check src/"

# Workenv settings
[workenv]
auto_install = true
```

## Sections

### Project Metadata

```toml
project_name = "myproject"
version = "1.0.0"
```

**Fields:**
- `project_name` (string, required) - Project identifier
- `version` (string, optional) - Project version

### Tools

Define tool versions to install and manage:

```toml
[tools]
terraform = ["1.6.x", "1.5.x"]
tofu = ["1.9.x"]
go = ["1.21.x"]
uv = ["0.1.x"]

[tools.node]
version = "20.x"
```

**Supported Tools:**
- `terraform` - Terraform versions
- `tofu` - OpenTofu versions
- `go` - Go versions
- `uv` - UV Python package manager
- `node` - Node.js (via tool-specific config)
- `bao` - HashiCorp Bao

**Version Syntax:**
- Exact: `"1.6.0"`
- Patch wildcard: `"1.6.x"` (latest 1.6.*)
- Multiple versions: `["1.6.x", "1.5.x"]`

**Tool-Specific Config:**

```toml
[tools.bao]
version = "2.1.0"
url = "https://custom-mirror.com/bao"
checksum = "sha256:..."
```

### Environment Variables

Define project-specific environment variables:

```toml
[env]
DEBUG = "false"
LOG_LEVEL = "info"
API_URL = "https://api.example.com"
DATABASE_URL = "postgresql://localhost/mydb"
```

**Usage:**
- Variables set in generated `env.sh` and `env.ps1`
- Available to all tasks
- Can be overridden at runtime

### Tasks

Define development tasks. See [Task System](../features/task-system.md) for full details.

#### Flat Tasks

Simple command tasks:

```toml
[tasks]
test = "pytest tests/"
lint = "ruff check src/"
format = "ruff format src/"
build = "python -m build"
```

#### Complex Tasks

Tasks with full configuration:

```toml
[tasks.test]
run = "pytest tests/"
description = "Run the full test suite"
timeout = 300.0
env = { PYTEST_WORKERS = "4" }
working_dir = "tests"
```

**Task Fields:**
- `run` (string or array, required) - Command to execute or list of tasks
- `description` (string, optional) - Task description
- `timeout` (float, optional) - Timeout in seconds (default: 300)
- `env` (object, optional) - Task-specific environment variables
- `working_dir` (string, optional) - Working directory
- `depends_on` (array, optional) - Task dependencies (not implemented yet)
- `stream_output` (bool, optional) - Stream output in real-time (default: false)
- `process_title_format` (string, optional) - Process title format: "full", "leaf", "abbreviated" (default: "full")
- `command_prefix` (string, optional) - Override command prefix (e.g., "uv run", "docker run myimage", or "" for none)
- `execution_mode` (string, optional) - Execution mode: "auto", "uv_run", "direct", "system" (default: "auto")

#### Nested Tasks

Organize tasks hierarchically (up to 3 levels):

```toml
[tasks.test]
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"

[tasks.test.unit]
fast = "pytest tests/unit/ -x"
coverage = "pytest tests/unit/ --cov"
```

#### Default Tasks

Use `_default` for namespace defaults:

```toml
[tasks.test]
_default = "pytest tests/"
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"
```

Now `we test` runs the default task.

#### Composite Tasks

Run multiple tasks in sequence:

```toml
[tasks.quality]
run = ["lint", "typecheck", "format"]
description = "Run all quality checks"

[tasks.ci]
run = ["quality", "test", "build"]
description = "Complete CI pipeline"
```

#### Environment Auto-Detection

wrknv automatically detects the optimal execution strategy (no need to prefix commands with `uv run`!):

**Basic Example** (auto-detection):
```toml
[tasks]
test = "pytest tests/"  # No "uv run" prefix needed!
lint = "ruff check src/"
```

**Advanced Configuration**:
```toml
# Force specific execution mode
[tasks.build]
run = "python -m build"
execution_mode = "uv_run"  # Override auto-detection

# Custom prefix
[tasks.docker-test]
run = "pytest tests/"
command_prefix = "docker run myimage"

# Disable prefix explicitly
[tasks.system-python]
run = "python --version"
command_prefix = ""  # Empty string = no prefix
```

**Detection Priority**:
1. `WRKNV_TASK_RUNNER` environment variable (highest)
2. Editable install detection (preserves `uv pip install -e .`)
3. UV project detection (`uv.lock` or `[tool.uv]`)
4. Virtual environment detection (`.venv/`, `venv/`, `workenv/`)
5. System Python (lowest)

**Why This Matters**: `uv run` can uninstall editable installs (UV issue #3843). wrknv auto-detects editable installs and uses direct execution to preserve them.

### Profiles

Define tool profiles for different environments:

```toml
[profiles.dev]
terraform = ["1.6.x", "1.5.x"]
go = ["1.21.x"]
node = "20.x"

[profiles.production]
terraform = ["1.6.0"]  # Exact version for prod
go = ["1.21.5"]
```

**Usage:**
```bash
we setup --profile dev
we setup --profile production
```

### Workenv Settings

Configure wrknv behavior:

```toml
[workenv]
auto_install = true
use_cache = true
cache_ttl = "7d"
log_level = "INFO"
container_runtime = "docker"
container_registry = "ghcr.io"
```

**Fields:**
- `auto_install` (bool, default: true) - Auto-install missing tools
- `use_cache` (bool, default: true) - Cache downloaded tools
- `cache_ttl` (string, default: "7d") - Cache time-to-live
- `log_level` (string, default: "INFO") - Logging level (DEBUG, INFO, WARNING, ERROR)
- `container_runtime` (string, default: "docker") - Container runtime (docker, podman)
- `container_registry` (string) - Custom container registry

### Sibling Packages

Configure discovery of sibling packages:

```toml
[siblings]
patterns = ["../*", "~/projects/*"]
exclude = ["**/node_modules", "**/.venv"]
```

**Fields:**
- `patterns` (array) - Glob patterns to search for sibling projects
- `exclude` (array) - Patterns to exclude from discovery

### Container Settings

Configure containerized development environment:

```toml
[container]
image = "python:3.11"
dockerfile = "Dockerfile.dev"
volumes = [
    "./src:/app/src",
    "./tests:/app/tests"
]
ports = ["8000:8000", "5432:5432"]
environment = { DEBUG = "true" }
```

**Fields:**
- `image` (string) - Base container image
- `dockerfile` (string) - Custom Dockerfile path
- `volumes` (array) - Volume mounts (host:container format)
- `ports` (array) - Port mappings (host:container format)
- `environment` (object) - Container environment variables

## Complete Example

```toml
# Project metadata
project_name = "myproject"
version = "1.0.0"

# Tool versions
[tools]
terraform = ["1.6.x", "1.5.x"]
tofu = ["1.9.x"]
go = ["1.21.x"]
uv = ["0.1.x"]

[tools.node]
version = "20.x"

# Profiles
[profiles.dev]
terraform = ["1.6.x"]
go = ["1.21.x"]

[profiles.production]
terraform = ["1.6.0"]
go = ["1.21.5"]

# Environment variables
[env]
DEBUG = "false"
LOG_LEVEL = "info"
API_URL = "https://api.example.com"

# Workenv settings
[workenv]
auto_install = true
use_cache = true
cache_ttl = "7d"
log_level = "INFO"

# Tasks
[tasks]
# Flat tasks
lint = "ruff check src/ tests/"
format = "ruff format src/ tests/"
typecheck = "mypy src/"

# Nested test tasks
[tasks.test]
_default = "pytest tests/"
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"
e2e = "pytest tests/e2e/"

[tasks.test.unit]
fast = "pytest tests/unit/ -x"
coverage = "pytest tests/unit/ --cov=src"

# Documentation tasks
[tasks.docs]
build = "mkdocs build"
serve = "mkdocs serve"

# Complex task with full config
[tasks.deploy]
run = "bash scripts/deploy.sh"
description = "Deploy to staging"
timeout = 1800.0
working_dir = "deployment"
env = { ENV = "staging", REGION = "us-west-2" }

# Composite tasks
[tasks.quality]
run = ["lint", "typecheck", "format"]
description = "Run all quality checks"

[tasks.ci]
run = ["quality", "test", "build"]
description = "Complete CI pipeline"

# Container settings
[container]
image = "python:3.11-slim"
volumes = ["./src:/app/src", "./tests:/app/tests"]
ports = ["8000:8000"]
environment = { DEBUG = "true" }
```

## Validation

Validate your configuration:

```bash
we config validate
```

Common validation errors:
- **Invalid TOML syntax** - Check brackets, quotes, commas
- **Unknown fields** - Check spelling and section names
- **Invalid version syntax** - Use "1.6.x" not "1.6.*"
- **Nested too deep** - Tasks max 3 levels

## Schema Reference

### Task Schema

```toml
[tasks.TASK_NAME]
run = "command"                    # Required: string or array
description = "Description"        # Optional: string
timeout = 300.0                    # Optional: float (seconds)
working_dir = "path"               # Optional: string (path)
env = { KEY = "value" }            # Optional: object
depends_on = ["task1", "task2"]    # Optional: array (not implemented)
stream_output = false              # Optional: bool
```

### Tool Schema

```toml
[tools]
TOOL_NAME = ["version1", "version2"]  # Array of versions

[tools.TOOL_NAME]
version = "1.0.0"                     # Specific version
url = "https://..."                   # Custom download URL
checksum = "sha256:..."               # Checksum verification
```

### Profile Schema

```toml
[profiles.PROFILE_NAME]
TOOL_NAME = ["version"]               # Tool versions for this profile
```

## Best Practices

### Version Pinning

**Development:**
```toml
[profiles.dev]
terraform = ["1.6.x"]  # Allow patch updates
go = ["1.21.x"]
```

**Production:**
```toml
[profiles.production]
terraform = ["1.6.0"]  # Exact versions
go = ["1.21.5"]
```

### Task Organization

**Small, focused tasks:**
```toml
[tasks]
lint = "ruff check ."
format = "ruff format ."
typecheck = "mypy src/"
```

**Composite workflows:**
```toml
[tasks.quality]
run = ["lint", "typecheck", "format"]
```

**Logical namespaces:**
```toml
[tasks.test]
unit = "..."
integration = "..."

[tasks.docs]
build = "..."
serve = "..."
```

### Environment Variables

**Project defaults:**
```toml
[env]
DEBUG = "false"
LOG_LEVEL = "info"
```

**Profile-specific:**
```toml
[profiles.dev.env]
DEBUG = "true"
LOG_LEVEL = "debug"
```

**Task-specific:**
```toml
[tasks.test]
env = { PYTEST_WORKERS = "4" }
```

## Migration from Other Tools

### From Make

```makefile
# Makefile
test:
    pytest tests/

.PHONY: test
```

Becomes:

```toml
[tasks]
test = "pytest tests/"
```

### From npm scripts

```json
{
  "scripts": {
    "test": "pytest tests/",
    "lint": "ruff check ."
  }
}
```

Becomes:

```toml
[tasks]
test = "pytest tests/"
lint = "ruff check ."
```

### From just

```just
# justfile
test:
    pytest tests/

lint:
    ruff check .
```

Becomes:

```toml
[tasks]
test = "pytest tests/"
lint = "ruff check ."
```

## See Also

- [Task System](../features/task-system.md) - Task execution details
- [CLI Reference](../features/we-cli-reference.md) - Command documentation
- [Examples](../../examples/) - Sample configurations
