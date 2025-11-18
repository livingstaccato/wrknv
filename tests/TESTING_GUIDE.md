# Testing Guide for wrknv

## Testing attrs-based Classes

This project uses [attrs](https://www.attrs.org/) for defining data classes. attrs provides immutability, validation, and automatic method generation, but it requires different testing patterns than standard Python classes.

### The Problem

attrs classes are **immutable by default**. You cannot mock individual methods on an attrs instance:

```python
# ❌ DOESN'T WORK - attrs objects are read-only
manager = ContainerManager(config)
manager.runtime.is_available = Mock(return_value=True)  # AttributeError!
```

### The Solution

**Replace entire attrs objects with mocks** instead of mocking individual methods:

```python
# ✅ WORKS - replace the whole object
from tests.utils.fixtures import create_mock_runtime

manager = ContainerManager(config)
manager.runtime = create_mock_runtime(available=True)  # Works!
```

## Common Patterns

### Pattern 1: Using Mock Factories

We provide mock factories for all attrs-based classes in `tests/utils/fixtures.py`:

```python
# Import from conftest (imports are re-exported there)
from tests.conftest import (
    create_mock_runtime,
    create_mock_lifecycle,
    create_mock_exec,
    create_mock_logs,
    create_mock_builder,
    create_mock_volumes,
    create_mock_storage,
    create_mock_manager,  # Creates manager with all mocks
)

# Or import directly from fixtures
from tests.utils.fixtures import create_mock_runtime

def test_example():
    # Create a mock runtime
    runtime = create_mock_runtime(available=True)

    # Create manager and replace runtime
    manager = ContainerManager(config)
    manager.runtime = runtime

    # Now you can control runtime behavior
    assert manager.check_docker() == True
```

### Pattern 2: Using the Complete Mock Manager

For most tests, use `create_mock_manager()` which gives you a manager with all dependencies mocked:

```python
from tests.conftest import create_mock_manager

def test_with_mock_manager():
    # All dependencies are already mocked
    manager = create_mock_manager(
        docker_available=True,
        container_exists=True,
        container_running=False,
    )

    # Control behavior via flags
    assert manager.check_docker() == True
    assert manager.container_exists() == True
    assert manager.container_running() == False
```

### Pattern 3: Testing Manager Logic

When testing ContainerManager methods, replace just the components you need:

```python
from tests.conftest import create_mock_builder

def test_build_image():
    manager = ContainerManager(config)

    # Replace the builder component
    mock_builder = create_mock_builder()
    manager.builder = mock_builder

    # Call manager method
    result = manager.build_image()

    # Verify builder was called
    assert result == True
    mock_builder.build.assert_called_once()
```

### Pattern 4: pytest Fixtures

Use pytest fixtures from `conftest.py`:

```python
def test_with_fixtures(mock_manager, test_config):
    """
    Fixtures automatically available:
    - test_config: Test configuration
    - mock_manager: Manager with mocked dependencies
    - mock_runtime, mock_lifecycle, etc.
    """
    assert mock_manager.check_docker() == True
```

## Migration Examples

### Before (doesn't work with attrs):

```python
@patch.object(manager.runtime, 'is_available')
def test_check_docker(mock_available):
    # ❌ Fails: can't mock attrs object methods
    mock_available.return_value = True
    assert manager.check_docker() == True
```

### After (works with attrs):

```python
from tests.conftest import create_mock_runtime

def test_check_docker():
    # ✅ Replace entire runtime
    manager = ContainerManager(config)
    manager.runtime = create_mock_runtime(available=True)

    assert manager.check_docker() == True
```

## Quick Reference

### Available Mock Factories

| Factory | Creates Mock For | Key Parameters |
|---------|-----------------|----------------|
| `create_mock_runtime()` | `DockerRuntime` | `available=True` |
| `create_mock_lifecycle()` | `ContainerLifecycle` | `exists=True`, `running=True` |
| `create_mock_exec()` | `ContainerExec` | `container_name` |
| `create_mock_logs()` | `ContainerLogs` | `container_name` |
| `create_mock_builder()` | `ContainerBuilder` | - |
| `create_mock_volumes()` | `VolumeManager` | `backup_dir` |
| `create_mock_storage()` | `ContainerStorage` | `container_name` |
| `create_mock_manager()` | `ContainerManager` | `docker_available`, `container_exists`, `container_running` |

### Available pytest Fixtures

From `conftest.py`:
- `test_config` - Test configuration
- `mock_runtime` - Mock DockerRuntime
- `mock_manager` - Manager with mocked dependencies
- `mock_lifecycle` - Mock ContainerLifecycle
- `mock_exec` - Mock ContainerExec
- `mock_logs` - Mock ContainerLogs
- `mock_builder` - Mock ContainerBuilder
- `mock_volumes` - Mock VolumeManager
- `mock_storage` - Mock ContainerStorage

## Why This Approach?

1. **attrs Provides Value**: Immutability prevents bugs, validation catches errors early
2. **Production Code Quality**: Architecture is correct, tests adapt to it
3. **Type Safety**: Better IDE support and type checking
4. **Maintainability**: Less boilerplate in production code
5. **Future-Proof**: Modern Python ecosystem standard

## Common Mistakes

### ❌ Don't mock individual attrs methods
```python
manager.runtime.is_available = Mock(return_value=True)  # Fails!
```

### ❌ Don't use patch.object on attrs instances
```python
@patch.object(manager.runtime, 'is_available')  # Fails!
def test_something(mock):
    pass
```

### ✅ Do replace entire objects
```python
manager.runtime = create_mock_runtime(available=True)  # Works!
```

### ✅ Do use provided mock factories
```python
from tests.utils.fixtures import create_mock_builder
manager.builder = create_mock_builder()  # Works!
```

## Need Help?

1. Check `tests/utils/fixtures.py` for available mock factories
2. Look at `tests/container/test_manager.py` for working examples
3. See `tests/conftest.py` for available pytest fixtures
4. Refer to this guide for patterns and anti-patterns
