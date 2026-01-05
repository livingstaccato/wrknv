# Installation

Get started with wrknv, a tool that generates standardized development environment scripts for the provide.io ecosystem with tool version management, sibling package integration, and containerized development support.

## Prerequisites

--8<-- ".provide/foundry/docs/_partials/python-requirements.md"

--8<-- ".provide/foundry/docs/_partials/uv-installation.md"

--8<-- ".provide/foundry/docs/_partials/python-version-setup.md"

## Installation Methods

### As a Command-Line Tool

If you want to use wrknv to manage development environments:

**Using uv (Recommended):**
```bash
# Install wrknv globally with uv
uvx wrknv --help

# Or install in a dedicated virtual environment
uv tool install wrknv
```

### As a Library Dependency

If you're integrating wrknv into your project:

**Using uv:**
```bash
uv add wrknv
```

**In your `pyproject.toml`:**
```toml
[project]
dependencies = [
    "wrknv>=0.3.0",
]
```

### For Development

Clone the repository and set up the development environment:

```bash
# Clone the repository
git clone https://github.com/provide-io/wrknv.git
cd wrknv

# Set up development environment
uv sync

# Or install with all development dependencies
uv sync --all-groups

# Verify installation
uv run wrknv --version
```

**Important:** wrknv uses `workenv/` directory for virtual environments (not `.venv/`):

```bash
# After installation, environment scripts will reference workenv/
source ./env.sh  # Linux/macOS

# The workenv location follows pattern: workenv/wrknv_${OS}_${ARCH}
```

--8<-- ".provide/foundry/docs/_partials/virtual-env-setup.md"

!!! note "Virtual Environment Location"
    Unlike most Python projects, wrknv uses `workenv/` directory instead of `.venv/`. This is intentional for the provide.io ecosystem's standardized environment management.

--8<-- ".provide/foundry/docs/_partials/platform-specific-macos.md"

## Optional Dependencies

### Container Support

For Docker-based development environments:

```bash
# Install with container support
uv tool install wrknv[container]
```

**Container Features:**
- Docker runtime abstraction
- Container lifecycle management
- Volume management
- Build operations
- Exec commands in containers

**Requirements:**
- Docker or compatible container runtime installed
- Docker daemon running
- Appropriate user permissions for container operations

**Verify Docker:**
```bash
# Check Docker installation
docker --version
docker info

# Test container operations
docker run --rm hello-world
```

## Verifying Installation

### Basic Verification

--8<-- ".provide/foundry/docs/_partials/verification-commands.md"

!!! note "Package and Command Names"
    Replace `{{PACKAGE_NAME}}` with `wrknv` and `{{COMMAND_NAME}}` with `wrknv` in the verification commands above.

### wrknv-Specific Verification

**1. Test Core Imports:**
```python
import wrknv
from wrknv.cli import hub_cli
from wrknv.wenv.config import WorkenvConfig
from wrknv.wenv.env_generator import EnvironmentGenerator

print(f"wrknv version: {wrknv.__version__}")
print("Installation successful!")
```

**2. Test Configuration Loading:**
```python
from wrknv.wenv.config import WorkenvConfig
from wrknv.wenv.schema import load_config_from_toml
from pathlib import Path

# Create minimal test config
config_content = """
[tools.uv]
version = "0.5.11"

[tools.terraform]
version = "1.9.8"
"""

config_path = Path("test_workenv.toml")
config_path.write_text(config_content)

config = load_config_from_toml(config_path)
print(f"Loaded configuration with {len(config.tools)} tool(s)")
config_path.unlink()  # Clean up
```

**3. Test Environment Generation:**
```bash
# Generate environment scripts
wrknv generate

# Should create:
# - env.sh (Unix shell script)
# - env.ps1 (PowerShell script)

# Source the environment
source ./env.sh

# Verify tools are in PATH
echo $PATH | grep workenv
```

**4. Run Tests:**
```bash
# Run all tests with coverage
uv run pytest tests/ -v --cov=src/wrknv --cov-report=term-missing

# Run specific test categories
uv run pytest -m unit
uv run pytest -m cli
```

## Configuration Setup

### Creating a Configuration File

wrknv uses TOML configuration (`workenv.toml` by default):

```bash
# Create example configuration
cat > workenv.toml << 'EOF'
# Tool version management
[tools.uv]
version = "0.5.11"

[tools.terraform]
version = "1.9.8"

[tools.opentofu]
version = "1.8.5"

[tools.go]
version = "1.23.0"

# Sibling package patterns
[sibling_patterns]
pyvider = "../pyvider-*"
provide = "../provide-*"

# Container settings (optional)
[container]
runtime = "docker"
base_image = "python:3.11-slim"
work_dir = "/workspace"
EOF
```

**Configuration Options:**

| Section | Description |
|---------|-------------|
| `[tools.*]` | Tool version specifications (uv, terraform, opentofu, go, etc.) |
| `[sibling_patterns]` | Patterns for locating sibling packages |
| `[container]` | Container runtime configuration |

**Supported Tools:**

- **uv**: Python package manager
- **terraform**: Infrastructure as code
- **opentofu**: Open-source Terraform alternative
- **go**: Go programming language
- **python**: Python runtime version

### Environment Scripts

After generating with `wrknv generate`, source the appropriate script:

**Linux/macOS:**
```bash
# Source environment
source ./env.sh

# Or in your shell profile
echo "source $(pwd)/env.sh" >> ~/.bashrc
```

**Windows:**
```powershell
# Load environment
.\env.ps1

# Or in your PowerShell profile
Add-Content $PROFILE "& '$PWD\env.ps1'"
```

**Generated Scripts Include:**

- Tool paths and version management
- Sibling package detection and PYTHONPATH setup
- Virtual environment activation
- Container runtime configuration
- Platform-specific path handling

## Tool Managers

wrknv includes managers for common development tools:

### UV Manager

```python
from wrknv.wenv.managers.uv import UVManager

manager = UVManager()
await manager.ensure_installed(version="0.5.11")
```

### Terraform Manager

```python
from wrknv.wenv.managers.terraform import TerraformManager

manager = TerraformManager()
await manager.ensure_installed(version="1.9.8")
```

### Custom Tool Managers

Extend `ToolManager` base class for custom tools:

```python
from wrknv.wenv.managers.base import ToolManager

class CustomToolManager(ToolManager):
    async def get_download_url(self, version: str, platform: str) -> str:
        # Return download URL for tool
        pass

    async def verify_installation(self, install_path: Path) -> bool:
        # Verify tool is correctly installed
        pass
```

## Development Workflow

--8<-- ".provide/foundry/docs/_partials/testing-setup.md"

**Additional Testing Options:**
```bash
# Run unit tests only
uv run pytest -m unit

# Run CLI tests
uv run pytest -m cli

# Run specific test file
uv run pytest tests/path/to/test_file.py -xvs
```

--8<-- ".provide/foundry/docs/_partials/code-quality-setup.md"

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

### Building the Package

```bash
# Build distribution packages
uv build

# The wheel will be in dist/
ls dist/
```

## Container Development

### Setting Up Container Environment

```bash
# Install with container support
uv tool install wrknv[container]

# Configure container in workenv.toml
cat >> workenv.toml << 'EOF'
[container]
runtime = "docker"
base_image = "python:3.11-slim"
work_dir = "/workspace"
volumes = [
    "./:/workspace",
    "~/.cache:/root/.cache"
]
EOF

# Generate container configuration
wrknv container build

# Start container environment
wrknv container up
```

### Container Operations

```bash
# Build container image
wrknv container build

# Start container
wrknv container up

# Execute command in container
wrknv container exec -- pytest tests/

# Stop container
wrknv container down

# Clean up container and volumes
wrknv container clean
```

## Troubleshooting

--8<-- ".provide/foundry/docs/_partials/troubleshooting-common.md"

### wrknv-Specific Issues

#### Generated Scripts Not Working

Verify script generation:

```bash
# Check generated files
ls -la env.sh env.ps1

# Verify script syntax
bash -n env.sh  # Check for syntax errors

# Source with verbose output
bash -x env.sh  # See what the script is doing
```

#### Tools Not Found After Sourcing

Check tool installation:

```bash
# Verify tool is installed
wrknv tools list

# Check workenv directory
ls -la workenv/

# Verify PATH includes workenv
echo $PATH | grep workenv
```

#### Sibling Package Detection Failing

Verify patterns and paths:

```bash
# Check configuration
wrknv config show

# List detected siblings
wrknv sibling list

# Verify paths exist
ls ../pyvider-*
ls ../provide-*
```

#### Container Build Failures

Check Docker setup:

```bash
# Verify Docker is running
docker info

# Check image availability
docker images | grep wrknv

# View build logs
wrknv container build --verbose
```

#### Permission Errors

Fix workenv permissions:

```bash
# Make scripts executable
chmod +x env.sh

# Fix ownership
sudo chown -R $USER:$USER workenv/

# Clear and regenerate
rm -rf workenv/
wrknv generate
```

### Getting Help

If you encounter issues:

1. **Check generated scripts** - Look at `env.sh` or `env.ps1` content
2. **Verify Python version** - Ensure you're using Python 3.11+
3. **Check configuration** - Validate TOML syntax with `wrknv config show`
4. **Review logs** - Run with `--verbose` flag for detailed output
5. **Report issues** - [GitHub Issues](https://github.com/provide-io/wrknv/issues)

## Next Steps

### Quick Start

1. **[Quick Start Guide](quick-start.md)** - Generate your first environment in 5 minutes

Ready to manage your development environment? Start with the [Quick Start Guide](quick-start.md)!
