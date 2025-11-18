# wrknv Build Orchestration - Code Examples & Implementation Guide

## Critical File Paths for Build Orchestration

### Primary Files to Understand

```
/Users/tim/code/gh/provide-io/wrknv/src/wrknv/
├── workspace/schema.py ................ RepoConfig (where to add dependencies)
├── workspace/discovery.py ............ detect_dependencies() goes here
├── workspace/manager.py .............. build_repos() & graph methods here
├── managers/base.py .................. Abstract build interface
├── cli/commands/workspace.py ......... New build commands here
└── (NEW) build/
    ├── graph.py ....................... DependencyGraph implementation
    ├── manager.py ..................... BuildOrchestrator
    └── affected.py .................... AffectedAnalysis
```

## 1. EXTENDING RepoConfig (workspace/schema.py)

### Current Code
```python
@define(frozen=True)
class RepoConfig:
    path: Path
    name: str
    type: str
    template_profile: str
    features: list[str] = field(factory=list)
    custom_values: dict[str, Any] = field(factory=dict)
    last_sync: str | None = None
    template_version: str | None = None
```

### Required Addition
```python
@define(frozen=True)
class RepoConfig:
    # ... existing fields ...
    
    # NEW: Build orchestration fields
    dependencies: dict[str, str] = field(
        factory=dict,
        validator=validators.instance_of(dict)
    )  # Maps repo_name -> version_constraint
    
    build_config: dict[str, Any] = field(
        factory=dict,
        validator=validators.instance_of(dict)
    )  # Build-specific settings like build_command, test_command
    
    # Track which repos depend on this one (computed field)
    affected_by: list[str] = field(
        factory=list,
        validator=validators.instance_of(list)
    )  # Repos that list this one as dependency

    # Also update from_dict() and to_dict() methods to handle new fields
```

**Migration in to_dict()**:
```python
def to_dict(self) -> dict[str, Any]:
    """Convert to dictionary, excluding None values for TOML compatibility."""
    data = {
        # ... existing fields ...
        "dependencies": self.dependencies,
        "build_config": self.build_config,
        "affected_by": self.affected_by,
    }
    return {k: v for k, v in data.items() if v is not None}
```

## 2. EXTENDING WorkspaceDiscovery (workspace/discovery.py)

### New Method: detect_dependencies
```python
def detect_dependencies(self, repo: RepoInfo) -> dict[str, str]:
    """Extract workspace dependencies from a repository.
    
    Returns:
        Dict mapping repo_name -> version_constraint
        For workspace deps, constraint is typically "*" (any)
    """
    dependencies = {}
    
    if not repo.current_config:
        return dependencies
    
    pyproject = repo.current_config
    project_deps = pyproject.get("project", {}).get("dependencies", [])
    
    # Check for workspace dependencies
    # Pattern 1: Direct path references (e.g., "../provide-foundation")
    workspace_sources = pyproject.get("tool", {}).get("uv", {}).get("sources", {})
    if workspace_sources:
        for pkg_name, source_config in workspace_sources.items():
            if isinstance(source_config, dict) and "workspace" in source_config:
                # This is a workspace reference
                # Map package name to repo name (heuristic)
                repo_name = self._package_to_repo_name(pkg_name)
                dependencies[repo_name] = "*"  # workspace deps are unversioned
    
    # Pattern 2: Check for internal dependencies by name
    # (for provide-io ecosystem specifics)
    internal_prefixes = ["provide-", "pyvider-", "flavor-"]
    for dep in project_deps:
        dep_name = dep.split(";")[0].split(">=")[0].strip()
        for prefix in internal_prefixes:
            if dep_name.startswith(prefix):
                repo_name = self._package_to_repo_name(dep_name)
                # Extract version constraint
                constraint = dep.split(">=")[1] if ">=" in dep else "*"
                dependencies[repo_name] = constraint.split(";")[0].strip()
                break
    
    return dependencies

def _package_to_repo_name(self, package_name: str) -> str:
    """Convert package name to repo name (heuristic).
    
    Examples:
        provide-foundation -> provide-foundation
        pyvider-cty -> pyvider-cty
        pyvider -> pyvider
    """
    # For now, assume repo name == package name (common case)
    # Could be made more sophisticated with mapping
    return package_name.replace("_", "-")

def build_dependency_graph(self) -> "DependencyGraph":
    """Build complete dependency graph for workspace.
    
    Returns:
        DependencyGraph with all repo dependencies resolved
    """
    from wrknv.build.graph import DependencyGraph, DependencyEdge
    
    repos = self.discover_repos()
    nodes = {repo.name: RepoConfig(...) for repo in repos}
    edges = []
    
    for repo_info in repos:
        dependencies = self.detect_dependencies(repo_info)
        for target_repo, constraint in dependencies.items():
            if target_repo in nodes:  # Only add if target exists in workspace
                edge = DependencyEdge(
                    source=repo_info.name,
                    target=target_repo,
                    constraint=constraint
                )
                edges.append(edge)
    
    return DependencyGraph(nodes=nodes, edges=edges)
```

## 3. EXTENDING WorkspaceManager (workspace/manager.py)

### New Method: get_dependency_graph
```python
def get_dependency_graph(self) -> "DependencyGraph":
    """Get dependency graph for workspace.
    
    Returns:
        DependencyGraph with topological sort capability
    """
    config = self.load_config()
    if config is None:
        raise RuntimeError("No workspace configuration found")
    
    return self.discovery.build_dependency_graph()

def get_affected_repos(self, changed_repos: list[str]) -> set[str]:
    """Get all repos affected by changes to the specified repos.
    
    Args:
        changed_repos: List of repo names that have changed
    
    Returns:
        Set of repo names that are affected by the changes,
        including transitive dependents
    """
    graph = self.get_dependency_graph()
    affected = set(changed_repos)  # Include changed repos themselves
    
    # Find all repos that depend (directly or transitively) on changed repos
    to_process = list(changed_repos)
    while to_process:
        current = to_process.pop(0)
        # Find all repos that have current as dependency
        dependents = graph.get_dependents(current)
        for dependent in dependents:
            if dependent not in affected:
                affected.add(dependent)
                to_process.append(dependent)
    
    return affected

async def build_repos(
    self,
    repo_names: list[str] | None = None,
    parallel: bool = False,
    dry_run: bool = False,
    base_branch: str = "main"
) -> dict[str, "BuildResult"]:
    """Build repositories in dependency order.
    
    Args:
        repo_names: Repos to build (None = all, or specify list)
        parallel: Build in parallel when possible
        dry_run: Show what would be built without building
        base_branch: For detecting changed repos
    
    Returns:
        Dict mapping repo_name -> BuildResult
    """
    from wrknv.build.manager import BuildOrchestrator
    
    config = self.load_config()
    if config is None:
        raise RuntimeError("No workspace configuration found")
    
    # Determine repos to build
    if repo_names is None:
        # Build all repos
        to_build = [repo.name for repo in config.repos]
    else:
        # Build specified + their dependents
        graph = self.get_dependency_graph()
        to_build = list(graph.get_transitive_dependents(repo_names))
    
    # Create orchestrator and execute
    orchestrator = BuildOrchestrator(config, self.root, parallel=parallel)
    
    if dry_run:
        logger.info("DRY RUN: Would build repos in order:", repos=to_build)
        return {}
    
    results = await orchestrator.build(to_build)
    return results

def get_git_changes(self, base_branch: str = "main") -> dict[str, list[str]]:
    """Get git changes since base_branch and map to repos.
    
    Returns:
        Dict mapping repo_name -> [changed_files]
    """
    from wrknv.git.operations import get_changed_files
    
    # Get all changed files since base_branch
    changed_files = get_changed_files(self.root, base_branch)
    
    # Map to repos
    changes_by_repo = {}
    for file_path in changed_files:
        repo = self._find_repo_for_file(file_path)
        if repo:
            if repo.name not in changes_by_repo:
                changes_by_repo[repo.name] = []
            changes_by_repo[repo.name].append(file_path)
    
    return changes_by_repo

def _find_repo_for_file(self, file_path: str) -> RepoConfig | None:
    """Find which repo a file belongs to."""
    config = self.load_config()
    if not config:
        return None
    
    file_path = Path(file_path)
    for repo in config.repos:
        repo_path = repo.path if repo.path.is_absolute() else self.root / repo.path
        try:
            file_path.relative_to(repo_path)
            return repo  # Found it
        except ValueError:
            continue  # Not in this repo
    
    return None
```

## 4. NEW: DependencyGraph (build/graph.py)

```python
from attrs import define, field
from typing import Any
from pathlib import Path

@define
class DependencyEdge:
    """Single dependency relationship."""
    source: str  # repo name (depends on target)
    target: str  # repo name (required by source)
    constraint: str = "*"  # version constraint, "*" for workspace

@define
class DependencyGraph:
    """Directed graph of repo dependencies."""
    nodes: dict[str, "RepoConfig"]
    edges: list[DependencyEdge]
    
    def get_dependents(self, repo_name: str) -> list[str]:
        """Get repos that depend on this one.
        
        Returns list of repo names that have this repo as dependency.
        """
        return [edge.source for edge in self.edges if edge.target == repo_name]
    
    def get_dependencies(self, repo_name: str) -> list[str]:
        """Get repos that this one depends on."""
        return [edge.target for edge in self.edges if edge.source == repo_name]
    
    def get_transitive_dependents(self, repo_names: list[str]) -> list[str]:
        """Get all repos affected by changes to these repos (transitive)."""
        affected = set(repo_names)
        to_process = list(repo_names)
        
        while to_process:
            current = to_process.pop(0)
            dependents = self.get_dependents(current)
            for dep in dependents:
                if dep not in affected:
                    affected.add(dep)
                    to_process.append(dep)
        
        return sorted(affected)
    
    def topological_sort(self) -> list[str]:
        """Sort repos in build order (dependencies before dependents).
        
        Returns:
            List of repo names in build order
        """
        # Kahn's algorithm
        in_degree = {name: 0 for name in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] += 1
        
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Remove edges from current
            for edge in self.edges:
                if edge.source == current:
                    in_degree[edge.target] -= 1
                    if in_degree[edge.target] == 0:
                        queue.append(edge.target)
        
        if len(result) != len(self.nodes):
            # Cycle detected
            raise ValueError("Circular dependency detected in workspace")
        
        return result
```

## 5. NEW: BuildOrchestrator (build/manager.py)

```python
from typing import Any
from pathlib import Path
from attrs import define
from provide.foundation import logger
import asyncio

@define
class BuildResult:
    """Result of building a single repository."""
    repo_name: str
    success: bool
    duration_seconds: float
    output: str
    error: str | None = None
    artifacts: dict[str, Path] = field(factory=dict)
    timestamp: str = field(factory=lambda: datetime.now().isoformat())

class BuildOrchestrator:
    """Orchestrates building repos in dependency order."""
    
    def __init__(
        self,
        workspace_config: "WorkspaceConfig",
        workspace_root: Path,
        parallel: bool = False
    ):
        self.config = workspace_config
        self.root = workspace_root
        self.parallel = parallel
        self.graph = self._build_graph()
    
    def _build_graph(self) -> "DependencyGraph":
        """Build dependency graph from config."""
        from wrknv.build.graph import DependencyGraph
        from wrknv.workspace.discovery import WorkspaceDiscovery
        
        discovery = WorkspaceDiscovery(self.root)
        return discovery.build_dependency_graph()
    
    async def build(self, repo_names: list[str]) -> dict[str, BuildResult]:
        """Build specified repos in order.
        
        Args:
            repo_names: Repos to build (must be in order)
        
        Returns:
            Dict mapping repo_name -> BuildResult
        """
        results = {}
        build_order = self.graph.topological_sort()
        
        # Filter to requested repos, maintain order
        repos_to_build = [r for r in build_order if r in repo_names]
        
        if self.parallel:
            # Could use asyncio.gather for parallel builds of independent repos
            # But must respect dependency ordering
            results = await self._build_parallel(repos_to_build)
        else:
            for repo_name in repos_to_build:
                result = await self._build_single(repo_name)
                results[repo_name] = result
                if not result.success:
                    logger.error(f"Build failed for {repo_name}, stopping")
                    break
        
        return results
    
    async def _build_single(self, repo_name: str) -> BuildResult:
        """Build a single repository."""
        import time
        from wrknv.managers.factory import get_tool_manager
        
        start = time.time()
        repo_config = self.config.find_repo(repo_name)
        
        if not repo_config:
            return BuildResult(
                repo_name=repo_name,
                success=False,
                duration_seconds=0,
                output="",
                error=f"Repository {repo_name} not found in workspace"
            )
        
        repo_path = repo_config.path if repo_config.path.is_absolute() else self.root / repo_config.path
        
        try:
            # Get build command from config or detect from tool
            build_cmd = repo_config.build_config.get("build_command")
            if not build_cmd:
                # Auto-detect based on repo type
                build_cmd = self._get_default_build_command(repo_config)
            
            logger.info(f"Building {repo_name}: {build_cmd}")
            
            # Execute build (simplified - would use proper subprocess handling)
            from subprocess import run, PIPE
            result = await asyncio.to_thread(
                run,
                build_cmd,
                shell=True,
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start
            
            return BuildResult(
                repo_name=repo_name,
                success=result.returncode == 0,
                duration_seconds=duration,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )
        
        except Exception as e:
            duration = time.time() - start
            return BuildResult(
                repo_name=repo_name,
                success=False,
                duration_seconds=duration,
                output="",
                error=str(e)
            )
    
    def _get_default_build_command(self, repo: "RepoConfig") -> str:
        """Get default build command based on repo type."""
        # Would check repo.type and return appropriate command
        # e.g., "uv build" for Python packages, "go build" for Go, etc.
        match repo.type:
            case "foundation-based" | "pyvider-plugin" | "testkit":
                return "uv build"
            case "provider":
                return "uv build"
            case _:
                return "echo 'No build command defined'"
```

## 6. NEW CLI COMMANDS (cli/commands/workspace.py - additions)

```python
@register_command("workspace.build", description="Build repositories in dependency order")
def build_command(
    repos: list[str] | None = None,
    parallel: bool = False,
    dry_run: bool = False,
    base_branch: str = "main"
) -> None:
    """Build repositories respecting dependencies.
    
    Args:
        repos: Specific repos to build (comma-separated)
        parallel: Build independent repos in parallel
        dry_run: Show what would be built
        base_branch: Base branch for change detection
    """
    manager = WorkspaceManager()
    
    repo_list = None
    if repos:
        repo_list = repos.split(",") if isinstance(repos, str) else repos
    
    try:
        import asyncio
        results = asyncio.run(
            manager.build_repos(
                repo_names=repo_list,
                parallel=parallel,
                dry_run=dry_run,
                base_branch=base_branch
            )
        )
        
        # Report results
        for repo_name, result in results.items():
            if result.success:
                logger.info(f"✓ {repo_name} ({result.duration_seconds:.1f}s)")
            else:
                logger.error(f"✗ {repo_name}: {result.error}")
    
    except Exception as e:
        logger.error("Build failed", error=str(e))
        raise

@register_command("workspace.affected", description="Show repos affected by changes")
def affected_command(base_branch: str = "main") -> None:
    """Show which repos are affected by changes since base_branch."""
    manager = WorkspaceManager()
    
    try:
        changes = manager.get_git_changes(base_branch)
        affected = set()
        
        for repo_name in changes:
            repo_affected = manager.get_affected_repos([repo_name])
            affected.update(repo_affected)
        
        logger.info(f"Affected repos: {', '.join(sorted(affected))}")
        return affected
    
    except Exception as e:
        logger.error("Failed to detect affected repos", error=str(e))
        raise

@register_command("workspace.graph", description="Display dependency graph")
def graph_command(format: str = "text") -> None:
    """Show workspace dependency graph.
    
    Args:
        format: Output format (text, json, dot)
    """
    manager = WorkspaceManager()
    
    try:
        graph = manager.get_dependency_graph()
        
        if format == "text":
            _print_graph_text(graph)
        elif format == "json":
            _print_graph_json(graph)
        elif format == "dot":
            _print_graph_dot(graph)
    
    except Exception as e:
        logger.error("Failed to display graph", error=str(e))
        raise

def _print_graph_text(graph: "DependencyGraph") -> None:
    """Print dependency graph as text tree."""
    try:
        order = graph.topological_sort()
        logger.info("Build order (dependencies before dependents):")
        for i, repo_name in enumerate(order, 1):
            deps = graph.get_dependencies(repo_name)
            if deps:
                logger.info(f"  {i}. {repo_name} -> {', '.join(deps)}")
            else:
                logger.info(f"  {i}. {repo_name}")
    except ValueError as e:
        logger.error(f"Circular dependency: {e}")
```

## 7. GIT OPERATIONS (build/git/operations.py - new)

```python
from pathlib import Path
from provide.foundation.process import run

def get_changed_files(root: Path, base_branch: str = "main") -> list[str]:
    """Get files changed since base_branch.
    
    Args:
        root: Workspace root
        base_branch: Branch to compare against
    
    Returns:
        List of changed file paths
    """
    try:
        result = run(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split("\n") if result.stdout else []
    except Exception as e:
        logger.warning(f"Failed to get git changes: {e}")
        return []
```

## Key Implementation Order

1. **Phase 1**: Add fields to RepoConfig (schema.py)
2. **Phase 2**: Implement detect_dependencies() in WorkspaceDiscovery
3. **Phase 3**: Create build/graph.py with DependencyGraph
4. **Phase 4**: Add get_dependency_graph() to WorkspaceManager
5. **Phase 5**: Add get_affected_repos() to WorkspaceManager
6. **Phase 6**: Create build/manager.py with BuildOrchestrator
7. **Phase 7**: Add CLI commands (workspace.py)

## Testing These Features

```python
# tests/workspace/test_build_orchestration.py

import pytest
from wrknv.workspace.manager import WorkspaceManager
from wrknv.build.graph import DependencyGraph

@pytest.mark.workspace
def test_dependency_detection(workspace_root):
    """Test that dependencies are detected from pyproject.toml."""
    manager = WorkspaceManager(workspace_root)
    graph = manager.get_dependency_graph()
    
    # Example: repo B depends on repo A
    assert "a" in graph.get_dependencies("b")

@pytest.mark.workspace
def test_topological_sort(workspace_root):
    """Test that repos sort in buildable order."""
    manager = WorkspaceManager(workspace_root)
    graph = manager.get_dependency_graph()
    
    order = graph.topological_sort()
    # A should come before B if B depends on A
    assert order.index("a") < order.index("b")

@pytest.mark.workspace
async def test_build_execution(workspace_root):
    """Test building repos."""
    manager = WorkspaceManager(workspace_root)
    results = await manager.build_repos(["a", "b"], parallel=False)
    
    assert results["a"].success
    assert results["b"].success
```

