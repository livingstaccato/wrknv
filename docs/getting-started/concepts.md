# Core Concepts

Understanding wrknv's architecture and design principles.

## The Environment Generation Model

wrknv follows a **configuration-driven code generation** approach:

```
┌─────────────────────┐
│  pyproject.toml     │  ← Your configuration
│  [tool.wrknv]      │
└──────────┬──────────┘
           │
           ↓ wrknv generate
┌─────────────────────┐
│  Templates (Jinja2) │  ← Shell script templates
│  sh/base.sh.j2     │
│  pwsh/base.ps1.j2  │
└──────────┬──────────┘
           │
           ↓ Render
┌─────────────────────┐
│  env.sh + env.ps1   │  ← Generated scripts
│  (300-400 lines)    │
└──────────┬──────────┘
           │
           ↓ source env.sh
┌─────────────────────┐
│  Running Env        │  ← Your development environment
│  ✓ Tools installed  │
│  ✓ Venv activated   │
│  ✓ Deps installed   │
└─────────────────────┘
```

## Key Concepts

### 1. Configuration, Not Code

wrknv replaces shell script **code** with TOML **configuration**:

**Before (Shell Script)**:
```bash
# env.sh (400 lines of bash)
TERRAFORM_VERSION="1.9.0"
GO_VERSION="1.22.0"
# ... 300+ more lines ...
```

**After (TOML Configuration)**:
```toml
# pyproject.toml (4 lines)
[tool.wrknv.tools]
terraform = "1.9.0"
go = "1.22.0"
```

### 2. Template-Based Generation

wrknv uses Jinja2 templates to generate platform-specific scripts:

- **Templates**: Battle-tested, maintained once
- **Generation**: Happens locally, verifiable
- **Scripts**: Fresh, correct, platform-appropriate

This means:
- ✅ No copy-paste errors
- ✅ Automatic platform handling
- ✅ Updates via `wrknv generate`
- ✅ Inspectable output

### 3. Work Environments (workenv/)

wrknv uses `workenv/` instead of `.venv/` for important reasons:

```
my-project/
├── pyproject.toml
├── env.sh              # Generated scripts
├── env.ps1
├── workenv/            # Work environment (wrknv-managed)
│   ├── bin/
│   ├── lib/
│   └── pyvenv.cfg
└── .venv/              # Never used by wrknv
```

**Why workenv/?**
- **Clear ownership**: Managed by wrknv, not manual
- **Avoid conflicts**: Doesn't interfere with IDE-created .venv/
- **Consistency**: Same name across all projects
- **Gitignore-friendly**: Standard pattern to exclude

### 4. Tool Managers

Each tool (UV, Terraform, Go) has a **manager** that knows how to:

1. **Download** - From official sources
2. **Verify** - Checksums and signatures
3. **Install** - To `workenv/bin/`
4. **Update** - When configuration changes

```
ToolManager (Abstract Base)
    ├── UVManager        # UV package manager
    ├── TerraformManager # HashiCorp Terraform
    ├── OpenTofuManager  # OpenTofu fork
    └── GoManager        # Go toolchain
```

**Manager Pattern Benefits:**
- Extensible: Add new tools easily
- Consistent: Same interface for all tools
- Platform-aware: Handles OS/architecture differences
- Cacheable: Reuses downloads across projects

### 5. Sibling Package Discovery

wrknv automatically finds and installs related packages in a monorepo:

```
workspace/
├── provide-foundation/     # Core library
│   └── pyproject.toml
├── pyvider/                # Depends on foundation
│   └── pyproject.toml
└── my-provider/            # Depends on both
    ├── pyproject.toml
    └── wrknv.toml
```

**Configuration:**
```toml
[tool.wrknv.siblings]
discover_patterns = ["../*/pyproject.toml"]
install_as_editable = true
```

**Discovery Process:**
1. Match patterns against filesystem
2. Read each `pyproject.toml`
3. Build dependency graph
4. Install in topological order
5. Use editable mode (`uv pip install -e`)

**Benefits:**
- ✅ No manual path management
- ✅ Automatic dependency order
- ✅ Live code updates (editable mode)
- ✅ Works across ecosystems

### 6. Configuration Hierarchy

wrknv loads configuration from multiple sources:

```
┌─────────────────────────┐
│  Default Values         │  ← Built-in defaults
└───────────┬─────────────┘
            │ (overridden by)
┌───────────▼─────────────┐
│  pyproject.toml         │  ← Project configuration
│  [tool.wrknv]          │
└───────────┬─────────────┘
            │ (overridden by)
┌───────────▼─────────────┐
│  wrknv.toml             │  ← Optional separate config
└───────────┬─────────────┘
            │ (overridden by)
┌───────────▼─────────────┐
│  Environment Variables  │  ← Runtime overrides
│  WRKNV_*               │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│  Final Configuration    │  ← Merged result
└─────────────────────────┘
```

### 7. Lockfiles

wrknv.lock ensures reproducible environments:

```toml
# wrknv.lock
[tools]
uv = { version = "0.5.1", hash = "sha256:..." }
terraform = { version = "1.9.0", hash = "sha256:..." }

[resolution]
timestamp = "2025-01-15T10:30:00Z"
platform = "darwin_arm64"
```

**Lock Command:**
```console
$ wrknv lock
✓ Resolved tool versions
✓ Verified checksums
✓ Created wrknv.lock
```

**Benefits:**
- 🔒 Exact versions across team
- 🔒 Verified downloads
- 🔒 Audit trail

### 8. Profiles

Different configurations for different environments:

```toml
# pyproject.toml
[tool.wrknv.tools]
uv = "0.5.1"

[tool.wrknv.profile.ci]
terraform = "1.9.0"  # CI needs Terraform

[tool.wrknv.profile.local]
terraform = "1.9.0"
go = "1.22.0"        # Local dev also needs Go
```

**Usage:**
```console
# Default profile
$ wrknv generate

# CI profile
$ wrknv generate --profile ci

# Local profile
$ wrknv generate --profile local
```

### 9. Container Integration

wrknv can generate environments **inside containers**:

```toml
[tool.wrknv.container]
runtime = "docker"
base_image = "python:3.11-slim"
volumes = [".:/workspace"]
```

**Workflow:**
```console
$ wrknv container build
$ wrknv container shell
(container) $ source env.sh
(container) $ # Fully configured environment inside Docker!
```

### 10. Doctor System

Health checks ensure your environment is correct:

```console
$ wrknv doctor
✓ Python version: 3.11.12 (✓ matches >=3.11)
✓ UV installed: 0.5.1 (✓ matches config)
✓ Virtual environment: workenv/ (✓ active)
✓ Dependencies: 45 packages (✓ all installed)
! Terraform: not found (⚠ specified in config)

2025-11-07 14:30:00 [WARNING] terraform specified but not installed
```

**Doctor Checks:**
- Python version requirements
- Tool installation and versions
- Virtual environment state
- Dependency installation
- Configuration validity
- Platform compatibility

## Design Principles

### 1. Configuration Over Convention

wrknv requires explicit configuration. No hidden magic.

**Example:** You must specify tool versions:
```toml
[tool.wrknv.tools]
uv = "0.5.1"  # Explicit, not "latest"
```

### 2. Generate, Don't Abstract

wrknv generates readable scripts you can inspect and modify.

**Philosophy:**
- Scripts are **artifacts**, not black boxes
- You can read `env.sh` to see what it does
- Modifications go in config, not scripts
- Regenerate anytime with `wrknv generate`

### 3. Platform Native

Generated scripts use platform-native patterns:

- **Linux/macOS**: Bash with POSIX compatibility
- **Windows**: PowerShell with native cmdlets

No "universal shell" compromises.

### 4. Tool Ownership

wrknv owns tool installation, not your entire environment:

**wrknv manages:**
- Tools in `workenv/bin/`
- Python virtual environment
- Sibling package installation

**wrknv does NOT manage:**
- System Python installation
- IDE configuration
- Global shell settings
- Git configuration

### 5. Fail Fast, Fail Clearly

wrknv validates early and provides clear errors:

```console
$ wrknv generate
❌ Error: Python version 3.9.0 does not satisfy requirement >=3.11
   Current: 3.9.0
   Required: >=3.11

   Please upgrade Python or adjust requires-python in pyproject.toml
```

## Common Patterns

### Pattern 1: Monorepo Structure

```
workspace/
├── .wrknvignore          # Exclude certain directories
├── library-a/
│   └── pyproject.toml    # [tool.wrknv.siblings]
├── library-b/
│   └── pyproject.toml    # [tool.wrknv.siblings]
└── app/
    └── pyproject.toml    # Uses both libraries
```

### Pattern 2: CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Setup Environment
  run: |
    uv tool install wrknv
    wrknv generate --profile ci
    source env.sh
    pytest
```

### Pattern 3: Team Standardization

All team projects use:
```toml
[tool.wrknv.tools]
uv = "0.5.1"  # Team standard
```

One command updates all projects:
```console
$ for dir in */; do (cd "$dir" && wrknv generate); done
```

## Next Steps

Now that you understand wrknv's concepts:

- **[API Reference](../reference/)** - Python API documentation
- **[Quick Start Guide](quick-start.md)** - Get wrknv running
- **[Installation Guide](installation.md)** - Complete setup guide

Or return to:

- **[Getting Started Index](index.md)**
