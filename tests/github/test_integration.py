#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""GitHub Client Integration Tests
================================
Integration tests using real GitHub API."""

from __future__ import annotations

import os
import pathlib

import pytest

from wrknv.managers.github import GitHubReleasesClient

# Skip if no GitHub token available (CI-friendly)
pytestmark = pytest.mark.skipif(
    not os.environ.get("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set - skipping integration tests"
)


@pytest.mark.asyncio
@pytest.mark.network
async def test_list_releases_real() -> None:
    """Test listing releases from real repository."""
    # Use astral-sh/uv as test repository (stable, well-maintained)
    client = GitHubReleasesClient("astral-sh/uv")

    releases = await client.list_releases()

    assert len(releases) > 0
    assert all(r.tag_name for r in releases)
    assert all(r.assets for r in releases)


@pytest.mark.asyncio
@pytest.mark.network
async def test_get_latest_release_real() -> None:
    """Test getting latest release from real repository."""
    client = GitHubReleasesClient("astral-sh/uv")

    release = await client.get_latest_release()

    assert release.tag_name
    assert not release.prerelease
    assert not release.draft
    assert len(release.assets) > 0


@pytest.mark.asyncio
@pytest.mark.network
async def test_list_tags_real() -> None:
    """Test listing tags from real repository."""
    client = GitHubReleasesClient("astral-sh/uv")

    tags = await client.list_tags()

    assert len(tags) > 0
    assert all(t.name for t in tags)
    assert all(t.commit_sha for t in tags)


@pytest.mark.asyncio
@pytest.mark.network
async def test_get_versions_real() -> None:
    """Test getting versions from real repository."""
    client = GitHubReleasesClient("astral-sh/uv")

    versions = await client.get_versions()

    assert len(versions) > 0
    # Versions should not have 'v' prefix
    assert all(not v.startswith("v") for v in versions)


@pytest.mark.asyncio
@pytest.mark.network
async def test_find_asset_real() -> None:
    """Test finding asset in real release."""
    client = GitHubReleasesClient("astral-sh/uv")

    release = await client.get_latest_release()

    # Find a Linux asset
    asset = client.find_asset(release, "*linux*.tar.gz")

    assert asset is not None
    assert asset.browser_download_url
    assert asset.size > 0


@pytest.mark.asyncio
@pytest.mark.network
async def test_download_asset_real(tmp_path: pathlib.Path) -> None:
    """Test downloading a real asset (small file)."""
    client = GitHubReleasesClient("astral-sh/uv")

    release = await client.get_latest_release()

    # Find smallest asset to download (usually checksum file)
    smallest_asset = min(release.assets, key=lambda a: a.size)

    destination = tmp_path / smallest_asset.name

    await client.download_asset(smallest_asset, destination)

    # Verify download
    assert destination.exists()
    assert destination.stat().st_size == smallest_asset.size


@pytest.mark.asyncio
@pytest.mark.network
async def test_download_archive_real(tmp_path: pathlib.Path) -> None:
    """Test downloading repository archive."""
    # Use a small test repository
    client = GitHubReleasesClient("provide-io/supsrc")

    destination = tmp_path / "supsrc-main.zip"

    await client.download_archive("main", destination, format="zipball", ref_type="heads")

    # Verify download
    assert destination.exists()
    assert destination.stat().st_size > 0

    # Verify it's a valid zip file
    import zipfile

    assert zipfile.is_zipfile(destination)


@pytest.mark.asyncio
@pytest.mark.network
async def test_download_archive_tarball_real(tmp_path: pathlib.Path) -> None:
    """Test downloading repository archive as tarball."""
    client = GitHubReleasesClient("provide-io/supsrc")

    destination = tmp_path / "supsrc-main.tar.gz"

    await client.download_archive("main", destination, format="tarball", ref_type="heads")

    # Verify download
    assert destination.exists()
    assert destination.stat().st_size > 0

    # Verify it's a valid gzip file
    import gzip

    with gzip.open(destination, "rb") as f:
        # Should be able to read without error
        f.read(100)


@pytest.mark.asyncio
@pytest.mark.network
async def test_download_tag_archive_real(tmp_path: pathlib.Path) -> None:
    """Test downloading tag as archive."""
    client = GitHubReleasesClient("astral-sh/uv")

    # Get a known tag
    tags = await client.list_tags()
    if tags:
        tag = tags[0].name

        destination = tmp_path / f"uv-{tag}.zip"

        await client.download_archive(tag, destination, format="zipball", ref_type="tags")

        assert destination.exists()
        assert destination.stat().st_size > 0


@pytest.mark.asyncio
@pytest.mark.network
async def test_progress_callback_real(tmp_path: pathlib.Path) -> None:
    """Test download with progress callback."""
    client = GitHubReleasesClient("provide-io/supsrc")

    destination = tmp_path / "supsrc.zip"

    progress_updates = []

    def progress_callback(downloaded: int, total: int) -> None:
        progress_updates.append((downloaded, total))

    await client.download_archive("main", destination, progress_callback=progress_callback)

    # Should have received progress updates
    assert len(progress_updates) > 0
    # Last update should have downloaded <= total (if total is known)
    # or downloaded > 0 (if total is unknown/0)
    if progress_updates:
        last_downloaded, last_total = progress_updates[-1]
        if last_total > 0:
            assert last_downloaded <= last_total
        else:
            # Total size unknown - just verify we downloaded something
            assert last_downloaded > 0


@pytest.mark.asyncio
@pytest.mark.network
async def test_authenticated_client_real() -> None:
    """Test authenticated client with GitHub token."""
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        pytest.skip("GITHUB_TOKEN not set")

    client = GitHubReleasesClient("astral-sh/uv", token=token)

    # Should work the same but with higher rate limits
    releases = await client.list_releases()

    assert len(releases) > 0


# 🧰🌍🔚
