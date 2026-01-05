# we CLI Reference

Complete command-line reference for the `we` task runner and work environment manager.

## Overview

`we` is the command-line interface for wrknv, providing:

- **Task execution** with automatic detection
- **Tool management** for Terraform, OpenTofu, Go, UV, and more
- **Environment generation** with cross-platform scripts
- **Container orchestration** for development environments

## Global Options

Available for all commands:

```bash
--help, -h              Show help message
--version, -v           Show version information
```

## Task Commands

### Auto-Detected Task Execution

Run tasks directly without the `run` subcommand:

```bash
we TASK [ARGS...]
```

**Examples:**
```bash
we test                      # Run test task
we test unit                 # Run nested test.unit task
we test --verbose            # Pass arguments
we lint --fix                # Run lint task with --fix
we build docker production   # Multi-level nested task
```

**How it works:**
- Checks if first argument is a built-in command
- If not, tries to resolve as a task name
- Uses greedy matching for nested tasks
- Falls back to normal CLI if task not found

### we run

Explicitly run a task (backward compatibility):

```bash
we run TASK [OPTIONS]
```

**Options:**
- `--dry-run` - Show what would be executed without running
- `--info` - Show task information without running
- `--env KEY=VALUE` - Set environment variables (repeatable)

**Examples:**
```bash
we run test
we run test --dry-run
we run test --env DEBUG=1 --env LOG_LEVEL=info
we run build --info
```

### we tasks

List all available tasks:

```bash
we tasks [OPTIONS]
```

**Options:**
- `--verbose` - Show detailed task information including commands

**Examples:**
```bash
we tasks                     # List all tasks
we tasks --verbose           # Show task details
```

**Output Format:**

Normal mode:
```
Available tasks:

test
├── unit
├── integration
└── e2e

Flat tasks:
  • lint  Check code quality
  • format  Format code
```

Verbose mode adds command details:
```
test
├── unit
│   Command: pytest tests/unit/
├── integration
│   Command: pytest tests/integration/
```

## Environment Commands

### we setup

Initialize work environment:

```bash
we setup [OPTIONS]
```

**Options:**
- `--init` - Initialize new wrknv.toml configuration
- `--profile PROFILE` - Use specific tool profile
- `--force` - Overwrite existing files

**Examples:**
```bash
we setup                     # Initialize with default profile
we setup --init              # Create new wrknv.toml
we setup --profile dev       # Use dev profile
we setup --force             # Overwrite existing env scripts
```

### we config

Manage configuration:

```bash
we config [COMMAND]
```

**Subcommands:**
- `show` - Display current configuration
- `validate` - Validate wrknv.toml syntax
- `init` - Initialize new configuration

**Examples:**
```bash
we config show               # Show current config
we config validate           # Validate wrknv.toml
we config init               # Create new wrknv.toml
```

## Tool Commands

### we tools

Manage development tools:

```bash
we tools [COMMAND]
```

**Subcommands:**
- `list` - List configured tools and versions
- `install` - Install specific tool versions
- `upgrade` - Upgrade tools to latest allowed versions
- `verify` - Verify installed tools

**Examples:**
```bash
we tools list                # Show all configured tools
we tools install terraform   # Install Terraform
we tools install --all       # Install all tools
we tools upgrade terraform   # Upgrade to latest allowed version
we tools verify              # Verify installations
```

### we terraform

Manage Terraform versions:

```bash
we terraform [COMMAND]
```

**Commands:**
- `list` - List available/installed versions
- `install VERSION` - Install specific version
- `use VERSION` - Set active version

**Examples:**
```bash
we terraform list
we terraform install 1.6.0
we terraform use 1.6.0
```

Similar commands exist for:
- `we tofu` - OpenTofu management
- `we go` - Go management
- `we uv` - UV management

## Container Commands

### we container

Manage containerized development environments:

```bash
we container [COMMAND]
```

**Subcommands:**
- `build` - Build development container
- `start` - Start container
- `stop` - Stop container
- `exec` - Execute command in container
- `shell` - Open interactive shell

**Examples:**
```bash
we container build           # Build dev container
we container start           # Start container
we container exec -- pytest  # Run command in container
we container shell           # Interactive shell
we container stop            # Stop container
```

## Workspace Commands

### we workspace

Manage workspace operations:

```bash
we workspace [COMMAND]
```

**Subcommands:**
- `sync` - Sync workspace dependencies
- `list` - List workspace packages
- `run` - Run task across all packages

**Examples:**
```bash
we workspace sync            # Sync all packages
we workspace list            # List packages
we workspace run test        # Run test in all packages
```

## Utility Commands

### we doctor

Diagnose environment issues:

```bash
we doctor
```

Checks:
- Configuration validity
- Tool installations
- Path setup
- Container runtime availability

### we profile

Manage tool profiles:

```bash
we profile [COMMAND]
```

**Commands:**
- `list` - List available profiles
- `show PROFILE` - Show profile details
- `use PROFILE` - Activate profile

**Examples:**
```bash
we profile list
we profile show dev
we profile use production
```

### we secrets

Manage environment secrets:

```bash
we secrets [COMMAND]
```

**Commands:**
- `list` - List configured secrets (masked)
- `set KEY VALUE` - Set secret value
- `unset KEY` - Remove secret
- `encrypt` - Encrypt secrets file
- `decrypt` - Decrypt secrets file

**Examples:**
```bash
we secrets list
we secrets set API_KEY abc123
we secrets unset OLD_KEY
```

### we gitignore

Generate gitignore entries:

```bash
we gitignore [OPTIONS]
```

**Options:**
- `--update` - Update existing .gitignore

**Examples:**
```bash
we gitignore                 # Show recommended entries
we gitignore --update        # Add to .gitignore
```

### we lock

Manage dependency locks:

```bash
we lock [COMMAND]
```

**Commands:**
- `generate` - Generate lock file
- `verify` - Verify lock file
- `upgrade` - Upgrade locked dependencies

## Task Execution Details

### Resolution Order

When you run `we test unit fast`:

1. **Exact match**: Look for `test.unit.fast` task
2. **Default task**: Check `test.unit._default`
3. **Parent + args**: Try `test.unit` with args `["fast"]`
4. **Default parent**: Check `test._default` with args `["unit", "fast"]`
5. **Grandparent + args**: Try `test` with args `["unit", "fast"]`

### Built-in Commands

These commands bypass task resolution:

- `config`, `setup`, `run`, `tasks`
- `tools`, `terraform`, `tofu`, `go`, `uv`
- `container`, `workspace`, `doctor`
- `profile`, `secrets`, `gitignore`, `lock`
- `--help`, `-h`, `--version`, `-v`

### Environment Variable Priority

1. Runtime flags: `--env KEY=VALUE`
2. Task definition: `[tasks.name] env = {...}`
3. Executor environment
4. System environment

### Exit Codes

- `0` - Success
- `1` - General failure
- Task exit code - For task execution failures

## Configuration Files

### wrknv.toml

Main configuration file. See [Configuration Reference](../reference/configuration.md).

**Location:**
- Project root: `./wrknv.toml`
- User home: `~/.wrknv/config.toml` (global defaults)

### Environment Scripts

Generated by `we setup`:

- `env.sh` - Bash/Zsh environment script
- `env.ps1` - PowerShell environment script

**Usage:**
```bash
source env.sh              # Bash/Zsh
. ./env.ps1                # PowerShell
```

## Shell Integration

### Bash/Zsh

Add to `.bashrc` or `.zshrc`:

```bash
# Load wrknv environment if present
if [ -f "./env.sh" ]; then
    source ./env.sh
fi

# Auto-complete for we command
eval "$(we --completion bash)"  # or zsh
```

### PowerShell

Add to profile:

```powershell
# Load wrknv environment if present
if (Test-Path ".\env.ps1") {
    . .\env.ps1
}
```

## Examples

### Common Workflows

**Development workflow:**
```bash
we setup                     # Initialize environment
we test                      # Run tests
we lint                      # Check code quality
we build                     # Build project
```

**CI/CD workflow:**
```bash
we quality                   # Run quality checks
we test unit                 # Unit tests
we test integration          # Integration tests
we build                     # Build artifacts
we deploy staging            # Deploy to staging
```

**Tool management:**
```bash
we tools list                # See what's configured
we tools install --all       # Install all tools
we terraform use 1.6.0       # Switch Terraform version
```

**Container development:**
```bash
we container build           # Build dev container
we container start           # Start container
we container exec -- we test # Run tests in container
we container shell           # Interactive debugging
we container stop            # Clean up
```

### Task Composition

**Simple tasks:**
```bash
we test                      # Single task
we lint --fix                # Task with args
```

**Composite workflows:**
```bash
we quality                   # Runs: lint, typecheck, format
we ci                        # Runs: quality, test, build
```

**Nested organization:**
```bash
we test unit                 # Specific test suite
we test unit fast            # Quick unit tests
we run docs.build            # Build documentation
we run docs.serve            # Serve docs locally
```

## Troubleshooting

### Command Not Found

If `we` command not found:

```bash
# Install wrknv
uv tool install wrknv

# Verify installation
which we
we --version
```

### Task Not Found

If `we test` fails:

1. Check task exists: `we tasks`
2. Verify `wrknv.toml` syntax: `we config validate`
3. Try explicit: `we run test`
4. Check for typos in task name

### Environment Issues

If tools not found:

1. Run setup: `we setup`
2. Source environment: `source env.sh`
3. Verify tools: `we doctor`
4. Check tool installation: `we tools list`

### Container Issues

If container commands fail:

1. Check Docker running: `docker ps`
2. Verify runtime: `we doctor`
3. Check container config in `wrknv.toml`

## See Also

- [Task System](task-system.md) - Task definition and execution
- [Configuration Reference](../reference/configuration.md) - Configuration schema
- [Examples](../../examples/) - Sample projects and workflows
