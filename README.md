# 🧰🌍 Wrknv

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package_manager-FF6B35.svg)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/provide-io/wrknv/actions/workflows/ci.yml/badge.svg)](https://github.com/provide-io/wrknv/actions)

**Work Environment** - The foundation for the provide.io ecosystem, generating standardized development environments across all projects.

## ✨ Key Features

- 🚀 **Task Runner (`we`)** - Intuitive task execution with automatic command detection, nested task organization, and smart resolution
- 📜 **Environment Script Generation** - Creates standardized `env.sh` and `env.ps1` scripts from templates
- 🔧 **Tool Version Management** - Pin versions of Terraform, OpenTofu, Go, and `uv`
- 🔗 **Sibling Package Integration** - Automatically discover and install local, editable dependencies
- 🐍 **Python Version Safety** - Detects `pyproject.toml` Python requirements and manages virtual environments
- 🐳 **Containerized Development** - (Experimental) Manage Docker-based development environments
- 📦 **Provider Packaging** - (Experimental) Interface for building `flavor`-based provider packages

## Quick Start

> **Note**: wrknv is in pre-release (v0.x.x). APIs and features may change before 1.0 release.

- Jump to [Quick Start: Task Runner](#quick-start-task-runner) or [Quick Start: Environment Management](#quick-start-environment-management).
- Full documentation is in [docs/index.md](https://github.com/provide-io/wrknv/blob/main/docs/index.md).

## Documentation
- [Documentation index](https://github.com/provide-io/wrknv/blob/main/docs/index.md)
- [Configuration reference](https://github.com/provide-io/wrknv/blob/main/docs/reference/configuration.md)
- [Examples](https://github.com/provide-io/wrknv/tree/main/examples)

## Development

### Quick Start

```bash
# Set up environment
uv sync

# Run common tasks
we test           # Run tests
we lint           # Check code
we format         # Format code
we tasks          # See all available commands
```

See [CLAUDE.md](https://github.com/provide-io/wrknv/blob/main/CLAUDE.md) for detailed development instructions and architecture information.

## Contributing
See [CONTRIBUTING.md](https://github.com/provide-io/wrknv/blob/main/CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - See LICENSE file for details.

## Requirements

- **Python 3.11 or later** - wrknv uses modern Python features including native type hints with pipe operators (`str | None`), native TOML support via `tomllib`, and other Python 3.11+ improvements.
- Git (for version control operations)
- curl or wget (for downloading tools)

## Overview

`wrknv` is THE central tool that generates all `env.sh` and `env.ps1` scripts for the provide.io ecosystem. Instead of maintaining hundreds of lines of duplicated shell scripts, each project uses wrknv to generate consistent, maintainable environment setup scripts.

## Quick Start: Task Runner

The `we` command provides an intuitive way to run development tasks:

```bash
# Install wrknv
uv tool install wrknv

# Define tasks in wrknv.toml
cat > wrknv.toml << EOF
[tasks]
test = "pytest tests/"
lint = "ruff check src/"

[tasks.test]
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"
EOF

# Run tasks directly - no 'run' subcommand needed!
we test                  # Run all tests
we test unit             # Run unit tests
we lint --fix            # Run lint with --fix flag
we tasks                 # List all available tasks
```

**Key Features:**
- ✅ **Auto-detection** - Just `we test`, not `we run test`
- ✅ **Nested tasks** - Organize with namespaces like `test.unit`, `docs.build`
- ✅ **Smart resolution** - Hierarchical fallback finds the right task
- ✅ **Arguments** - Pass flags directly: `we test --verbose`
- ✅ **Hierarchical display** - Beautiful tree view of tasks

See [Task System Documentation](https://github.com/provide-io/wrknv/blob/main/docs/features/task-system.md) for full details.

## Quick Start: Environment Management

1.  **Install wrknv**:
    ```bash
    uv tool install wrknv
    ```

2.  **Create a `wrknv.toml` file**:

    ```toml
    # wrknv.toml
    
    [project]
    name = "my-project"
    
    [tools]
    uv = "latest"
    tofu = "1.7.0"
    go = "1.22.1"
    
    [siblings]
    patterns = ["pyvider-*", "tofusoup", "garnish"]
    ```

3.  **Generate Environment Scripts**:
    ```bash
    wrknv generate
    ```
    This creates `env.sh` and `env.ps1` in your project root.

4.  **Activate Your Environment**:
    ```bash
    uv sync
    ```
    Your shell is now configured with the specified tool versions and all Python dependencies installed in `./workenv/`.

## Core Commands

-   `wrknv init`: Initialize a new wrknv.toml interactively
-   `wrknv generate`: Generate env.sh and env.ps1 scripts
-   `wrknv status`: Show the status and versions of all managed tools
-   `wrknv setup`: Complete setup (init + generate + activate instructions)
-   `wrknv test`: Run project tests
-   `wrknv build`: Build project artifacts

## Ecosystem Commands

-   `wrknv ecosystem setup`: Set up all provide.io projects
-   `wrknv ecosystem status`: Check health of all projects
-   `wrknv ecosystem test`: Run tests for all projects
-   `wrknv ecosystem build`: Build all project artifacts

## Project Configuration

Each project needs a simple `wrknv.toml`:

```toml
[project]
name = "flavorpack"
description = "Cross-language packaging system"

[tools]
uv = "latest"
go = "1.22.1"
rust = "1.75"

[siblings]
patterns = [
    "pyvider-*",      # All pyvider packages
    "tofusoup",       # Testing suite
    "plating",        # Documentation generator
]

[settings]
python_version = ">=3.11"
verify_checksums = true
```

## Generated Files

wrknv generates:
- `env.sh` - Bash environment setup script
- `env.ps1` - PowerShell environment setup script  
- `Makefile` - Standard development commands (optional)
- `.vscode/` - VS Code settings and launch configs (optional)

## Why wrknv?

Before wrknv, every project had 300-400 lines of hand-written, duplicated `env.sh` scripts. This led to:
- Inconsistent setup experiences
- Maintenance burden
- Copy-paste errors
- Drift between projects

With wrknv:
- Single source of truth for environment setup
- Consistent experience across all projects
- Easy updates - change template once, regenerate everywhere
- Zero duplication

Copyright (c) provide.io LLC.
