#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for Download Operations
=============================
Tests for the download functionality in wrknv."""

from __future__ import annotations

import hashlib

from provide.testkit.mocking import patch

from wrknv.wenv.operations.download import (
    download_file,
    get_filename_from_url,
    parse_checksum_file,
    validate_download_url,
    verify_checksum,
)


class TestDownloadOperations:
    """Test download operations functionality."""

    def test_verify_checksum_success(self, tmp_path) -> None:
        """Test successful checksum verification."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)

        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()

        # Verify checksum
        result = verify_checksum(test_file, expected_hash)
        assert result is True

    def test_verify_checksum_mismatch(self, tmp_path) -> None:
        """Test checksum verification with mismatch."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")

        # Verify checksum should fail with wrong hash
        result = verify_checksum(test_file, "wronghash")
        assert result is False

    def test_verify_checksum_nonexistent_file(self, tmp_path) -> None:
        """Test checksum verification with non-existent file."""
        test_file = tmp_path / "nonexistent.txt"

        # Should return False
        result = verify_checksum(test_file, "somehash")
        assert result is False

    def test_verify_checksum_different_algorithms(self, tmp_path) -> None:
        """Test checksum verification with different algorithms."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)

        # Test SHA256
        sha256_hash = hashlib.sha256(test_content).hexdigest()
        assert verify_checksum(test_file, sha256_hash, "sha256") is True

        # Test SHA1
        sha1_hash = hashlib.sha1(test_content).hexdigest()
        assert verify_checksum(test_file, sha1_hash, "sha1") is True

        # Test MD5
        md5_hash = hashlib.md5(test_content).hexdigest()
        assert verify_checksum(test_file, md5_hash, "md5") is True

    def test_verify_checksum_unsupported_algorithm(self, tmp_path) -> None:
        """Test checksum verification with unsupported algorithm."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")

        # Should return False for unsupported algorithm
        result = verify_checksum(test_file, "somehash", "sha512")
        assert result is False

    @patch("wrknv.wenv.operations.download.UniversalClient")
    def test_download_file_success(self, mock_client_class, tmp_path) -> None:
        """Test successful file download."""
        from unittest.mock import AsyncMock, MagicMock

        url = "https://example.com/test.zip"
        dest_path = tmp_path / "test.zip"

        # Mock response object
        mock_response = MagicMock()
        mock_response.is_success.return_value = True
        mock_response.status = 200
        mock_response.headers = {"content-length": "16"}

        # Mock UniversalClient
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.head = AsyncMock(return_value=mock_response)

        async def mock_stream(url, method="GET"):
            yield b"ZIP file content"

        mock_client.stream = mock_stream
        mock_client_class.return_value = mock_client

        download_file(url, dest_path)

        # Verify file was written
        assert dest_path.exists()
        assert dest_path.read_bytes() == b"ZIP file content"

    @patch("wrknv.wenv.operations.download.UniversalClient")
    def test_download_file_with_progress(self, mock_client_class, tmp_path) -> None:
        """Test file download with progress display."""
        from unittest.mock import AsyncMock, MagicMock

        url = "https://example.com/test.zip"
        dest_path = tmp_path / "test.zip"

        # Mock response object
        mock_response = MagicMock()
        mock_response.is_success.return_value = True
        mock_response.status = 200
        mock_response.headers = {"content-length": "16"}

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.head = AsyncMock(return_value=mock_response)

        async def mock_stream(url, method="GET"):
            yield b"ZIP file content"

        mock_client.stream = mock_stream
        mock_client_class.return_value = mock_client

        download_file(url, dest_path, show_progress=True)

        assert dest_path.exists()
        assert dest_path.read_bytes() == b"ZIP file content"

    def test_parse_checksum_file_success(self, tmp_path) -> None:
        """Test parsing checksum file."""
        checksum_file = tmp_path / "checksums.sha256"
        checksum_file.write_text("""
# Comment line
abc123  test.zip
def456  other.zip
789xyz  *marked.zip
        """)

        # Find checksum for test.zip
        result = parse_checksum_file(checksum_file, "test.zip")
        assert result == "abc123"

        # Find checksum for marked.zip (with asterisk)
        result = parse_checksum_file(checksum_file, "marked.zip")
        assert result == "789xyz"

    def test_parse_checksum_file_not_found(self, tmp_path) -> None:
        """Test parsing checksum file when target not found."""
        checksum_file = tmp_path / "checksums.sha256"
        checksum_file.write_text("abc123  other.zip\n")

        result = parse_checksum_file(checksum_file, "test.zip")
        assert result is None

    def test_parse_checksum_file_nonexistent(self, tmp_path) -> None:
        """Test parsing non-existent checksum file."""
        checksum_file = tmp_path / "missing.sha256"
        result = parse_checksum_file(checksum_file, "test.zip")
        assert result is None

    def test_get_filename_from_url(self) -> None:
        """Test extracting filename from URL."""
        # Normal URL
        assert get_filename_from_url("https://example.com/test.zip") == "test.zip"

        # URL with query params
        assert get_filename_from_url("https://example.com/file.tar.gz?v=1") == "file.tar.gz"

        # URL without filename
        result = get_filename_from_url("https://example.com/")
        assert result.startswith("download_")

    def test_validate_download_url(self) -> None:
        """Test URL validation."""
        # Valid URLs
        assert validate_download_url("https://example.com/file.zip") is True
        assert validate_download_url("http://example.com/file.zip") is True

        # Invalid URLs
        assert validate_download_url("ftp://example.com/file.zip") is False
        assert validate_download_url("not-a-url") is False
        assert validate_download_url("") is False
        assert validate_download_url("file:///path/to/file") is False


# 🧰🌍🔚
