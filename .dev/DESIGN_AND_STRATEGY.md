# DESIGN_AND_STRATEGY.md - wrknv Architecture and Vision

This document outlines the strategic vision, architectural principles, and key design patterns for the `wrknv` project.

## 1. Strategic Vision

`wrknv` is evolving from a tool-version manager into a **comprehensive developer workflow orchestrator** for the Provide.io ecosystem and beyond. Its primary purpose is to provide a reliable, reproducible, and efficient development experience for projects within the Terraform ecosystem.

The strategy is to create a central CLI tool that handles:
1.  **Environment Setup:** Managing versions of tools like OpenTofu, Go, and `uv`.
2.  **Development Lifecycle:** Providing containerized development environments.
3.  **Building & Packaging:** Integrating with `flavor` to build and distribute provider packages.
4.  **Context Management:** (Future) A generic system for bundling files and configurations for AI-assisted development.

## 2. Core Architectural Principles

- **Operational Excellence:** All features must be robust, testable, and reliable. Critical infrastructure code requires high test coverage.
- **Type-Safe Configuration:** User-facing configuration should be validated against a defined schema to ensure correctness and provide clear, actionable error messages to the user.
- **Extensibility:** The system should be designed with clear interfaces (e.g., `BaseToolManager`, `Bundle` protocols) to allow for future expansion with new tools or bundle types.
- **Standalone Runtime:** The primary output for end-users (`env.sh`/`env.ps1`) should be self-contained and **not** require `wrknv` to be installed, ensuring maximum portability. `wrknv` is a development-time tool.

## 3. Key Design Patterns

### 3.1. Validated Configuration

- **Current State:** Basic TOML parsing.
- **Target State:** Configuration loaded from `wrknv.toml` will be validated against an internal schema. This provides:
  - Early failure for invalid configuration.
  - Rich, context-aware error messages.
  - A structured, discoverable configuration API for programmatic use (e.g., by AI agents).

### 3.2. Sibling Dependency Management

- The `siblings` configuration in `wrknv.toml` allows projects to link to other local, editable packages.
- The generated scripts (`env.sh`) will attempt to install these siblings. A critical feature is the **graceful fallback** mechanism: if an installation with dependencies fails (often due to Python version conflicts between a local project and a published dependency), the script should retry with `--no-deps`. This prioritizes a working local environment.

### 3.3. Containerized Development

- The `wrknv container` command provides a disposable, consistent development environment.
- **Implementation:** The `ContainerManager` generates a `Dockerfile` dynamically.
- **Target State:** The Dockerfile's contents (base image, system packages) will be configurable in `wrknv.toml` to adapt to different project requirements.

### 3.4. Bundler System (Future)

- **Concept:** A generic framework for discovering, parsing, and compiling "bundles" of files. A bundle is a directory with a specific structure and suffix (e.g., `.agents`, `.garnish`).
- **Use Cases:**
  - Consolidating AI agent configurations (`.agents`).
  - Aggregating documentation (`.garnish`).
  - Processing source code bundles for LLM context (`bfiles`).
- **Architecture:**
  - A `Bundle` protocol defining the interface.
  - A `BundleDiscovery` service to find bundles on the filesystem.
  - `BundleCompiler` classes to transform bundles into different outputs (e.g., a single markdown file).
