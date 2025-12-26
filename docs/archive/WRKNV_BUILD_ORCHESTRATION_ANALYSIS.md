# wrknv Architecture Deep Dive & Build Orchestration Design

## Executive Summary

wrknv is a **workspace environment management tool** that generates standardized development environment scripts (env.sh, env.ps1) for multi-repo workspaces. It manages tool versions, configures development containers, and synchronizes configurations across repositories. The architecture is modular with clear separation between CLI, configuration, managers, and workspace management.

## 1. CORE ARCHITECTURE

### 1.1 Main Entry Points & CLI System

**File**: `src/wrknv/cli/hub_cli.py`

- Uses **provide.foundation.hub** pattern for command registration
- Commands are loaded via decorators from separate module files
- Main CLI created dynamically via `create_cli()` function
- Commands are organized in `/src/wrknv/cli/commands/` with ~12 command modules
- Hub pattern allows:
  - Lazy loading of command modules
  - Avoiding monolithic CLI file
  - Plugin-like extension capability
  - Test isolation (hub clearing between tests)

```python
class WrknvContext:
    """Shared context for wrknv CLI commands."""
    @classmethod
    def get_config(cls) -> WorkenvConfig:
        # Singleton pattern for config access
```

**Current Commands**:
- `config` - Configuration management
- `container` - Docker container operations
- `doctor` - Diagnostics
- `gitignore` - .gitignore generation
- `lock` - Dependency locking
- `profile` - Tool version profiles
- `secrets` - Secret management
- `setup` - Setup & integration
- `terraform` - Terraform-specific commands
- `tools` - Tool management
- `workspace` - Multi-repo workspace management

### 1.2 Configuration Architecture

**Files**:
- `src/wrknv/config/core.py` - Runtime config (WorkenvConfig)
- `src/wrknv/wenv/schema.py` - Schema definitions (WorkenvSchema)
- `src/wrknv/workspace/schema.py` - Workspace schemas

**WorkenvConfig** (Runtime, loads from wrknv.toml):
```python
@define
class WorkenvConfig(RuntimeConfig):
    project_name: str
    version: str
    tools: dict[str, dict[str, Any]]  # tool_name -> {version, path, env}
    container: ContainerConfig | None
    profiles: dict[str, dict[str, str]]
    workenv: WorkenvSettings  # auto_install, cache, log_level, etc.
    env: dict[str, Any]
    gitignore: dict[str, Any]
```

**WorkenvSchema** (Type-safe schema with validators):
```python
@define
class WorkenvSchema:
    project_name: str
    tools: dict[str, ToolConfig]  # Version-specific configs
    container: ContainerConfig | None
    package: PackageConfig | None
    registry: RegistryConfig | None
    profiles: dict[str, ProfileConfig]
    # ... plus install_dir, cache_dir, log_level, telemetry, etc.
```

**Workspace Schemas** (`workspace/schema.py`):
```python
@define(frozen=True)
class RepoConfig:
    path: Path
    name: str
    type: str  # "provider", "foundation", "testkit", "foundation-based", etc.
    template_profile: str
    features: list[str]
    custom_values: dict[str, Any]
    last_sync: str | None
    template_version: str | None

@define(frozen=True)
class WorkspaceConfig(BaseConfig):
    root: Path
    repos: list[RepoConfig]
    template_source: TemplateSource | None
    global_standards: dict[str, Any]
    sync_strategy: str  # "manual", "auto", "check"
```

**Config Loading Priority**:
1. File: `.wrknv.toml`, `wrknv.toml`, `pyproject.toml`, `~/.config/wrknv/config.toml`
2. Environment: `WRKNV_*` variables
3. Default values from `src/wrknv/config/defaults.py`

### 1.3 Tool Management System

**Base Class**: `src/wrknv/managers/base.py`

```python
class BaseToolManager(ABC):
    def __init__(self, config: WorkenvConfig | None = None)
    
    @property
    @abstractmethod
    def tool_name(self) -> str
    
    @property
    @abstractmethod
    def executable_name(self) -> str
    
    @abstractmethod
    def get_available_versions(self) -> list[str]
    
    @abstractmethod
    def get_download_url(self, version: str) -> str
    
    @abstractmethod
    def get_checksum_url(self, version: str) -> str | None
    
    def get_binary_path(self, version: str) -> pathlib.Path
    def get_installed_version(self) -> str | None
    def set_installed_version(self, version: str) -> None
```

**Concrete Managers**:
- `managers/uv.py` - UV package manager
- `managers/go.py` - Go toolchain
- `managers/tf/base.py`, `managers/tf/ibm.py`, `managers/tf/tofu.py` - Terraform variants
- `managers/subrosa/` - Secret management (Bao, Vault)

**Factory Pattern**: `src/wrknv/managers/factory.py`
```python
def get_tool_manager(tool_name: str, config: WorkenvConfig | None = None) -> BaseToolManager | None
def get_supported_tools() -> list[str]  # ibmtf, tofu, bao, vault, uv, go
```

### 1.4 Workspace Management

**Discovery**: `src/wrknv/workspace/discovery.py`

Discovers repositories and analyzes them:
```python
class WorkspaceDiscovery:
    def discover_repos(patterns: list[str] | None = None) -> list[RepoInfo]
    def analyze_repo(path: Path) -> RepoInfo
    def detect_repo_type(pyproject: dict, path: Path) -> str | None
    def get_repo_status(repo_path: Path) -> dict[str, Any]
    def validate_workspace_structure(root: Path) -> list[str]
    def get_workspace_summary() -> dict[str, Any]
```

Detects repo type based on:
- Name patterns: `provide-foundation`, `provide-testkit`, `pyvider-*`, `flavor`
- Dependencies: `provide-foundation`, `pyvider` in pyproject.toml
- File structure: presence of `src/pyvider`, `src/provide`
- Classifiers in pyproject.toml

**Manager**: `src/wrknv/workspace/manager.py`

```python
class WorkspaceManager:
    def init_workspace(template_source: str | None = None, auto_discover: bool = True) -> WorkspaceConfig
    def load_config() -> WorkspaceConfig | None
    def save_config(config: WorkspaceConfig) -> None
    def add_repo(repo_path: Path | str, ...) -> WorkspaceConfig
    def remove_repo(name: str) -> WorkspaceConfig
    async def sync_all(dry_run: bool = False) -> dict[str, Any]
    async def sync_repo(name: str, dry_run: bool = False) -> dict[str, Any]
    def check_drift() -> dict[str, Any]
    def get_workspace_status() -> dict[str, Any]
    def setup_workspace(generate_only: bool = False) -> dict[str, Any]
```

Workspace config stored in `.wrknv/workspace.toml`

### 1.5 Environment Script Generation

**File**: `src/wrknv/wenv/env_generator.py`

```python
class EnvScriptGenerator:
    def __init__(self, template_base_dir: Path | None = None)
    def generate_env_script(
        project_name: str,
        output_path: Path,
        script_type: str = "sh",  # "sh" or "ps1"
        **kwargs: Any
    ) -> None
```

**Templates Location**: `src/wrknv/templates/env/`
- `sh/` - Bash/sh templates (env.sh)
- `pwsh/` - PowerShell templates (env.ps1)

**Template Variables**:
- `project_name`, `env_profile_var`, `venv_prefix`
- `install_siblings`, `sibling_patterns`, `special_siblings`
- `tools_to_verify` - List of tools to check (Python, UV, wrknv, ibmtf, tofu)
- `useful_commands` - Help commands to display
- Uses Jinja2 with `trim_blocks`, `lstrip_blocks`

### 1.6 Container Management

**File**: `src/wrknv/container/core.py`, `src/wrknv/container/manager.py`

```python
class ContainerManager:
    def build_container(config: WorkenvConfig, rebuild: bool = False) -> bool
    def start_container() -> bool
    def stop_container() -> bool
    def restart_container() -> bool
    def enter_container() -> bool
    def get_container_status() -> dict[str, Any]
    def clean_container() -> bool
```

**Container Runtime**: `src/wrknv/container/runtime/docker.py`
- Abstract base: `src/wrknv/container/runtime/base.py`
- Supports Docker operations with container names like `wrknv-<project>-dev`

**Container Operations**:
- `operations/build.py` - Image building
- `operations/exec.py` - Command execution
- `operations/lifecycle.py` - Container start/stop/restart
- `operations/logs.py` - Log viewing
- `operations/volumes.py` - Volume management

## 2. WORKSPACE DISCOVERY & ANALYSIS

### 2.1 Repository Type Detection

**Detection Order**:
1. Name patterns (most specific)
2. Dependencies in pyproject.toml
3. File structure
4. Classifiers

**Supported Types**:
- `foundation` - provide-foundation base library
- `foundation-based` - Packages using provide-foundation
- `provider` - pyvider main package
- `pyvider-plugin` - pyvider plugins/extensions
- `testkit` - provide-testkit
- `packaging` - flavor/packaging tools
- `unknown` - Cannot determine

### 2.2 Cross-Repo Dependency Discovery

**Current Implementation**: Limited
- Discovers git repos with pyproject.toml
- Analyzes dependencies to detect type
- Template features configured by type

**Gaps for Build Orchestration**:
- No explicit dependency graph tracking
- No "sibling detection" for workspace dependencies
- No affected package detection when one repo changes

## 3. KEY EXTENSION POINTS FOR BUILD ORCHESTRATION

### 3.1 Configuration System

**Extension Point**: Workspace/RepoConfig schemas
- Add `dependencies: dict[str, str]` to RepoConfig
- Add `build_config: dict[str, Any]` for build-specific settings
- Add `affected_by: list[str]` for tracking dependents

**Location**: `src/wrknv/workspace/schema.py`

```python
@define(frozen=True)
class RepoConfig:
    # ... existing fields ...
    dependencies: dict[str, str] = field(factory=dict)  # repo_name -> constraint
    build_config: dict[str, Any] = field(factory=dict)  # build-specific settings
    affected_by: list[str] = field(factory=list)  # repos that depend on this
```

### 3.2 Workspace Discovery

**Extension Point**: WorkspaceDiscovery class
- Enhance `analyze_repo()` to extract dependencies
- Add `detect_dependencies()` method
- Add `build_dependency_graph()` method
- Add `get_affected_repos()` method

**Location**: `src/wrknv/workspace/discovery.py`

Key opportunities:
- Parse pyproject.toml `[project.dependencies]` for workspace references
- Analyze `[tool.uv.sources]` for workspace paths
- Check `PYTHONPATH` or workspace sibling patterns
- Build transitive dependency graph

### 3.3 Workspace Manager

**Extension Points**: WorkspaceManager class

New methods:
```python
def get_dependency_graph(self) -> DependencyGraph
def get_affected_repos(self, repo_names: list[str]) -> list[str]
async def build_repos(
    repo_names: list[str] | None = None,
    parallel: bool = False,
    topological_order: bool = True
) -> dict[str, BuildResult]
def detect_changes(self, base_branch: str) -> dict[str, list[str]]
```

**Location**: `src/wrknv/workspace/manager.py`

### 3.4 Tool Managers

**Extension Point**: BaseToolManager class

Add build orchestration methods:
```python
async def build(self, repo_path: Path, **kwargs) -> BuildResult
async def test(self, repo_path: Path, **kwargs) -> TestResult
def get_build_commands(self) -> dict[str, str]
def get_test_commands(self) -> dict[str, str]
```

Could be specialized per tool:
- UvManager: Handles Python builds via `uv build`
- GoManager: Handles Go builds via `go build`
- Terraform managers: Could coordinate Terraform apply/test

**Location**: `src/wrknv/managers/base.py`

### 3.5 CLI Commands

**New Command Group**: `workspace.build` (or separate `build` group)

```python
@register_command("workspace.build", description="Build repositories in dependency order")
@register_command("workspace.test", description="Test affected repositories")
@register_command("workspace.affected", description="Show affected repos for changes")
@register_command("workspace.graph", description="Display dependency graph")
```

**Location**: New or enhanced `src/wrknv/cli/commands/workspace.py`

### 3.6 Synchronization System

**Extension Point**: WorkspaceSync class

Currently syncs configuration templates. Could extend to:
- Run build commands after sync
- Coordinate build outputs
- Cache build artifacts per repo
- Track build metadata per sync

**Location**: `src/wrknv/workspace/sync.py`

## 4. EXISTING PATTERNS TO LEVERAGE

### 4.1 Manager Pattern

All tools use abstract base class with concrete implementations:
```python
class ToolManager(ABC):
    @abstractmethod
    def get_available_versions() -> list[str]
    @abstractmethod
    def get_download_url(version: str) -> str
```

**Apply to builds**: Create `BuildManager` base with:
- `get_build_targets()` - What can be built
- `execute_build()` - Run build
- `parse_build_output()` - Extract results
- `get_dependencies()` - Build dependencies

### 4.2 Hub Registration Pattern

Commands registered via `@register_command()` decorators:
```python
@register_command("workspace", group=True, description="...")
def workspace_group() -> None:
    pass

@register_command("workspace.init", description="...")
def init(...) -> None:
    pass
```

**Apply to builds**:
```python
@register_command("workspace.build", description="Build in dependency order")
def build_cmd(repos: list[str] | None = None, parallel: bool = False, ...) -> None:
    pass
```

### 4.3 Configuration Schema Pattern

Typed configuration with validators:
```python
@define
class ToolConfig:
    version: str = field(validator=[validators.instance_of(str), validate_version])
    enabled: bool = field(default=DEFAULT_TOOL_ENABLED)
    environment: dict[str, str] = field(factory=dict)
```

**Apply to builds**:
```python
@define
class BuildConfig:
    enabled: bool = field(default=True)
    command: str = field(validator=...)
    parallel: bool = field(default=False)
    dependencies: list[str] = field(factory=list)
```

### 4.4 Workspace Sync Pattern

Current WorkspaceSync handles configuration distribution:
```python
async def sync_all(dry_run: bool = False) -> dict[str, Any]
async def sync_repo(repo: RepoConfig, dry_run: bool = False) -> dict[str, Any]
def _build_template_context(repo: RepoConfig) -> dict[str, Any]
```

**Apply to builds**:
- Similar async pattern for distributed build execution
- Per-repo results tracking
- Dry-run capability for planning

## 5. GIT INTEGRATION POINTS

### 5.1 Current Git Usage

**File**: `src/wrknv/workspace/discovery.py`

```python
def _get_git_status(repo_path: Path) -> dict[str, Any] | None:
    # Gets: current branch, dirty status, files changed count
```

### 5.2 Build Orchestration Git Integration

**New Capabilities Needed**:
- Detect changed files since base branch: `git diff --name-only base...HEAD`
- Map changed files to repos: Match paths to RepoConfig paths
- Get commit metadata: Author, timestamp, message
- Check repo status before building: Stash/clean working directory

**Suggested Location**: New module `src/wrknv/git/` or in discovery

## 6. PYPROJECT.TOML INTEGRATION

### 6.1 Current Integration

**Locations**:
- `discovery.py` - Reads `[project]` and dependencies
- `env_generator.py` - Template variables for pyproject fields
- `workspace/sync.py` - Merges workspace standards with repo pyproject

### 6.2 Build Orchestration Integration

**Parse from pyproject.toml**:
```toml
[tool.wrknv.workspace]
# Sibling packages
sibling_sources = {provide-foundation = "../provide-foundation"}

[tool.wrknv.build]
enabled = true
command = "uv build"  # or custom build script
test_command = "pytest"
dependencies = ["provide-foundation"]  # Internal dependencies
```

**Parsing Location**: Extend `discovery.py` or new `src/wrknv/config/pyproject.py`

## 7. DESIGN PATTERNS FOR EXTENSION

### 7.1 Data Models

**DependencyGraph**: 
```python
@define
class DependencyEdge:
    source: str  # repo name
    target: str  # repo name
    constraint: str  # version constraint if any

@define
class DependencyGraph:
    nodes: dict[str, RepoConfig]
    edges: list[DependencyEdge]
    
    def topological_sort(self) -> list[str]
    def get_dependents(self, repo: str) -> list[str]
    def get_transitive_dependents(self, repos: list[str]) -> set[str]
```

**BuildResult**:
```python
@define
class BuildResult:
    repo_name: str
    success: bool
    duration_seconds: float
    output: str
    error: str | None
    artifacts: dict[str, Path]  # artifact_type -> path
    timestamp: str
```

**AffectedRepos**:
```python
@define
class AffectedAnalysis:
    changed_files: list[str]
    repo_changes: dict[str, list[str]]  # repo -> [changed_files]
    affected_repos: list[str]
    analysis_details: dict[str, Any]
```

### 7.2 New Modules

Create modular structure:
```
src/wrknv/
├── build/
│   ├── __init__.py
│   ├── graph.py           # DependencyGraph, topological sorting
│   ├── manager.py         # BuildManager base/orchestrator
│   ├── affected.py        # Affected repo detection
│   └── result.py          # BuildResult, test results
├── git/
│   ├── __init__.py
│   ├── operations.py      # Git operations for build context
│   └── integration.py     # Integration with discovery
```

### 7.3 Command Organization

Organize related commands:
```
workspace.build - Build repos in order
workspace.build.affected - Build only affected
workspace.build.all - Build all
workspace.test - Run tests
workspace.graph - Show dependency graph
workspace.affected - Show affected repos for changes
```

## 8. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Data Models & Discovery)
1. Add `DependencyGraph` to `build/graph.py`
2. Enhance `WorkspaceDiscovery.analyze_repo()` to extract dependencies
3. Add `get_dependency_graph()` to `WorkspaceManager`
4. Add dependency fields to `RepoConfig` schema

### Phase 2: Affected Detection
1. Implement `get_affected_repos()` in `WorkspaceManager`
2. Create `build/affected.py` with git-based change detection
3. Add `workspace.affected` CLI command
4. Add `workspace.graph` CLI command to visualize

### Phase 3: Build Execution
1. Create `BuildManager` base class with:
   - `execute_build()` - Run build command
   - `parse_output()` - Extract artifacts/errors
   - `get_build_command()` - Tool-specific build command
2. Extend `ToolManager` with build methods
3. Implement topological build ordering
4. Add parallel execution support (with dependency constraints)

### Phase 4: CLI & Integration
1. Add `workspace.build` command group
2. Implement `--affected`, `--parallel`, `--dry-run` flags
3. Add build result reporting/visualization
4. Integrate with `WorkspaceSync` for coordinated operations

## 9. CRITICAL DESIGN DECISIONS

### 9.1 Where Does Dependency Tracking Live?

**Option A**: In RepoConfig (schema.py)
- Pros: Explicit, queryable, saveable
- Cons: Requires user maintenance

**Option B**: Computed from pyproject.toml (discovery.py)
- Pros: Single source of truth, version constraint info
- Cons: Requires parsing, may miss implicit deps

**Recommendation**: **Hybrid approach**
- Extract explicit dependencies from pyproject.toml during discovery
- Allow override/manual specification in RepoConfig
- Cache computed graph in workspace state

### 9.2 Build Orchestration Level

**Option A**: Per-tool (each ToolManager does builds)
- Pros: Tool-specific optimization
- Cons: Complex coordination

**Option B**: Centralized (BuildManager orchestrates all)
- Pros: Clean separation, easier to reason about order
- Cons: Must understand all tool build patterns

**Recommendation**: **Centralized orchestrator** (Option B)
- BuildManager knows about ToolManagers
- ToolManagers implement `get_build_command()` interface
- Orchestrator handles order, parallelism, artifact collection

### 9.3 Async vs Sync Execution

**Current wrknv style**: Heavy use of async (esp. WorkspaceSync)

**For builds**: Should be async for:
- Parallel builds of independent repos
- Non-blocking I/O for long-running builds
- Progress reporting and cancellation

**Recommendation**: Match existing pattern with async/await

### 9.4 Configuration vs Runtime Discovery

**Dependencies**: Should they be:
- Explicit in workspace.toml? (Requires maintenance)
- Auto-detected from pyproject.toml? (Always current)
- Cached in workspace state? (Performance)

**Recommendation**: Auto-detect from pyproject.toml, cache in memory, invalidate when repo config changes

## 10. INTEGRATION WITH EXISTING SYSTEMS

### 10.1 With Workspace Sync

After syncing configs, could trigger:
```python
# In workspace/sync.py
async def sync_repo(self, repo: RepoConfig, dry_run: bool = False):
    changes = await self._apply_config_change(...)
    
    # NEW: Check if rebuild needed
    if changes and self.config.build_on_sync:
        await self._trigger_build(repo)
    
    return result
```

### 10.2 With Container Management

Build artifacts could be:
- Mounted into containers for testing
- Used to populate container images
- Tested in containers before deployment

### 10.3 With Tool Managers

Tool managers could:
- Report which tools are needed for builds
- Provide build commands specific to tool/repo combo
- Handle tool-specific artifact gathering

### 10.4 With Environment Generation

Generated env scripts could include:
- Build commands: `wrknv build`
- Affected detection: `wrknv affected`
- Pre-commit hooks for build validation

## 11. NATURAL EXTENSION PATTERNS

The architecture already supports extension through:

1. **Manager Pattern**: New BuildManager follows same pattern as ToolManager
2. **Hub Registration**: New commands registered same way
3. **Schema Pattern**: New BuildConfig follows same attrs pattern
4. **Async Pattern**: Mirrors WorkspaceSync async operations
5. **Factory Pattern**: Could extend get_tool_manager to handle builds
6. **Configuration Priority**: Environment vars, TOML, defaults all work

**Key insight**: Build orchestration fits naturally into wrknv's existing architecture because it's just another type of manager/operation that wrknv coordinates across a workspace.

