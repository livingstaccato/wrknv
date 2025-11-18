# Getting Started with wrknv

Welcome to wrknv! This guide will help you get up and running quickly.

## What is wrknv?

**wrknv** (Work Environment) is a tool that generates standardized development environment scripts for Python projects. Instead of maintaining complex shell scripts in every project, wrknv generates `env.sh` and `env.ps1` files from your `pyproject.toml` configuration.

### Key Benefits

- **Standardized Environments**: Consistent setup across all projects
- **Tool Version Management**: Pin versions of UV, Terraform, OpenTofu, Go, etc.
- **Sibling Package Discovery**: Automatically find and install related packages
- **Cross-Platform**: Works on Linux, macOS, and Windows
- **Zero Duplication**: One configuration generates both Bash and PowerShell scripts

### How It Works

```
pyproject.toml (config)
    ↓
wrknv generate
    ↓
env.sh + env.ps1 (scripts)
    ↓
source env.sh
    ↓
Fully configured development environment!
```

## Choose Your Path

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quick Start**

    ---

    Get your first environment running in 5 minutes.

    [:octicons-arrow-right-24: Quick Start Guide](quick-start/)

-   :material-cog:{ .lg .middle } **Complete Installation**

    ---

    Detailed installation with all options and configurations.

    [:octicons-arrow-right-24: Installation Guide](installation/)

-   :material-lightbulb:{ .lg .middle } **Core Concepts**

    ---

    Understand wrknv's architecture and design.

    [:octicons-arrow-right-24: Learn Concepts](concepts/)

-   :material-school:{ .lg .middle } **First Project**

    ---

    Step-by-step walkthrough of setting up a complete project.

    [:octicons-arrow-right-24: Project Tutorial](#first-commands)

</div>

## Overview

wrknv solves a common problem in Python development: **environment setup scripts**. Instead of copying and maintaining 300-400 line shell scripts across projects, you configure wrknv once in `pyproject.toml` and generate fresh, tested scripts whenever needed.

### Before wrknv

```bash
# Copy 400-line env.sh from another project
# Manually update Python version
# Manually update tool versions
# Hope it works on all platforms
# Duplicate across 10+ projects
```

### After wrknv

```toml
# pyproject.toml
[tool.wrknv.tools]
uv = "0.5.1"
terraform = "1.9.0"
```

```bash
$ wrknv generate
$ source env.sh
# ✓ Done!
```

## Who Should Use wrknv?

wrknv is designed for:

- **Python developers** managing multiple projects
- **DevOps teams** standardizing development environments
- **Monorepo maintainers** with sibling package dependencies
- **Teams using Terraform** alongside Python
- **Anyone tired of maintaining** shell scripts

## Common Use Cases

### 1. Python Package Development

Standard Python project with UV for dependency management:

```toml
[project]
name = "my-package"
requires-python = ">=3.11"

[tool.wrknv.tools]
uv = "0.5.1"
```

### 2. Terraform Provider Development

Python Terraform provider using pyvider:

```toml
[tool.wrknv.tools]
uv = "0.5.1"
terraform = "1.9.0"
go = "1.22.0"  # For testing against Go providers

[tool.wrknv.siblings]
discover_patterns = ["../pyvider*/pyproject.toml"]
```

### 3. Monorepo with Shared Dependencies

Multiple projects sharing common libraries:

```toml
[tool.wrknv.siblings]
discover_patterns = [
    "../provide-foundation/pyproject.toml",
    "../provide-testkit/pyproject.toml"
]
install_as_editable = true
```

### 4. Containerized Development

Development inside Docker containers:

```toml
[tool.wrknv.container]
runtime = "docker"
base_image = "python:3.11-slim"
```

## What wrknv Manages

### Tools

- **UV**: Fast Python package manager
- **Terraform**: Infrastructure as code
- **OpenTofu**: Open source Terraform fork
- **Go**: Go language toolchain
- Custom tools via extensible manager system

### Python Environment

- Virtual environment creation (`workenv/` not `.venv/`)
- Dependency installation via UV
- Python version validation
- Platform-specific handling

### Sibling Packages

- Auto-discovery of related projects
- Editable installation for development
- Dependency graph awareness
- Monorepo support

### Configuration

- TOML-based configuration
- Profile support for different environments
- Lockfile for reproducible builds
- Secret management integration

## Installation Methods

### From PyPI (Recommended)

```console
$ pip install wrknv
```

### Using UV

```console
$ uv pip install wrknv
```

### From Source

```console
$ git clone https://github.com/provide-io/wrknv.git
$ cd wrknv
$ uv sync
$ uv pip install -e .
```

## First Commands

After installation, try these commands:

```console
# Check version
$ wrknv --version

# Get help
$ wrknv --help

# Generate environment scripts
$ wrknv generate

# Check environment health
$ wrknv doctor

# View configuration
$ wrknv config show
```

## Learning Path

### 1. Basics (30 minutes)

- [Quick Start Guide](quick-start/) - 5-minute tutorial
- [Core Concepts](concepts/) - Understanding wrknv
- [Installation Guide](installation/) - Complete setup

## System Requirements

- **Python**: 3.11 or higher
- **OS**: Linux, macOS, or Windows
- **Disk Space**: ~100MB for cached tools
- **Internet**: Required for downloading tools

## Getting Help

- **[GitHub Issues](https://github.com/provide-io/wrknv/issues)** - Bug reports and feature requests
- **[API Reference](../reference/)** - Python API documentation

## Next Steps

Ready to get started?

1. **[Quick Start Guide](quick-start/)** - Get running in 5 minutes
2. **[Installation Guide](installation/)** - Detailed setup
3. **[Core Concepts](concepts/)** - Understand how wrknv works
