# Command Loading Refactor Plan

## Problem Statement

Current command registration uses Python decorators (`@register_command`) that execute at module import time. This causes issues in tests:

1. Commands are registered when modules are imported
2. Python caches modules in `sys.modules` after first import
3. Subsequent calls to `create_cli()` don't re-execute decorators
4. Attempting to re-register causes `AlreadyExistsError` in hub registry
5. Tests must share a single CLI instance (less isolation) or force module reloading (fragile)

## Current Architecture

```python
# src/wrknv/cli/commands/gitignore.py
from provide.foundation.hub import register_command

@register_command("gitignore", group=True)  # ← Executes at import time
def gitignore_group():
    pass

# src/wrknv/cli/hub_cli.py
def load_commands():
    # Import all command modules - triggers decorator execution
    from wrknv.cli.commands import config, gitignore, setup  # etc

def create_cli():
    load_commands()  # ← First call registers, subsequent calls do nothing
    return hub.create_cli_app()
```

## Proposed Solution: Lazy/Dynamic Command Registration

### Option A: Registration Function Pattern

Replace decorators with explicit registration functions that can be called multiple times safely:

```python
# src/wrknv/cli/commands/gitignore.py
import click
from provide.foundation.hub import get_hub

def create_gitignore_commands():
    """Create and register gitignore commands."""
    @click.group()
    def gitignore_group():
        """Manage .gitignore files"""
        pass

    @gitignore_group.command("build")
    def gitignore_build():
        """Build .gitignore from templates"""
        pass

    return {
        "gitignore": gitignore_group,
    }

def register_commands(replace=False):
    """Register gitignore commands with hub."""
    commands = create_gitignore_commands()
    hub = get_hub()

    for name, cmd in commands.items():
        hub._component_registry.register(
            name=name,
            value=cmd,
            dimension="command",
            replace=replace,  # ← Allow override in tests
        )
```

**Usage:**
```python
# src/wrknv/cli/hub_cli.py
def load_commands(replace=False):
    from wrknv.cli.commands import gitignore, config, setup

    gitignore.register_commands(replace=replace)
    config.register_commands(replace=replace)
    setup.register_commands(replace=replace)

def create_cli(replace_commands=False):
    load_commands(replace=replace_commands)
    return hub.create_cli_app()

# In tests
cli = create_cli(replace_commands=True)  # ← Safe to call multiple times
```

### Option B: Command Registry Class

Create a command registry that manages registration lifecycle:

```python
# src/wrknv/cli/command_registry.py
class CommandRegistry:
    def __init__(self):
        self._factories = {}
        self._registered = set()

    def register_factory(self, name, factory_fn):
        """Register a command factory function."""
        self._factories[name] = factory_fn

    def load_into_hub(self, hub, replace=False):
        """Load all commands into hub registry."""
        for name, factory in self._factories.items():
            if name in self._registered and not replace:
                continue

            command = factory()
            hub._component_registry.register(
                name=name,
                value=command,
                dimension="command",
                replace=replace,
            )
            self._registered.add(name)

    def reset(self):
        """Clear registration state (for tests)."""
        self._registered.clear()

# Global registry
_command_registry = CommandRegistry()

# In command modules
def register_gitignore():
    def _factory():
        @click.group()
        def gitignore():
            """Manage .gitignore files"""
            pass
        return gitignore

    _command_registry.register_factory("gitignore", _factory)

# Auto-register on import
register_gitignore()
```

### Option C: Conditional Decorator (Minimal Change)

Add logic to decorators to check if already registered:

```python
# src/wrknv/cli/decorators.py
def smart_register_command(name_or_func=None, **kwargs):
    """Decorator that safely handles re-registration."""
    def decorator(func):
        hub = get_hub()

        # Check if already registered
        try:
            existing = hub._component_registry.get(name, "command")
            if existing:
                # Already registered, skip
                return func
        except:
            pass

        # Not registered, proceed
        return register_command(name, **kwargs)(func)

    return decorator

# Usage in command modules
@smart_register_command("gitignore", group=True)
def gitignore_group():
    pass
```

## Recommendation

**Option A (Registration Function Pattern)** is recommended because:

1. ✅ Explicit control over registration timing
2. ✅ Clean separation of command creation vs. registration
3. ✅ Easy to test command creation independently
4. ✅ Supports `replace=True` for tests without changing all decorators
5. ✅ No magic/hidden behavior
6. ✅ Aligns with dependency injection principles

**Migration Path:**

1. Create new `register_commands()` function in one command module (e.g., gitignore)
2. Update `load_commands()` to call it
3. Test with gitignore commands
4. Migrate remaining commands incrementally
5. Deprecate decorator pattern (or keep for simple cases)

## Implementation Checklist

- [ ] Create `src/wrknv/cli/command_loader.py` with base registration utilities
- [ ] Refactor `gitignore.py` to use registration function pattern
- [ ] Update `hub_cli.py` to support `replace_commands` parameter
- [ ] Add tests for command registration/re-registration
- [ ] Migrate remaining command modules
- [ ] Update test fixtures to use `create_cli(replace_commands=True)`
- [ ] Document pattern in `CLAUDE.md`

## Benefits

- **Testability**: Tests can safely create multiple CLI instances
- **Flexibility**: Commands can be registered/unregistered dynamically
- **Clarity**: Explicit registration vs. implicit decorator magic
- **Control**: Application code controls when registration happens
- **Debugging**: Easier to trace command loading issues

## Alternatives Considered

- ❌ **Module reloading**: Fragile, breaks if modules have side effects
- ❌ **Single global CLI**: Reduces test isolation
- ❌ **`replace=True` everywhere**: Changes all decorators, no semantic improvement
- ❌ **Registry clearing**: Doesn't solve root cause (module caching)
