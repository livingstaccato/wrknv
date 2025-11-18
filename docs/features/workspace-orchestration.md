# Workspace Task Orchestration

Run tasks across multiple repositories in your workspace with streaming output and comprehensive error handling.

## Overview

The workspace task orchestration feature allows you to execute tasks defined in `wrknv.toml` across all repositories in your workspace with a single command. This is particularly useful for:

- Running tests across your entire ecosystem
- Performing code quality checks on multiple packages
- Building all packages in a monorepo-style workflow
- Running any task consistently across related projects

## Quick Start

```bash
# Run tests across all repositories in workspace
we workspace run test

# Run typecheck on specific packages
we workspace run typecheck --repos="pyvider-*"

# Parallel execution
we workspace run test --parallel

# Stop on first failure
we workspace run test --fail-fast
```

## Command Syntax

```bash
we workspace run <task> [OPTIONS]
```

### Arguments

- **`task`** (required): Name of the task to run (e.g., `test`, `typecheck`, `build`)
  - Must exist in each repository's `wrknv.toml`
  - Repositories without the task are skipped automatically

### Options

- **`--repos=PATTERN`**: Glob pattern to filter repositories
  - Default: All repositories in workspace
  - Examples: `"pyvider-*"`, `"terraform-provider-*"`, `"wrknv"`
  - Supports standard glob patterns (`*`, `?`, `[]`)

- **`--parallel`**: Run tasks in parallel across repositories
  - Default: Sequential execution
  - Sequential provides clearer output ordering
  - Parallel is faster for independent tasks

- **`--fail-fast`**: Stop on first failure (sequential mode only)
  - Default: Continue on error (collect all results)
  - Useful for CI/CD pipelines
  - Ignored in parallel mode

## Execution Modes

### Sequential Execution (Default)

Runs tasks one repository at a time, with clear output separation:

```bash
we workspace run test
```

**Benefits:**
- Clear, ordered output per repository
- Easy to debug failures
- Fail-fast support
- Real-time streaming output

**Output Format:**
```
================================================================================
▶ Running 'test' in pyvider
================================================================================
[test output from pyvider]

✓ Task 'test' succeeded in pyvider (2.1s)

================================================================================
▶ Running 'test' in pyvider-cty
================================================================================
[test output from pyvider-cty]

✓ Task 'test' succeeded in pyvider-cty (1.8s)

================================================================================
📊 Workspace Task Summary
================================================================================
Task: test
Total repos: 2
✅ Succeeded: 2
❌ Failed: 0
⏭️  Skipped: 0
⏱️  Duration: 4.2s

✅ All repositories succeeded!
```

### Parallel Execution

Runs tasks concurrently across all repositories:

```bash
we workspace run test --parallel
```

**Benefits:**
- Faster execution
- Efficient use of system resources
- Good for independent tasks

**Considerations:**
- Output may be interleaved
- No fail-fast support (all repos run to completion)
- Harder to debug failures in real-time

## Repository Discovery

### Auto-Discovery

By default, the workspace orchestrator discovers all Git repositories with `pyproject.toml` files in the parent directory of your current location:

```bash
# From /path/to/workspace/wrknv
we workspace run test
# Discovers all repos in /path/to/workspace/
```

### Pattern-Based Filtering

Filter repositories using glob patterns:

```bash
# Only pyvider-* packages
we workspace run test --repos="pyvider-*"

# Specific repository
we workspace run typecheck --repos="wrknv"

# Multiple patterns (use shell expansion)
we workspace run lint --repos="pyvider-{cty,hcl,rpcplugin}"

# Terraform providers only
we workspace run build --repos="terraform-provider-*"
```

## Task Requirements

For a task to run in a repository:

1. **Repository must have:**
   - `.git` directory (Git repository)
   - `pyproject.toml` file (Python project)

2. **Task must be defined in `wrknv.toml`:**
   ```toml
   [tasks]
   test = "pytest"
   typecheck = "mypy src/"
   ```

3. **If task is missing:**
   - Repository is automatically skipped
   - Counted in "Skipped" metric
   - Warning logged but not treated as failure

## Environment Isolation

Each repository executes in its own isolated environment:

- **Independent virtual environments**: Each repo uses its own `workenv/` or `.venv/`
- **Auto-detection**: Environment execution mode detected per-repo
- **Editable installs**: Automatically detected and handled correctly
- **PATH management**: Virtual environment bins properly prepended
- **No cross-contamination**: Dependencies isolated between projects

## Error Handling

### Continue-on-Error (Default)

By default, all repositories are tested even if some fail:

```bash
we workspace run test
```

**Summary includes:**
- Total repositories processed
- Succeeded count
- Failed count with repo names and exit codes
- Skipped count
- Total duration

**Exit Code:**
- `0` if all repositories succeeded
- `1` if any repository failed

### Fail-Fast Mode

Stop on first failure (sequential mode only):

```bash
we workspace run test --fail-fast
```

**Behavior:**
- Stops immediately when any task fails
- Remaining repositories are not processed
- Faster feedback in CI/CD
- Only works in sequential mode (ignored with `--parallel`)

## Real-World Examples

### Development Workflow

```bash
# Format all code
we workspace run format

# Check formatting without changes
we workspace run format.check

# Lint all projects
we workspace run lint

# Type check everything
we workspace run typecheck

# Run all quality checks
we workspace run quality
```

### Testing Workflow

```bash
# Run unit tests everywhere
we workspace run test.unit

# Run all tests with coverage
we workspace run test.coverage

# Parallel test execution for speed
we workspace run test --parallel

# Test specific package family
we workspace run test --repos="pyvider-*"
```

### CI/CD Pipeline

```bash
# Quality gate (fail-fast for quick feedback)
we workspace run quality --fail-fast

# Comprehensive test suite
we workspace run test.coverage

# Build all packages
we workspace run build --parallel

# Verify installations
we workspace run pkg.install --fail-fast
```

### Package-Specific Operations

```bash
# Update all pyvider plugins
we workspace run pkg.lock --repos="pyvider-*"

# Build terraform providers
we workspace run build --repos="terraform-provider-*"

# Run integration tests on core packages
we workspace run test.integration --repos="{wrknv,pyvider,flavorpack}"
```

## Performance Considerations

### When to Use Sequential

- Debugging failures
- Clear output required
- Tasks modify shared resources
- Fail-fast behavior needed

### When to Use Parallel

- Independent tasks
- Many repositories
- CI/CD pipelines (when fail-fast not needed)
- Tasks are I/O bound or slow

### Optimization Tips

1. **Use specific filters**: Don't run tasks on repos that don't need them
   ```bash
   # Bad: runs on all repos, many skipped
   we workspace run test

   # Good: only relevant repos
   we workspace run test --repos="pyvider-*"
   ```

2. **Combine with parallel for speed**:
   ```bash
   we workspace run typecheck --repos="pyvider-*" --parallel
   ```

3. **Use fail-fast in CI for quick feedback**:
   ```bash
   we workspace run quality --fail-fast
   ```

## Integration with Existing Features

### Task Auto-Detection

Environment auto-detection works per-repository:
- Each repo's environment is detected independently
- `uv run` prefix added automatically when needed
- Editable installs detected and handled correctly

### Process Streaming

All task output is streamed in real-time:
- See progress as it happens
- Process titles show current repo
- Same streaming behavior as `we run <task>`

### Task Execution Environment

Respects all task configuration:
- `timeout`: Per-task timeouts
- `stream_output`: Streaming preferences
- `execution_mode`: Environment detection mode
- `env`: Task-specific environment variables

## Troubleshooting

### No Repositories Found

```
⚠️ No repositories found
```

**Solutions:**
- Ensure you're in a workspace directory
- Check that sibling directories have `.git` and `pyproject.toml`
- Verify `--repos` pattern is correct
- Use `we workspace status` to see discovered repos

### Task Not Found in Repository

```
⚠️ Task 'test' not found in pyvider-cty
```

**Solutions:**
- Add task to repository's `wrknv.toml`
- Use different filter to exclude repos without task
- Task will be skipped automatically (not an error)

### All Tasks Failing

```
❌ Task 'test' failed in wrknv (exit code: 1)
❌ Task 'test' failed in pyvider (exit code: 1)
```

**Solutions:**
- Check task works in individual repos: `we run test`
- Verify environment is set up: `we setup`
- Check for dependency issues: `uv sync`
- Review stderr output for specific errors

### Parallel Execution Issues

If parallel execution causes problems:
- Use sequential mode instead
- Tasks may have shared resource conflicts
- Output may be too interleaved to debug

## See Also

- [Task Runner](task-runner.md) - Core task execution system
- [Task System](task-system.md) - Task configuration and structure
- [Configuration Reference](../reference/configuration.md) - wrknv.toml schema
