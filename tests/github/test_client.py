#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""GitHub Client Unit Tests
=========================
Unit tests for GitHubReleasesClient."""

from __future__ import annotations

from provide.testkit.mocking import MagicMock, patch
import pytest

from wrknv.managers.github import GitHubReleasesClient, Release, Tag


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock()
    response.headers = {}
    return response


@pytest.fixture
def sample_release_data():
    """Sample GitHub release API response."""
    return {
        "tag_name": "v1.0.0",
        "name": "Release 1.0.0",
        "prerelease": False,
        "draft": False,
        "body": "Release notes",
        "published_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z",
        "id": 12345,
        "html_url": "https://github.com/owner/repo/releases/tag/v1.0.0",
        "assets": [
            {
                "name": "tool-1.0.0-linux-amd64.tar.gz",
                "browser_download_url": "https://github.com/owner/repo/releases/download/v1.0.0/tool-1.0.0-linux-amd64.tar.gz",
                "size": 1024000,
                "content_type": "application/gzip",
                "id": 1,
                "state": "uploaded",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        ],
    }


@pytest.fixture
def sample_tag_data():
    """Sample GitHub tag API response."""
    return {
        "name": "v1.0.0",
        "commit": {"sha": "abc123"},
        "zipball_url": "https://github.com/owner/repo/zipball/v1.0.0",
        "tarball_url": "https://github.com/owner/repo/tarball/v1.0.0",
    }


class TestGitHubReleasesClient:
    """Test GitHubReleasesClient."""

    def test_init(self) -> None:
        """Test client initialization."""
        client = GitHubReleasesClient("owner/repo")
        assert client.repo == "owner/repo"
        assert client.token is None

    def test_init_with_token(self) -> None:
        """Test client initialization with token."""
        client = GitHubReleasesClient("owner/repo", token="ghp_test")
        assert client.repo == "owner/repo"
        assert client.token == "ghp_test"
        assert "Authorization" in client.client.default_headers

    @pytest.mark.asyncio
    async def test_list_releases(self, sample_release_data, mock_response) -> None:
        """Test listing releases."""
        mock_response.json = MagicMock(return_value=[sample_release_data])

        client = GitHubReleasesClient("owner/repo")

        with patch(
            "provide.foundation.transport.client.UniversalClient.get", return_value=mock_response
        ) as mock_get:
            releases = await client.list_releases()

            assert len(releases) == 1
            assert isinstance(releases[0], Release)
            assert releases[0].tag_name == "v1.0.0"
            assert releases[0].name == "Release 1.0.0"
            assert len(releases[0].assets) == 1

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_releases_filter_prereleases(self, sample_release_data, mock_response) -> None:
        """Test filtering prereleases."""
        prerelease_data = sample_release_data.copy()
        prerelease_data["prerelease"] = True

        mock_response.json = MagicMock(return_value=[sample_release_data, prerelease_data])

        client = GitHubReleasesClient("owner/repo")

        with patch("provide.foundation.transport.client.UniversalClient.get", return_value=mock_response):
            # Without prereleases
            releases = await client.list_releases(include_prereleases=False)
            assert len(releases) == 1
            assert not releases[0].prerelease

            # With prereleases
            releases = await client.list_releases(include_prereleases=True)
            assert len(releases) == 2

    @pytest.mark.asyncio
    async def test_get_latest_release(self, sample_release_data, mock_response) -> None:
        """Test getting latest release."""
        mock_response.json = MagicMock(return_value=sample_release_data)

        client = GitHubReleasesClient("owner/repo")

        with patch(
            "provide.foundation.transport.client.UniversalClient.get", return_value=mock_response
        ) as mock_get:
            release = await client.get_latest_release()

            assert isinstance(release, Release)
            assert release.tag_name == "v1.0.0"

            # Check correct endpoint was called
            call_args = mock_get.call_args
            assert "releases/latest" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_release_by_tag(self, sample_release_data, mock_response) -> None:
        """Test getting release by tag."""
        mock_response.json = MagicMock(return_value=sample_release_data)

        client = GitHubReleasesClient("owner/repo")

        with patch(
            "provide.foundation.transport.client.UniversalClient.get", return_value=mock_response
        ) as mock_get:
            release = await client.get_release_by_tag("v1.0.0")

            assert isinstance(release, Release)
            assert release.tag_name == "v1.0.0"

            # Check correct endpoint was called
            call_args = mock_get.call_args
            assert "releases/tags/v1.0.0" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_tags(self, sample_tag_data, mock_response) -> None:
        """Test listing tags."""
        mock_response.json = MagicMock(return_value=[sample_tag_data])

        client = GitHubReleasesClient("owner/repo")

        with patch(
            "provide.foundation.transport.client.UniversalClient.get", return_value=mock_response
        ) as mock_get:
            tags = await client.list_tags()

            assert len(tags) == 1
            assert isinstance(tags[0], Tag)
            assert tags[0].name == "v1.0.0"
            assert tags[0].commit_sha == "abc123"

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_versions(self, sample_release_data, mock_response) -> None:
        """Test getting version strings."""
        mock_response.json = MagicMock(return_value=[sample_release_data])

        client = GitHubReleasesClient("owner/repo")

        with patch("provide.foundation.transport.client.UniversalClient.get", return_value=mock_response):
            versions = await client.get_versions()

            assert len(versions) == 1
            assert versions[0] == "1.0.0"  # v prefix stripped

    @pytest.mark.asyncio
    async def test_get_versions_no_v_prefix(self, sample_release_data, mock_response) -> None:
        """Test getting versions without v prefix."""
        sample_release_data["tag_name"] = "1.0.0"  # No 'v' prefix
        mock_response.json = MagicMock(return_value=[sample_release_data])

        client = GitHubReleasesClient("owner/repo")

        with patch("provide.foundation.transport.client.UniversalClient.get", return_value=mock_response):
            versions = await client.get_versions()

            assert versions[0] == "1.0.0"

    def test_find_asset(self, sample_release_data) -> None:
        """Test finding asset by pattern."""
        release = Release.from_api(sample_release_data)
        client = GitHubReleasesClient("owner/repo")

        # Find by exact name
        asset = client.find_asset(release, "tool-1.0.0-linux-amd64.tar.gz")
        assert asset is not None
        assert asset.name == "tool-1.0.0-linux-amd64.tar.gz"

        # Find by glob pattern
        asset = client.find_asset(release, "*linux*.tar.gz")
        assert asset is not None

        # Find by partial match
        asset = client.find_asset(release, "linux-amd64")
        assert asset is not None

        # Not found
        asset = client.find_asset(release, "*windows*")
        assert asset is None

    # Download tests are covered by integration tests
    # Unit testing downloads with mocked transport is complex due to context managers

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test client as context manager."""
        async with GitHubReleasesClient("owner/repo") as client:
            assert client.repo == "owner/repo"


# 🧰🌍🔚
