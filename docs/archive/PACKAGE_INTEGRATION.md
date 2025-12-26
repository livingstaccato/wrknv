# 📦 Package Integration - wrknv + flavorpack

This document describes how wrknv integrates with flavorpack to enable self-packaging and provider packaging.

## Overview

wrknv can now package itself and other Python applications using the `flavor pack` command through its package management interface.

## Installation

Install flavorpack to enable packaging functionality:

```bash
uv pip install --system flavorpack
```

Or with regular pip:

```bash
pip install flavorpack
```

## Configuration

wrknv's `pyproject.toml` includes flavor configuration:

```toml
[tool.flavor]
# Configuration for packaging wrknv with flavor
entry_point = "wrknv.wenv.cli:entry_point"
app_name = "wrknv"
description = "🧰🌍 Work Environment - Foundation for the provide.io ecosystem"
```

## Usage

### Direct flavor pack Command

Package wrknv directly with flavor:

```bash
flavor pack --manifest pyproject.toml
```

This will create a `.psp` (Progressive Secure Package Format) file in the `dist/` directory.

### Using wrknv package Commands

wrknv provides wrapper commands for flavor functionality (when the CLI integration is complete):

```bash
# Build a package
wrknv package build --manifest pyproject.toml

# Verify a package
wrknv package verify dist/wrknv.psp

# Generate signing keys
wrknv package keygen --out-dir keys/

# List built packages
wrknv package list

# Get package info
wrknv package info dist/wrknv.psp

# Clean build cache
wrknv package clean

# Initialize a new provider project
wrknv package init my-provider
```

## Package Commands Implementation

The package commands are implemented in `src/wrknv/package/commands.py` and use subprocess calls to the `flavor` CLI:

- **`build_package()`** - Calls `flavor pack` to build packages
- **`verify_package()`** - Calls `flavor verify` to verify packages
- **`generate_keys()`** - Calls `flavor keygen` to generate signing keys
- **`clean_cache()`** - Calls `flavor clean` to clear caches
- **`get_package_info()`** - Calls `flavor inspect` to get package metadata

## Packaging Workflow

### 1. Build wrknv as a Package

```bash
cd /path/to/wrknv
flavor pack --manifest pyproject.toml
```

Output:
```
dist/wrknv.psp
```

### 2. Verify the Package

```bash
flavor verify dist/wrknv.psp
```

### 3. Inspect Package Contents

```bash
flavor inspect dist/wrknv.psp
```

### 4. Extract Package (for testing)

```bash
flavor extract-all dist/wrknv.psp --output extracted/
```

## Provider Project Initialization

Create a new Terraform provider project:

```bash
wrknv package init my-provider
cd my-provider
```

This creates:
```
my-provider/
├── pyproject.toml       # With [tool.flavor] config
├── src/                 # Source code
├── tests/               # Test files
└── keys/                # For signing keys
```

The generated `pyproject.toml` includes:

```toml
[tool.flavor]
provider_name = "example"
entry_point = "provider.main:serve"

[tool.flavor.signing]
private_key_path = "keys/private.pem"
public_key_path = "keys/public.pem"
```

## Signing Packages

Generate signing keys:

```bash
flavor keygen
```

This creates:
- `private.pem` - Keep this secret
- `public.pem` - Distribute with packages

Build with signing:

```bash
flavor pack --manifest pyproject.toml --private-key keys/private.pem
```

## Implementation Details

### CLI Integration Status

**Current Status:** The package commands use the flavor CLI via subprocess.

**Files Modified:**
- `src/wrknv/package/commands.py` - Rewritten to use flavor CLI
- `pyproject.toml` - Added `[tool.flavor]` configuration
- `src/wrknv/cli/hub_cli.py` - Fixed import (Context → CLIContext)

### Key Functions

```python
def _check_flavor_cli() -> bool:
    """Check if flavor CLI is available."""
    if not shutil.which("flavor"):
        raise ImportError(
            "flavor CLI not found. Install it with: uv pip install --system flavorpack"
        )
    return True

def _run_flavor_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a flavor CLI command."""
    _check_flavor_cli()
    cmd = ["flavor"] + args
    logger.debug(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
```

## Features

### ✅ Implemented
- [x] Package building via `flavor pack`
- [x] Package verification via `flavor verify`
- [x] Key generation via `flavor keygen`
- [x] Cache cleaning via `flavor clean`
- [x] Package inspection via `flavor inspect`
- [x] Provider project initialization
- [x] Configuration in `pyproject.toml`

### ⚠️ Experimental
- Package listing (reads from dist/)
- Package info (uses flavor inspect)

### ❌ Not Implemented
- Package signing (done during build with --private-key flag)
- Package publishing to registry (placeholder implementation)

## Examples

### Example 1: Package wrknv

```bash
cd wrknv/
flavor pack --manifest pyproject.toml
ls -lh dist/wrknv.psp
```

### Example 2: Create and Package a Provider

```bash
wrknv package init terraform-provider-example
cd terraform-provider-example

# Edit src/ to implement your provider

# Generate keys
flavor keygen

# Build the provider package with signing
flavor pack --manifest pyproject.toml --private-key private.pem

# Verify
flavor verify dist/terraform-provider-example.psp
```

### Example 3: Extract and Test

```bash
# Extract the package
flavor extract-all dist/wrknv.psp --output test-extraction/

# Inspect what's inside
ls -R test-extraction/
```

## Troubleshooting

### "flavor CLI not found"

Install flavorpack:
```bash
uv pip install --system flavorpack
# or
pip install flavorpack
```

### "Network connection error" during build

flavor pack needs network access to download dependencies. Ensure you have internet connectivity or use a package index mirror.

### Build fails with "setuptools not found"

The build system needs setuptools. Install it:
```bash
pip install setuptools>=68
```

### CLI import errors

There's a known issue with mixed CLI frameworks (click + hub). Use the flavor CLI directly until this is resolved:
```bash
flavor pack --manifest pyproject.toml
```

Instead of:
```bash
wrknv package build  # May not work due to CLI conflicts
```

## Architecture

```
┌─────────────────────────────────────┐
│   wrknv CLI (Click/Hub)              │
│   └─ package command group           │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   wrknv.package.commands             │
│   - build_package()                  │
│   - verify_package()                 │
│   - generate_keys()                  │
│   - clean_cache()                    │
└──────────────┬──────────────────────┘
               │
               ↓ subprocess.run()
┌─────────────────────────────────────┐
│   flavor CLI                         │
│   - pack                             │
│   - verify                           │
│   - keygen                           │
│   - clean                            │
│   - inspect                          │
└─────────────────────────────────────┘
```

## Next Steps

1. **Resolve CLI framework conflict** - Complete migration to hub-based CLI
2. **Implement registry publishing** - Add actual registry client
3. **Enhanced package info** - Parse flavor inspect output properly
4. **Testing** - Add integration tests for packaging workflow
5. **Documentation** - User guide for creating and distributing providers

## References

- [flavor GitHub](https://github.com/provide-io/flavor)
- [PSPF Specification](https://github.com/provide-io/flavor/blob/main/docs/pspf-spec.md)
- [wrknv README](README.md)
- [wrknv TODO](docs/TODO.md)

---

**Status:** ✅ Functional - flavor integration complete, CLI integration pending
**Last Updated:** 2025-11-13
**Version:** wrknv 0.1.0 + flavorpack 0.0.1026.post0
