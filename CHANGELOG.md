# Changelog

All notable changes to the wrknv project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of wrknv
- Environment script generation for `env.sh` and `env.ps1`
- Tool version management for UV, Terraform, OpenTofu, and Go
- Sibling package discovery and installation
- TOML-based configuration system (`wrknv.toml`)
- CLI command structure with provide-foundation hub integration
- Container-based development environments (experimental)
- Provider packaging integration with flavor (experimental)
- Cross-platform support (macOS, Linux, Windows)
- Comprehensive test suite with pytest
- Template-based script generation with Jinja2
- Platform-specific tool download and verification
- Checksum validation for downloaded tools

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- Checksum verification for all downloaded tools
- Secure template processing to prevent injection attacks
- File access restrictions for authorized paths only

## Release Notes

### v0.0.0.dev0 (Development Release)

This is the initial development release of wrknv, providing comprehensive work environment management for the provide.io ecosystem.

**Core Features:**
- **Environment Generation**: Creates standardized `env.sh` and `env.ps1` scripts from templates
- **Tool Management**: Manages versions of UV, Terraform, OpenTofu, Go, and other development tools
- **Sibling Integration**: Automatically discovers and installs local, editable dependencies
- **Configuration**: TOML-based configuration with type-safe schema validation

**CLI Commands:**
- **Core Commands**: `init`, `generate`, `status`, `setup`, `test`, `build`
- **Ecosystem Commands**: `ecosystem setup`, `ecosystem status`, `ecosystem test`, `ecosystem build`
- **Tool Commands**: Tool-specific version management and installation
- **Container Commands**: Docker-based development environment management (experimental)
- **Package Commands**: Provider packaging and distribution (experimental)

**Architecture:**
- **Hub Pattern**: Command registration via decorators to central hub
- **Manager Pattern**: Tool-specific managers inheriting from `ToolManager` base
- **Operation Pattern**: Focused modules for download, verify, and install operations
- **Schema-driven Config**: Typed configuration with `cattrs` serialization/validation

**Template System:**
- **Jinja2 Templates**: Flexible template system for script generation
- **Platform Support**: Cross-platform script generation for bash and PowerShell
- **Customization**: Configurable templates for different project needs

**Container Management:**
- **Docker Integration**: Experimental Docker-based development environments
- **Dockerfile Generation**: Dynamic Dockerfile creation from configuration
- **Lifecycle Management**: Container build, exec, and cleanup operations

**Tool Managers:**
- **UV Manager**: Python package manager installation and management
- **Terraform Manager**: Terraform version management and installation
- **OpenTofu Manager**: OpenTofu version management and installation
- **Go Manager**: Go language version management and installation

**Configuration Features:**
- **Type Safety**: Comprehensive type checking and validation
- **Sibling Patterns**: Pattern-based sibling package discovery
- **Tool Versions**: Pinned or latest version specifications
- **Environment Settings**: Python version requirements and verification options

**Development Features:**
- **Rich CLI**: Beautiful command-line interface with rich formatting
- **Comprehensive Testing**: Full test suite with pytest and coverage
- **Type Checking**: MyPy integration for static type analysis
- **Code Quality**: Ruff linting and formatting integration

**Security Features:**
- **Checksum Verification**: All downloaded tools verified with checksums
- **Template Security**: Safe template processing without injection risks
- **Access Control**: File operations restricted to authorized paths
- **Error Safety**: No sensitive information exposed in error messages

**Integration Points:**
- **provide-foundation**: Core foundation services and logging
- **UV**: Python package manager for dependency installation
- **Docker**: Container runtime for development environments
- **Jinja2**: Template engine for script generation
- **cattrs**: Configuration serialization and validation

**Dependencies:**
- `provide-foundation[all]>=0.0.0`: Foundation services
- `cattrs>=23.0.0`: Configuration attribute handling
- `packaging>=23.0`: Package version parsing
- `semver>=3.0.0`: Semantic version handling
- `tomli-w>=1.0.0`: TOML writing support
- `rich>=13.0.0`: Rich text formatting
- `jinja2>=3.0.0`: Template engine

This release establishes wrknv as the central work environment management tool for the provide.io ecosystem, enabling consistent development experiences across all projects.