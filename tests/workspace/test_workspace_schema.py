#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for workspace schema."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
import pytest

from wrknv.workspace.schema import RepoConfig, WorkspaceConfig


class TestWorkspaceConfig(FoundationTestCase):
    """Test WorkspaceConfig methods."""

    def test_get_repos_by_type(self) -> None:
        """Test getting repos by type."""
        config = WorkspaceConfig(
            root="/workspace",
            repos=[
                RepoConfig(name="repo1", type="python", path="/path1", template_profile="default"),
                RepoConfig(name="repo2", type="go", path="/path2", template_profile="default"),
                RepoConfig(name="repo3", type="python", path="/path3", template_profile="default"),
            ],
        )

        python_repos = config.get_repos_by_type("python")
        assert len(python_repos) == 2
        assert all(repo.type == "python" for repo in python_repos)

        go_repos = config.get_repos_by_type("go")
        assert len(go_repos) == 1
        assert go_repos[0].name == "repo2"

    def test_get_outdated_repos(self) -> None:
        """Test getting outdated repos."""
        config = WorkspaceConfig(
            root="/workspace",
            repos=[
                RepoConfig(
                    name="repo1",
                    type="python",
                    path="/path1",
                    template_profile="default",
                    template_version="1.0.0",
                ),
                RepoConfig(
                    name="repo2",
                    type="go",
                    path="/path2",
                    template_profile="default",
                    template_version="2.0.0",
                ),
                RepoConfig(
                    name="repo3",
                    type="python",
                    path="/path3",
                    template_profile="default",
                    template_version="1.0.0",
                ),
            ]
        )

        outdated = config.get_outdated_repos("2.0.0")
        assert len(outdated) == 2
        assert all(repo.template_version == "1.0.0" for repo in outdated)

        up_to_date = config.get_outdated_repos("1.0.0")
        assert len(up_to_date) == 1
        assert up_to_date[0].template_version == "2.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
