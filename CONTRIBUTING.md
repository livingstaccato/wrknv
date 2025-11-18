# Contributing to wrknv

Thank you for your interest in contributing to wrknv! This tool is the foundation for development environment management across the provide.io ecosystem, so your contributions help improve the development experience for all projects.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Docker (for container management features)

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/provide-io/wrknv.git
cd wrknv

# Set up development environment (uses workenv/ not .venv/)
uv sync

# Verify setup
pytest tests/
```

### Alternative Setup (Ecosystem Development)
If you're working on the entire ecosystem:
```bash
# From the provide-io root directory
cd /path/to/provide-io
uv sync --extra all --extra dev
source .venv/bin/activate
```

## Project Structure

```
wrknv/
├── src/wrknv/                    # Main package
│   ├── __init__.py               # Package initialization
│   ├── cli/                      # CLI commands and hub
│   │   ├── hub_cli.py           # Main CLI entry point
│   │   └── commands/            # Individual command modules
│   ├── wenv/                     # Work environment management
│   │   ├── config.py            # Configuration handling
│   │   ├── env_generator.py     # Script generation
│   │   └── managers/            # Tool managers
│   ├── container/                # Container management
│   ├── operations/               # Core operations (download, install)
│   └── testing/                  # Testing utilities
├── templates/                    # Jinja2 templates
│   └── env/                     # Environment script templates
├── tests/                        # Test suite
├── docs/                         # Documentation
├── README.md                     # Project overview
├── CHANGELOG.md                  # Version history
├── CONTRIBUTING.md               # This file
└── pyproject.toml               # Package configuration
```

## Architecture Philosophy

### Core Design Principles

1. **Hub Pattern**: Commands are registered via decorators to a central hub, avoiding monolithic CLI files
2. **Manager Pattern**: Each tool (UV, Terraform, etc.) has its own manager class inheriting from `ToolManager`
3. **Operation Pattern**: Complex operations (download, verify, install) are separated into focused modules
4. **Schema-driven Config**: All configuration uses typed schemas via `cattrs` for validation
5. **Template-based Generation**: Use Jinja2 templates for all script generation

### Key Concepts

- **Work Environment**: The `workenv/` directory pattern used throughout the ecosystem
- **Sibling Packages**: Local, editable dependencies discovered via patterns
- **Tool Managers**: Abstraction for managing different development tools
- **Container Environments**: Docker-based development environments
- **Template System**: Flexible script generation from Jinja2 templates

## Contribution Guidelines

### Adding New Tool Managers

1. **Create a manager class**: Inherit from `BaseToolManager` in `src/wrknv/wenv/managers/`
2. **Implement required methods**: `get_download_url()`, `get_executable_name()`, etc.
3. **Add platform support**: Handle different operating systems and architectures
4. **Include tests**: Comprehensive test coverage for all manager functionality
5. **Update configuration**: Add tool to configuration schema

Example tool manager:

```python
from wrknv.wenv.managers.base import BaseToolManager
from wrknv.wenv.managers.types import ToolInfo

class NewToolManager(BaseToolManager):
    """Manager for NewTool installation and management."""

    def get_download_url(self, version: str, platform: str, arch: str) -> str:
        """Get download URL for specified version and platform."""
        return f"https://releases.newtool.com/v{version}/newtool_{platform}_{arch}.zip"

    def get_executable_name(self, platform: str) -> str:
        """Get executable name for the platform."""
        return "newtool.exe" if platform == "windows" else "newtool"

    def get_tool_info(self, version: str) -> ToolInfo:
        """Get tool information for specified version."""
        return ToolInfo(
            name="newtool",
            version=version,
            description="Description of NewTool"
        )
```

### Adding New CLI Commands

1. **Create command module**: Add new file in `src/wrknv/cli/commands/`
2. **Use hub registration**: Register commands with the hub using decorators
3. **Follow naming conventions**: Use descriptive command names and help text
4. **Include error handling**: Comprehensive error handling with user-friendly messages
5. **Add tests**: Test all command functionality and error cases

Example command:

```python
from provide.foundation.hub import hub

@hub.command()
def new_command():
    """Description of the new command."""
    # Command implementation
    pass
```

### Extending Templates

1. **Template location**: Add templates to `templates/env/`
2. **Jinja2 syntax**: Use Jinja2 template syntax for dynamic content
3. **Platform support**: Consider cross-platform compatibility
4. **Variable context**: Document required template variables
5. **Test generation**: Ensure generated scripts work correctly

### Configuration Schema

1. **Schema definition**: Update configuration schema in `src/wrknv/wenv/schema.py`
2. **Type safety**: Use comprehensive type annotations
3. **Validation**: Include validation rules for configuration values
4. **Documentation**: Document configuration options clearly
5. **Backward compatibility**: Consider migration paths for configuration changes

## Testing Requirements

### Test Categories

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test interaction between components
- **CLI tests**: Test command-line interface functionality
- **Manager tests**: Test tool manager implementations
- **Container tests**: Test container management features
- **Operations tests**: Test download, install, and verify operations

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/wrknv --cov-report=term-missing

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m cli               # CLI tests only

# Run tests in parallel
pytest tests/ -n auto

# Run specific test file
pytest tests/test_managers.py -xvs
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/ --ignore-missing-imports

# Security scanning
bandit -r src/
```

## Development Workflow

### Making Changes

1. **Create feature branch**:
   ```bash
   git checkout -b feature/add-new-tool-manager
   ```

2. **Implement changes**:
   ```bash
   # Add new tool manager
   vim src/wrknv/wenv/managers/newtool.py

   # Add tests
   vim tests/test_newtool_manager.py

   # Update configuration
   vim src/wrknv/wenv/schema.py
   ```

3. **Test changes**:
   ```bash
   pytest tests/test_newtool_manager.py -v
   pytest tests/ # Run all tests
   ruff check src/ tests/
   mypy src/
   ```

4. **Update documentation**:
   ```bash
   # Update README if needed
   vim README.md

   # Add changelog entry
   vim CHANGELOG.md
   ```

5. **Submit pull request**:
   ```bash
   git add .
   git commit -m "feat: add NewTool manager support"
   git push origin feature/add-new-tool-manager
   ```

### Review Process

1. **Automated checks**: CI will run tests, linting, and type checking
2. **Code review**: Maintainers will review for:
   - Code quality and adherence to patterns
   - Test coverage and quality
   - Documentation completeness
   - Platform compatibility
   - Performance impact
3. **Testing**: Changes will be tested across different platforms
4. **Integration**: Once approved, changes will be merged and released

## Issue Reporting

### Bug Reports
When reporting bugs, include:
- **Environment**: OS, Python version, wrknv version
- **Configuration**: Relevant `wrknv.toml` configuration
- **Command**: Exact command that triggered the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Any relevant error messages or stack traces

### Feature Requests
When requesting features, include:
- **Use case**: Why is this feature needed?
- **Proposed implementation**: How should it work?
- **Configuration**: What configuration options are needed?
- **Examples**: How would it be used?

## Release Process

1. **Version bumping**: Follow semantic versioning
2. **Changelog**: Update CHANGELOG.md with all changes
3. **Testing**: Run full test suite across platforms
4. **Documentation**: Update README and docs as needed
5. **Release**: Create GitHub release with notes

## Development Guidelines

- **Modern Python**: Use Python 3.11+ features (native type hints, `tomllib`, etc.)
- **No inline defaults**: All defaults must come from configuration files or constants
- **Type safety**: Comprehensive type annotations throughout
- **Error handling**: User-friendly error messages with actionable guidance
- **Cross-platform**: Ensure functionality works on macOS, Linux, and Windows
- **Performance**: Minimize startup time and resource usage
- **Testing**: High test coverage, especially for critical infrastructure

## Questions?

- **Documentation**: Check the docs directory and existing code
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Design docs**: Review `docs/DESIGN_AND_STRATEGY.md` for architectural guidance

Thank you for contributing to wrknv! Your work helps provide consistent, reliable development environments for the entire provide.io ecosystem. 🧰🌍