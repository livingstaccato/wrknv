# WrkNv Documentation

Welcome to WrkNv - Work environment management and toolchain automation for modern development workflows.

## Features

WrkNv provides:

- **Environment Management**: Automated setup and management of development environments
- **Toolchain Automation**: Orchestration of development tools and dependencies
- **Container Integration**: Seamless Docker and container workflow support
- **Package Management**: Unified package management across languages and platforms
- **Configuration Management**: Environment-specific configuration handling
- **Git Integration**: Advanced Git workflow automation and management

## Quick Start

### Installation

<div class="termy">

```console
$ pip install wrknv
// Installing wrknv...
Successfully installed wrknv

$ wrknv --version
wrknv, version 0.3.0
```

</div>

### Initialize a New Work Environment

<div class="termy">

```console
$ wrknv init my-project
// Creating work environment...
✓ Created workenv/my-project/
✓ Initialized configuration
✓ Generated env.sh
✓ Generated env.ps1

Environment initialized successfully!

$ cd my-project
$ source workenv/*/bin/activate
// Activating work environment...
(my-project) $
```

</div>

### Check Environment Status

<div class="termy">

```console
$ wrknv status
// Checking environment status...

Environment: my-project
Status: ✓ active
Python: 3.11.12
UV: 0.5.1
Platform: darwin_arm64

Tools installed:
  ✓ uv
  ✓ terraform
  ✓ go
```

</div>

### Manage Tools and Dependencies

<div class="termy">

```console
$ wrknv tool install terraform --version 1.9.0
// Downloading terraform 1.9.0...
---> 100%
✓ Installed terraform 1.9.0
✓ Added to PATH

$ wrknv sync
// Synchronizing dependencies...
Resolved 45 packages
✓ Environment synchronized
```

</div>

### Python API Usage

```python
from wrknv import Environment, Container

# Create and manage development environment
env = Environment("myproject")
env.setup()

# Work with containers
container = Container("python:3.11")
container.run("pip install -r requirements.txt")
```

## API Reference

For complete API documentation, see the [API Reference](reference/).

## Core Components

- **Environment**: Development environment orchestration
- **Container**: Container and Docker integration
- **Package**: Package management and dependency resolution
- **Config**: Configuration management utilities
- **CLI**: Command-line interface tools