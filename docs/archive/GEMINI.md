# GEMINI.md: Your AI Assistant for the `wrknv` Project

This document provides context and instructions for interacting with the `wrknv` project. It is intended to be used by the Gemini AI assistant to help with development tasks.

## Project Overview

`wrknv` is a command-line tool for managing development tool versions and orchestrating developer workflows, with a focus on the Terraform provider ecosystem. It is written in Python and uses the `click` library for its command-line interface.

The main features of `wrknv` include:

*   **Tool Version Management**: Manage Terraform, OpenTofu, Go, UV, and more.
*   **Workflow Orchestration**: Integrated support for containerized environments and package building.
*   **Flexible Configuration**: Support for multiple configuration sources, with a plan to move to a schema-validated system.
*   **Portable Environments**: Generates self-contained `env.sh` and `env.ps1` scripts that do not require `wrknv` at runtime.

## Key Documentation

The project's direction and technical tasks are managed in the following documents:

*   **`docs/DESIGN_AND_STRATEGY.md`**: The source of truth for architectural principles, design patterns, and the strategic vision for the project. **Consult this file for all architectural questions.**
*   **`docs/TODO.md`**: The official, verified list of development tasks, prioritized by importance and urgency. **Refer to this file for the current development priorities.**
*   **`docs/README.md`**: High-level overview, installation, and quick-start guide for users.

## Development Conventions

The project follows standard Python development conventions. The code is formatted and linted with `ruff`. The project uses `pytest` for testing and `mypy` for type checking. Test coverage on critical infrastructure code is a high priority.
