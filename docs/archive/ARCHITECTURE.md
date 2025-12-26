# wrknv Architecture

## Overview

`wrknv` manages development environments with clear separation of concerns across multiple layers.

## Module Organization

### Core Configuration (`wrknv/config/`)

**Purpose**: Runtime configuration management

**Key Files**:
- `core.py` - `WorkenvConfig` class (THE single source of truth)
- `persistence.py` - Load/save TOML configuration
- `validation.py` - Configuration validation
- `display.py` - Configuration display logic

**Responsibilities**:
- Load configuration from `.wrknv.toml` and environment variables
- Manage tool versions, profiles, and settings
- Validate configuration data
- Persist configuration changes

### Environment Generation (`wrknv/wenv/`)

**Purpose**: Core environment script generation

**Key Files**:
- `env_generator.py` - `EnvScriptGenerator` (generates `env.sh`/`env.ps1`)
- `schema.py` - `WorkenvSchema` (validation schema only, renamed from `WorkenvConfig`)
- `workenv.py` - `WorkenvManager` (manages wrknv's own virtual environment)
- `bin_manager.py` - Tool binary path management
- `doctor.py` - Environment health checks

**Responsibilities**:
- Generate shell activation scripts (`env.sh`, `env.ps1`)
- Manage virtual environment creation
- Validate environment state
- Handle tool binaries and paths

**Note**: Schema is separate from runtime config - `WorkenvSchema` is for validation only.

### Workenv Packaging (`wrknv/workenv/`)

**Purpose**: Package and distribute pre-configured environments

**Key Files**:
- `export.py` - `WorkenvExporter` (export environments for sharing)
- `importer.py` - `WorkenvImporter` (import packaged environments)
- `packaging.py` - `WorkenvPackager` (create `.psp` packages)
- `registry.py` - `WorkenvRegistry` (workenv package registry)
- `config_templates.py` - `ConfigTemplateGenerator` (generate pyproject.toml, CLAUDE.md, etc.)

**Responsibilities**:
- Export current environment configuration
- Import and install packaged environments
- Create distributable packages
- Manage template-based config generation

**Note**: Uses `EnvScriptGenerator` from `wenv/` - does NOT duplicate generation logic.

### Tool Management (`wrknv/managers/`)

**Purpose**: Download, install, and manage development tools

**Key Files**:
- `base.py` - `BaseToolManager` (abstract base)
- `factory.py` - Tool manager factory
- Tool-specific managers: `terraform/`, `uv.py`, `go.py`, `bao.py`, etc.

**Responsibilities**:
- Download tool binaries
- Verify checksums and signatures
- Install tools to correct locations
- Manage tool versions

### Utilities (`wrknv/utils/`)

**Purpose**: Shared utility functions

**Key Files**:
- `python_version.py` - Python version detection and compatibility
- `version_resolver.py` - `VersionResolver` (resolve version patterns like `1.11.x`)

**Responsibilities**:
- Version string parsing and resolution
- Python environment inspection
- Common utility functions

### CLI Layer (`wrknv/cli/`)

**Purpose**: Command-line interface and user interaction

**Key Files**:
- `hub_cli.py` - Main CLI entry point (uses `provide.foundation.hub`)
- `visual.py` - Rich console UI (emojis, colors, formatting)
- `commands/` - Individual command implementations

**Responsibilities**:
- Parse command-line arguments
- Display rich output to users
- Orchestrate calls to core modules
- Handle user interaction

**UI Guidelines**: All visual/display logic belongs in `cli/`, not core modules.

## Key Design Principles

### 1. Single Source of Truth

**Configuration**: Only `wrknv.config.WorkenvConfig` for runtime configuration.
- ❌ WRONG: Multiple `WorkenvConfig` classes
- ✅ CORRECT: One `WorkenvConfig` in `config/`, one `WorkenvSchema` in `wenv/schema.py` (validation only)

**Env Generation**: Only `wrknv.wenv.env_generator.EnvScriptGenerator` for script generation.
- ❌ WRONG: Duplicate env generation in `workenv/export.py`
- ✅ CORRECT: `workenv/export.py` uses `EnvScriptGenerator` directly

### 2. Clear Separation of Concerns

**Core vs UI**:
- Core modules (`config/`, `wenv/`, `managers/`) should NOT import from `cli/`
- UI logic (`visual.py`) should NOT be in core modules
- ✅ CORRECT: `cli/visual.py` imported by CLI commands
- ❌ WRONG: `wenv/visual.py` mixed with core logic

**Configuration vs Schema**:
- Runtime config: `wrknv.config.WorkenvConfig` (attrs, env vars, persistence)
- Validation schema: `wrknv.wenv.schema.WorkenvSchema` (pure validation, no runtime logic)

### 3. Module Dependencies

Valid dependency directions:
```
CLI → Workenv → Wenv → Utils
CLI → Config → Utils
Managers → Utils
```

Invalid (circular):
```
Wenv → CLI ❌
Config → Workenv ❌
```

## Configuration Consolidation (2025-01)

Previously had 3 different `WorkenvConfig` classes:
1. `wrknv.config.WorkenvConfig` - Runtime (kept)
2. `wrknv.wenv.configuration.WorkenvConfig` - Old source-based (deleted)
3. `wrknv.wenv.schema.WorkenvConfig` - Validation (renamed to `WorkenvSchema`)

**Consolidation**:
- Deleted `wrknv.wenv.configuration/` entirely
- Renamed schema class to avoid naming collision
- All imports updated to use `wrknv.config.WorkenvConfig`

## File Organization Changes (2025-01)

**Moved to proper locations**:
- `wenv/python_version.py` → `utils/python_version.py` (utility, not core)
- `wenv/version_resolver.py` → `utils/version_resolver.py` (utility, not core)
- `wenv/visual.py` → `cli/visual.py` (UI belongs in CLI layer)

**Removed unnecessary inheritance**:
- `ConfigTemplateGenerator` no longer inherits from `EnvScriptGenerator`
- They serve different purposes (static configs vs environment scripts)

## Testing Strategy

- **Unit tests**: Test individual modules in isolation
- **Integration tests**: Test cross-module interactions
- **Test isolation**: Mock config file discovery to prevent environmental pollution
- **Fixtures**: Use `WorkenvConfig` directly, not deprecated classes

## Future Improvements

1. Consider renaming `wenv/` → `envgen/` for clarity (environment generation)
2. Move more shared utilities to `utils/` as they're identified
3. Further separate container operations from core environment generation
4. Improve async patterns in workenv import/export

## References

- Main config: `src/wrknv/config/core.py`
- Env generation: `src/wrknv/wenv/env_generator.py`
- CLI entry: `src/wrknv/cli/hub_cli.py`
- Schema validation: `src/wrknv/wenv/schema.py`
