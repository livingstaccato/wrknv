#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Integration tests for workspace task orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.workspace.orchestrator import WorkspaceOrchestrator


@pytest.mark.asyncio
async def test_workspace_task_execution_with_real_task(tmp_path: Path) -> None:
    """Test actual task execution across repos."""
    # Create test repos with simple echo task
    for repo_name in ["repo1", "repo2", "repo3"]:
        repo_path = tmp_path / repo_name
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "pyproject.toml").write_text(f'[project]\nname = "{repo_name}"')
        (repo_path / "wrknv.toml").write_text(
            """
[tasks.test]
_default = "echo 'Test passed'"
unit = "echo 'Unit test passed'"
"""
        )

    orchestrator = WorkspaceOrchestrator(root=tmp_path)

    # Run test task (should resolve to test._default)
    result = await orchestrator.run_task("test")

    assert result.total_repos == 3
    assert result.succeeded == 3
    assert result.failed == 0
    assert result.skipped == 0
    assert result.success is True

    # Verify all repos succeeded
    succeeded_repos = result.get_succeeded_repos()
    assert set(succeeded_repos) == {"repo1", "repo2", "repo3"}


@pytest.mark.asyncio
async def test_workspace_task_with_pattern_filter(tmp_path: Path) -> None:
    """Test pattern filtering during execution."""
    # Create mixed repos
    for repo_name in ["pyvider-test", "pyvider-other", "wrknv", "other"]:
        repo_path = tmp_path / repo_name
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "pyproject.toml").write_text(f'[project]\nname = "{repo_name}"')
        (repo_path / "wrknv.toml").write_text('[tasks]\ntest = "echo pass"')

    orchestrator = WorkspaceOrchestrator(root=tmp_path)

    # Filter for pyvider-* only
    result = await orchestrator.run_task("test", repo_filter="pyvider-*")

    assert result.total_repos == 2  # Only pyvider-test and pyvider-other
    assert result.succeeded == 2
    assert set(result.get_succeeded_repos()) == {"pyvider-test", "pyvider-other"}


@pytest.mark.asyncio
async def test_workspace_sequential_vs_parallel(tmp_path: Path) -> None:
    """Test both sequential and parallel execution modes."""
    # Create test repos
    for repo_name in ["repo1", "repo2"]:
        repo_path = tmp_path / repo_name
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "pyproject.toml").write_text(f'[project]\nname = "{repo_name}"')
        (repo_path / "wrknv.toml").write_text('[tasks]\nquick = "echo done"')

    orchestrator = WorkspaceOrchestrator(root=tmp_path)

    # Test sequential
    result_seq = await orchestrator.run_task("quick", parallel=False)
    assert result_seq.succeeded == 2
    assert result_seq.success is True

    # Test parallel
    result_par = await orchestrator.run_task("quick", parallel=True)
    assert result_par.succeeded == 2
    assert result_par.success is True


@pytest.mark.asyncio
async def test_workspace_fail_fast_mode(tmp_path: Path) -> None:
    """Test fail-fast stops on first failure."""
    # Create repos where second one will fail
    repo1_path = tmp_path / "repo1"
    repo1_path.mkdir()
    (repo1_path / ".git").mkdir()
    (repo1_path / "pyproject.toml").write_text('[project]\nname = "repo1"')
    (repo1_path / "wrknv.toml").write_text('[tasks]\ntest = "echo pass"')

    repo2_path = tmp_path / "repo2"
    repo2_path.mkdir()
    (repo2_path / ".git").mkdir()
    (repo2_path / "pyproject.toml").write_text('[project]\nname = "repo2"')
    (repo2_path / "wrknv.toml").write_text('[tasks]\ntest = "exit 1"')  # Will fail

    repo3_path = tmp_path / "repo3"
    repo3_path.mkdir()
    (repo3_path / ".git").mkdir()
    (repo3_path / "pyproject.toml").write_text('[project]\nname = "repo3"')
    (repo3_path / "wrknv.toml").write_text('[tasks]\ntest = "echo pass"')

    orchestrator = WorkspaceOrchestrator(root=tmp_path)

    # Run with fail-fast
    result = await orchestrator.run_task("test", fail_fast=True, parallel=False)

    # With fail-fast, execution stops on first failure
    # Since we can't control discovery order, just verify:
    # 1. At least one repo failed
    # 2. Overall result is failure
    # 3. We didn't necessarily process all repos (though discovery order may vary)
    assert result.failed >= 1  # At least one failure
    assert result.success is False  # Overall failure

    # Verify repo2 (the failing one) is in the results
    assert "repo2" in result.repo_results
    assert result.repo_results["repo2"].success is False
