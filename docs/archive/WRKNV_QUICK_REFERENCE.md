# wrknv Architecture Quick Reference

## Key Components Map

```
wrknv/src/
├── cli/
│   ├── hub_cli.py ..................... Main CLI entry (@register_command pattern)
│   └── commands/
│       ├── workspace.py ............... Workspace management commands
│       ├── container.py ............... Docker container commands
│       ├── profile.py ................. Tool version profiles
│       ├── tools.py ................... Tool management
│       └── setup.py, config.py, etc.
│
├── config/
│   ├── core.py ....................... WorkenvConfig (runtime, loads .wrknv.toml)
│   ├── defaults.py ................... Default values
│   └── persistence.py ................ Config file I/O
│
├── wenv/
│   ├── schema.py ..................... WorkenvSchema (typed config)
│   ├── env_generator.py .............. Jinja2 template generation for env.sh/.ps1
│   ├── workenv.py .................... Workenv manager
│   └── managers/
│       ├── base.py ................... BaseToolManager (abstract)
│       └── factory.py ................ get_tool_manager()
│
├── managers/
│   ├── base.py ....................... BaseToolManager abstract interface
│   ├── factory.py .................... Manager factory & tool registry
│   ├── uv.py ......................... UV package manager
│   ├── go.py ......................... Go toolchain
│   ├── tf/ ........................... Terraform (base, IBM variant, OpenTofu)
│   └── subrosa/ ...................... Secret management (Bao, Vault)
│
├── workspace/
│   ├── discovery.py .................. WorkspaceDiscovery (repo analysis)
│   ├── manager.py .................... WorkspaceManager (main API)
│   ├── schema.py ..................... RepoConfig, WorkspaceConfig
│   ├── sync.py ....................... WorkspaceSync (config distribution)
│   └── init_workspace() .............. Creates .wrknv/workspace.toml
│
├── container/
│   ├── core.py / manager.py .......... ContainerManager (Docker integration)
│   ├── operations/ ................... build.py, lifecycle.py, volumes.py
│   ├── runtime/ ...................... Docker implementation
│   └── shell_commands.py ............. Container CLI wrapper
│
└── templates/
    └── env/
        ├── sh/ ....................... Bash environment templates
        └── pwsh/ ..................... PowerShell templates
```

## Data Flow

### 1. Workspace Initialization
```
wrknv workspace init
  ├─> WorkspaceManager.__init__()
  ├─> WorkspaceDiscovery.discover_repos()
  │   └─> Scan for git repos + pyproject.toml
  │       └─> detect_repo_type() by name/deps/files
  └─> Create .wrknv/workspace.toml
      └─> Stores RepoConfig[] with paths, types, profiles
```

### 2. Configuration Loading
```
WorkenvConfig.load()
  ├─> _find_config_file() - checks .wrknv.toml, wrknv.toml, pyproject.toml
  ├─> _load_config() from TOML
  ├─> Merge with WRKNV_* environment variables
  └─> Access via WrknvContext.get_config() (singleton)
```

### 3. Environment Script Generation
```
EnvScriptGenerator.generate_env_script()
  ├─> Load Jinja2 templates from src/wrknv/templates/env/
  ├─> Build context dict (project name, tools_to_verify, sibling_patterns)
  └─> Render to env.sh (sh) or env.ps1 (pwsh)
```

### 4. Tool Manager Usage
```
get_tool_manager("uv")
  ├─> Returns UvManager instance (if available)
  └─> Manager knows:
      ├─> get_available_versions() - query upstream
      ├─> get_download_url(version) - build download URL
      ├─> get_installed_version() - from config
      └─> get_binary_path(version) - where binary lives
```

## Configuration Hierarchy

```
workspace.toml (.wrknv/workspace.toml)
  ├─ repos: list[RepoConfig]
  ├─ template_source: TemplateSource
  ├─ global_standards: dict
  └─ sync_strategy: "manual" | "auto" | "check"

wrknv.toml (project level)
  ├─ tools: dict[tool_name -> ToolConfig]
  ├─ profiles: dict[profile_name -> tools]
  ├─ container: ContainerConfig
  └─ workenv: WorkenvSettings
```

## Command Registration Pattern

```python
# In cli/commands/workspace.py
from provide.foundation.hub import register_command

@register_command("workspace", group=True, description="...")
def workspace_group() -> None:
    pass

@register_command("workspace.init", description="...")
def init(...) -> None:
    pass

@register_command("workspace.add", description="...")
def add_repo(...) -> None:
    pass
```

**Hub Pattern Benefits**:
- Avoid monolithic CLI file
- Commands are isolated modules
- Can be lazily loaded
- Easy to add new commands (just register_command decorator)
- Perfect for plugin-like extensions

## Key Interfaces

### BaseToolManager
```python
class BaseToolManager(ABC):
    @property
    def tool_name(self) -> str          # e.g., "terraform"
    
    @property
    def executable_name(self) -> str    # e.g., "terraform"
    
    def get_available_versions(self) -> list[str]
    def get_download_url(self, version: str) -> str
    def get_checksum_url(self, version: str) -> str | None
    def get_binary_path(self, version: str) -> Path
    def get_installed_version(self) -> str | None
    def set_installed_version(self, version: str) -> None
```

### WorkspaceManager
```python
class WorkspaceManager:
    def init_workspace(...) -> WorkspaceConfig
    def load_config() -> WorkspaceConfig | None
    def save_config(config: WorkspaceConfig) -> None
    def add_repo(...) -> WorkspaceConfig
    def remove_repo(name: str) -> WorkspaceConfig
    async def sync_all(dry_run: bool = False) -> dict[str, Any]
    async def sync_repo(name: str, dry_run: bool = False) -> dict[str, Any]
    def get_workspace_status() -> dict[str, Any]
```

### WorkspaceDiscovery
```python
class WorkspaceDiscovery:
    def discover_repos(patterns: list[str] | None = None) -> list[RepoInfo]
    def analyze_repo(path: Path) -> RepoInfo
    def detect_repo_type(pyproject: dict, path: Path) -> str | None
    def get_repo_status(repo_path: Path) -> dict[str, Any]
    def get_workspace_summary() -> dict[str, Any]
```

## Repository Type Detection

```
Detection Priority:
1. Name pattern matching (most specific)
   - "provide-foundation" -> "foundation"
   - "provide-testkit" -> "testkit"
   - "pyvider-*" -> "pyvider-plugin"
   - "flavor" -> "packaging"

2. Dependencies in pyproject.toml
   - "provide-foundation" -> "foundation-based"
   - "pyvider" -> "pyvider-plugin"

3. File structure
   - src/pyvider exists -> "provider"
   - src/provide exists -> "foundation-based"

4. Classifiers in pyproject.toml

Result: type: str = "foundation" | "foundation-based" | "provider" | 
                    "pyvider-plugin" | "testkit" | "packaging" | "unknown"
```

## Build Orchestration Extension Points

### Current Gaps (for build orchestration)
- No dependency graph tracking
- No affected package detection
- No build command orchestration
- No result aggregation

### Where to Add Build Features

1. **RepoConfig** (workspace/schema.py)
   - Add: `dependencies: dict[str, str]`
   - Add: `build_config: dict[str, Any]`

2. **WorkspaceDiscovery** (workspace/discovery.py)
   - Add: `detect_dependencies(repo: Path) -> dict[str, str]`
   - Add: `build_dependency_graph() -> DependencyGraph`

3. **WorkspaceManager** (workspace/manager.py)
   - Add: `get_dependency_graph() -> DependencyGraph`
   - Add: `get_affected_repos(repos: list[str]) -> list[str]`
   - Add: `async build_repos(...) -> dict[str, BuildResult]`

4. **BaseToolManager** (managers/base.py)
   - Add: `async build(repo_path: Path, **kwargs) -> BuildResult`
   - Add: `get_build_command() -> str`

5. **CLI Commands** (cli/commands/workspace.py)
   - Add: `@register_command("workspace.build")`
   - Add: `@register_command("workspace.affected")`
   - Add: `@register_command("workspace.graph")`

6. **New Modules**:
   - `src/wrknv/build/graph.py` - Dependency graph logic
   - `src/wrknv/build/manager.py` - Build orchestrator
   - `src/wrknv/build/affected.py` - Affected detection
   - `src/wrknv/git/operations.py` - Git integration

## Supported Tools Registry

```python
def get_supported_tools() -> list[str]:
    return ["ibmtf", "tofu", "bao", "vault", "uv", "go"]

# Tool managers available via:
get_tool_manager("uv")      # UvManager
get_tool_manager("go")      # GoManager
get_tool_manager("ibmtf")   # IbmTfVariant
get_tool_manager("tofu")    # TofuTfVariant
get_tool_manager("bao")     # BaoVariant
get_tool_manager("vault")   # IbmVaultVariant
```

## Testing & Integration

- Tests in: `tests/` mirroring `src/` structure
- Config tests: `tests/config/test_*.py`
- Workspace tests: `tests/workspace/test_*.py`
- Container tests: `tests/container/test_*.py`
- Manager tests: `tests/managers/test_*.py`

## Important Constraints

- **Python 3.11+** only (uses modern type hints, native TOML)
- **No hardcoded defaults** - configuration must be explicit
- **Virtual env location**: Always `workenv/`, never `.venv/`
- **No backward compatibility** - clean code prioritized
- **Async-first for I/O** - matches existing patterns

