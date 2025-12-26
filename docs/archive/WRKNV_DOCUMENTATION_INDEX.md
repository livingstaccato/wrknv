# wrknv Build Orchestration - Complete Documentation Index

This directory contains comprehensive analysis and design documentation for enhancing wrknv with build orchestration capabilities. These documents were created through systematic investigation of the wrknv codebase and are designed to guide implementation of dependency graph tracking, affected package detection, and distributed build orchestration.

## Documents Overview

### 1. WRKNV_BUILD_ORCHESTRATION_ANALYSIS.md (21 KB, 693 lines)
**The authoritative deep-dive into wrknv architecture and build orchestration design**

Contents:
- Executive summary of wrknv's purpose and architecture
- Complete overview of 11 core architectural components
- Current workspace discovery and analysis capabilities
- 6 key extension points for build orchestration
- 4 existing design patterns available for leverage
- Git integration points and pyproject.toml parsing
- 7 design patterns for extension (data models, modules, commands)
- 4-phase implementation roadmap
- 9 critical design decisions with recommendations
- Integration with existing systems
- Why build orchestration fits naturally into wrknv

**Best for**: Understanding the complete system, design decisions, integration strategies

### 2. WRKNV_QUICK_REFERENCE.md (9.2 KB, 273 lines)
**Quick lookup guide for key components and patterns**

Contents:
- Visual component map (directory tree with descriptions)
- 4 data flow diagrams (initialization, config loading, env generation, tools)
- Configuration hierarchy
- Command registration pattern with benefits
- Key interfaces (BaseToolManager, WorkspaceManager, WorkspaceDiscovery)
- Repository type detection priority
- Build orchestration extension points (gaps and where to add features)
- Supported tools registry
- Important constraints

**Best for**: Quick reference during development, understanding component relationships

### 3. WRKNV_CODE_EXAMPLES.md (22 KB, 685 lines)
**Concrete implementation code with examples**

Contents:
- Critical file paths for build orchestration
- Step-by-step code for extending RepoConfig
- Implementation of detect_dependencies() method
- WorkspaceManager extensions (get_dependency_graph, get_affected_repos, build_repos)
- Complete DependencyGraph class implementation
- BuildOrchestrator class with asyncio support
- New CLI command examples (build, affected, graph)
- Git operations module example
- Key implementation order (7 phases)
- Testing examples with pytest

**Best for**: Actual implementation, copy-paste starting points, understanding code patterns

## How to Use These Documents

### For Design Phase
1. Start with WRKNV_BUILD_ORCHESTRATION_ANALYSIS.md sections 1-3
2. Review critical design decisions (section 9)
3. Understand integration points (section 10)

### For Architecture Review
1. Read WRKNV_QUICK_REFERENCE.md for overview
2. Reference specific component details in ANALYSIS.md
3. Use CODE_EXAMPLES.md for interface understanding

### For Implementation
1. Follow the 7-phase roadmap in ANALYSIS.md section 8
2. Use QUICK_REFERENCE.md as checklist
3. Use CODE_EXAMPLES.md for actual coding
4. Reference QUICK_REFERENCE.md for testing locations

### For Team Communication
1. Use QUICK_REFERENCE.md component map in presentations
2. Share ANALYSIS.md critical decisions section
3. Provide CODE_EXAMPLES.md to developers

## Key Findings Summary

### wrknv Architecture Strengths
1. **Hub Pattern CLI**: Modular command registration, not monolithic
2. **Manager Pattern**: All tools use abstract base class with implementations
3. **Schema-Driven**: Type-safe configuration with validators via attrs
4. **Async-First**: Heavy use of async for I/O operations
5. **Workspace-Aware**: Already has workspace discovery and sync capability

### Build Orchestration Gaps (Currently)
1. No dependency graph tracking between repos
2. No affected package detection based on git changes
3. No build command orchestration
4. No result aggregation across repos

### Natural Extension Points
1. **RepoConfig schema** - Add dependency fields
2. **WorkspaceDiscovery** - Extract dependencies from pyproject.toml
3. **WorkspaceManager** - Add build coordination methods
4. **BaseToolManager** - Add build capability interface
5. **CLI commands** - Register new workspace.build commands
6. **New build/ module** - DependencyGraph, BuildOrchestrator, affected detection

### Recommended Approach
- **Hybrid dependency tracking**: Auto-detect from pyproject.toml, allow override
- **Centralized orchestrator**: Single BuildManager coordinates all tools
- **Async execution**: Match existing wrknv patterns for parallel builds
- **Git-based affected detection**: Use git diff to identify changed files

## Critical Code Locations

```
Primary files to modify:
├── src/wrknv/workspace/schema.py ......... Add dependency fields to RepoConfig
├── src/wrknv/workspace/discovery.py ..... Implement detect_dependencies()
├── src/wrknv/workspace/manager.py ....... Add build orchestration methods
├── src/wrknv/managers/base.py ........... Add build capability interface
├── src/wrknv/cli/commands/workspace.py .. Register new build commands
└── (NEW) src/wrknv/build/ ............... New module for orchestration
    ├── graph.py ......................... DependencyGraph implementation
    ├── manager.py ....................... BuildOrchestrator
    └── affected.py ...................... Affected repo detection
```

## Phase Implementation Guide

**Phase 1** (Foundation): Add schema fields and dependency detection
**Phase 2** (Affected): Implement affected repo detection with git
**Phase 3** (Build): Create build execution orchestrator
**Phase 4** (CLI): Add commands and integrate with existing systems

## Testing Strategy

- Tests mirror src/ structure in tests/
- Use pytest with markers (workspace, integration, etc.)
- Test dependency detection with fixture workspace
- Test build orchestration with mocked builders
- Integration tests for full pipeline

## Important Constraints

- Python 3.11+ only (modern type hints, native TOML)
- Async-first for I/O operations
- No print statements (use logging)
- No hardcoded defaults
- Use Path.cwd() not os.getcwd()
- Configuration must be explicit

## Related Documentation

- wrknv CLAUDE.md (project instructions)
- provide.foundation patterns (hub, logging, configuration)
- pyproject.toml standards (uv, workspace sources)

## Document Maintenance

These documents were generated on: 2025-11-10

If wrknv architecture changes significantly:
1. Update ANALYSIS.md with new components
2. Update QUICK_REFERENCE.md component map
3. Verify CODE_EXAMPLES.md still compiles
4. Check critical file paths are still valid

## Quick Navigation

| Task | Document | Section |
|------|----------|---------|
| Understand overall architecture | ANALYSIS.md | Section 1 |
| Find a specific component | QUICK_REFERENCE.md | Component Map |
| Learn about extension points | ANALYSIS.md | Section 3 |
| See code examples | CODE_EXAMPLES.md | Sections 1-7 |
| Understand design decisions | ANALYSIS.md | Section 9 |
| Check implementation order | ANALYSIS.md | Section 8 |
| Find a test location | QUICK_REFERENCE.md | Testing & Integration |

---

Total documentation: 1,651 lines across 3 comprehensive files
Generated with systematic codebase investigation and analysis
