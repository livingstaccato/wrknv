# wrknv Cleanup & Enhancement - Continuation Plan

## Session Context
**Date Started**: 2025-10-11
**Goal**: Remove package feature, fix bugs, update tests, implement missing container features
**Status**: Phase 1 & 2A partially complete

---

## ✅ COMPLETED WORK

### Phase 1: Package Feature Removal
- ✅ **Deleted**: `src/wrknv/package/` directory (complete removal)
  - Removed: `__init__.py`, `commands.py`, `manager.py`, `registry.py`
- ⚠️ **Note**: Did NOT touch `src/wrknv/workenv/packaging.py` (different feature - workenv distribution)

### Phase 2A: Bug Fixes (Partial)
- ✅ **Fixed**: Async/sync bug in `src/wrknv/gitignore/templates.py:133`
  - Added `asyncio.run()` wrapper around `get()` call
  - Bug was causing "coroutine object has no attribute 'json'" warnings
  - Now properly awaits the async HTTP call

---

## 🚧 REMAINING WORK

### Phase 2B: Delete Dead Code (15 min)
**Files to delete**:
```bash
rm src/wrknv/cli/commands/gitignore_failed.py  # 221 lines - old implementation
rm src/wrknv/cli/commands/profile_failed.py    # old implementation (if exists)
```

**Verify no imports**:
```bash
grep -r "gitignore_failed\|profile_failed" src/
```

---

### Phase 3: Update Gitignore Tests (2-3 hours)

#### 3.1 Fix GitignoreManager Tests
**File**: `tests/gitignore/test_manager.py`
**Status**: Currently skipped - "TemplateHandler mocking incompatible with current API"

**Issue**: Test mocks `TemplateHandler` but it's now created in `__init__` with cache_dir
**Solution**:
```python
# Update mocks to match current signature:
@patch('wrknv.gitignore.manager.TemplateHandler')
def test_something(self, mock_handler_class):
    mock_handler = Mock()
    mock_handler_class.return_value = mock_handler
    # ... rest of test
```

**Remove**: `@pytest.mark.skip(reason="...")` from line 16

---

#### 3.2 Fix TemplateHandler Tests
**File**: `tests/gitignore/test_templates.py`
**Status**: Currently skipped - "Template tests need update for current API"

**Changes needed**:
- Update cache directory expectations
- Fix `update_cache()` method expectations
- Account for resilience decorators (@retry, fallback)
- Test both success and fallback paths

**Remove**: `@pytest.mark.skip(reason="...")` from line 17

---

#### 3.3 Fix ProjectDetector Tests
**File**: `tests/gitignore/test_detector.py`
**Status**: Currently skipped - "Detector tests need update for current API"

**Changes needed**:
- Update `detect_project_types()` method expectations
- Fix fixture setup for project detection

**Remove**: `@pytest.mark.skip(reason="...")` from line 13

---

#### 3.4 Fix Container Test Issues (30 min)

**A. Hub CLI Parameter Duplication**
**File**: `tests/container/test_container_shell_commands.py:468`
**Issue**: "Hub CLI parameter duplication bug when tests run in sequence"
**Solution**:
- Check if command is registered twice in test setup
- Use test isolation or unique command names
**Remove skip**: Line 468

**B. Duplicate --backup-path Parameter**
**File**: `tests/container/test_container_volume_commands.py:377`
**Issue**: "Duplicate --backup-path parameter in CLI definition"
**Solution**:
- Check `src/wrknv/cli/commands/container.py` volumes restore command
- Verify parameter is only defined once
**Remove skip**: Line 377

**C. Attrs Mock Factory Pattern**
**File**: `tests/container/test_dynamic_config.py:83`
**Issue**: "Needs refactoring to use attrs mock factory pattern"
**Solution**:
- Update mock to use `attrs.evolve()` or similar patterns
**Remove skip**: Line 83

---

### Phase 4: Implement Container Features (3-4 hours)

#### 4.1 Verify list_volumes() Implementation ✅ LIKELY DONE
**File**: `src/wrknv/container/commands.py:156`
**Status**: Function EXISTS and looks complete (lines 156-194)
**Verify**:
```python
# Check if ContainerManager.list_volumes() exists:
grep -A 20 "def list_volumes" src/wrknv/container/manager.py
```

**If missing**, implement in `src/wrknv/container/manager.py`:
```python
def list_volumes(self) -> list[dict]:
    """List container volumes with info."""
    # Return volume name, path, exists, size, file count
    # See commands.py:156-194 for expected format
```

**Remove skip**: `tests/container/test_container_storage.py:241`

---

#### 4.2 Implement Container Stats Command (2 hours) ❌ NOT DONE

**A. Add Manager Method**
**File**: `src/wrknv/container/manager.py`
```python
def get_stats(self) -> dict:
    """Get container resource statistics.

    Returns:
        dict with keys: cpu_percent, memory_usage, memory_limit,
                       memory_percent, network_rx, network_tx,
                       block_read, block_write, pids
    """
    # Use docker stats command or docker API
    # Parse output and return structured data
```

**B. Add Command Function**
**File**: `src/wrknv/container/commands.py`
```python
def container_stats(
    config: WorkenvConfig | None = None,
    follow: bool = False,
    no_stream: bool = True,
) -> None:
    """Display container resource statistics."""
    manager = ContainerManager(config)
    console = Console()

    if follow:
        # Stream stats continuously
        pass
    else:
        # Show stats once
        stats = manager.get_stats()
        # Create rich table with stats
```

**C. Register CLI Command**
**File**: `src/wrknv/cli/commands/container.py`
```python
@register_command(
    "container.stats",
    description="Show container resource statistics",
)
def container_stats_command(follow: bool = False):
    """Show container resource statistics."""
    config = WrknvContext.get_config()
    container_stats(config=config, follow=follow)
```

**Remove skip**: `tests/container/test_container_shell_commands.py:506`

---

## 📊 Expected Final State

### Test Results:
- **Before**: 393 passing, 86 skipped
- **After**: ~440 passing, ~50 skipped
  - Remove 5 gitignore tests from skip
  - Remove ~30 gitignore test cases from skip
  - Remove 3 container tests from skip
  - Reduce by ~36 total skipped tests

### Code Quality:
- ✅ Zero async/sync bugs
- ✅ Zero dead code files
- ✅ Package feature completely removed
- ✅ All gitignore tests passing
- ✅ Container stats fully implemented

---

## 🚀 Quick Start Commands

### Run specific test suites:
```bash
# Gitignore tests
python -m pytest tests/gitignore/ -xvs

# Container tests
python -m pytest tests/container/test_container_storage.py::TestVolumeManagement::test_list_volumes -xvs
python -m pytest tests/container/test_container_shell_commands.py::TestCLIIntegration::test_cli_stats_command -xvs

# Full suite
python -m pytest tests/ -v
```

### Check for dead code:
```bash
find src/wrknv -name "*_failed.py"
```

### Verify async fix:
```bash
python -c "
import sys
sys.path.insert(0, 'src')
from wrknv.gitignore.templates import TemplateHandler
h = TemplateHandler()
h.update_cache(force=True)
print('✅ No async warnings!')
"
```

---

## 📝 Notes

- **Test Strategy**: Fix tests one file at a time, run after each fix
- **Container Stats**: Use `docker stats --no-stream` for implementation reference
- **Async Fix**: Verify no more "coroutine was never awaited" warnings
- **Dead Code**: Ensure no imports reference deleted files before removing

---

## 🎯 Priority Order

1. **Phase 2B** (15 min) - Delete dead code - quick win
2. **Phase 3.1-3.3** (2 hours) - Fix gitignore tests - biggest impact
3. **Phase 4.2** (2 hours) - Implement stats - new feature
4. **Phase 3.4** (30 min) - Fix container test issues - polish
5. **Phase 4.1** (30 min) - Verify/enable list_volumes - likely already done

**Total Remaining**: ~5 hours

---

## ✅ Definition of Done

- [ ] No `*_failed.py` files in codebase
- [ ] No async/sync warnings when running gitignore commands
- [ ] All gitignore tests passing (no skips in `tests/gitignore/`)
- [ ] `wrknv container stats` command works
- [ ] `wrknv container volumes list` command works
- [ ] Test count: ~440 passing, ~50 skipped
- [ ] Full test suite passes: `python -m pytest tests/ -v`

Good luck! 🚀
