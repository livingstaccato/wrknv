# TODO.md - wrknv Development Tasks

This document tracks prioritized development tasks.

## High Priority - Reliability & Correctness

- [ ] **Increase Test Coverage on Critical Infrastructure**
  - **`container` module (0% coverage):** Add comprehensive tests for Dockerfile generation, container lifecycle (build, start, stop), and command execution.
  - **`operations.download` (11% coverage):** Add tests for various download scenarios, error handling (404s, timeouts), and checksum verification.
  - **`operations.install` (14% coverage):** Test archive extraction for different formats and executable permission handling across platforms.
  - **`env.managers` (18-24% coverage):** Add tests for tool-specific installation logic for `ibmtf`, `tofu`, `go`, and `uv`.

## Medium Priority - Feature Completeness & Architecture

- [ ] **Implement Ecosystem Test Matrix Command**
  - Add `wrknv test-matrix` command to run tests across all sibling packages
  - Generate comprehensive test report in markdown format
  - Include pass/fail rates, coverage metrics, and identified issues
  - Support parallel test execution for faster results
  - Integrate with CI/CD for automated ecosystem health checks

- [ ] **Fix Test Environment Integration**
  - Tests should use wrknv-managed `workenv/` directories (e.g., `workenv/wrknv_darwin_arm64`)
  - Currently tests are creating `.venv` instead of using wrknv's workenv pattern
  - Update test runners to properly activate and use wrknv environments
  - Ensure consistent environment usage across all packages

- [ ] **Implement Type-Safe Configuration**
  - Define a validation schema for the `wrknv.toml` structure.
  - Refactor `env.config` to validate loaded configuration against this schema, providing clear errors on invalid input. This will improve reliability and user experience.

- [ ] **Complete `package` Command Implementation**
  - Implement the actual logic for `sign_package` and `publish_package` by integrating with the `flavor` API.
  - Remove mock data and `NotImplementedError` placeholders.
  - Mark commands as experimental in the CLI help text until fully functional.

- [ ] **Make Container Configuration Dynamic**
  - Refactor `ContainerManager._generate_dockerfile` to source its base image and packages from `wrknv.toml` instead of using hardcoded values.

- [ ] **Refactor Data Classes to Use `attrs`**
  - Systematically replace standard classes and dataclasses used for configuration and data modeling with `attrs` classes for improved validation and robustness.

## Low Priority - Future Enhancements

- [ ] **Implement Generic Bundler System**
  - Design and implement the extensible framework for managing directory-based bundles as proposed in `BUNDLER_PROPOSAL.md`.
  - This would provide a foundation for managing `.agents`, `.garnish`, and `bfiles` outputs.

- [ ] **Finalize `bfiles` Integration**
  - Implement `bfiles` as a managed tool and a bundle type within the new bundler system.
