#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for Install Operations
=============================
Tests for the install functionality in wrknv."""

from __future__ import annotations

import stat
import tarfile
import zipfile

from provide.testkit.mocking import patch
import pytest

from wrknv.wenv.operations.install import (
    clean_directory,
    copy_file,
    create_symlink,
    ensure_directory,
    extract_archive,
    get_file_size,
    is_executable,
    make_executable,
)


class TestExtractOperations:
    """Test archive extraction functionality."""

    def test_extract_archive_zip(self, tmp_path) -> None:
        """Test extracting ZIP archive."""
        # Create a test ZIP file
        archive_path = tmp_path / "test.zip"
        extract_dir = tmp_path / "extract"

        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("test.txt", "Hello World")
            zf.writestr("subdir/file.txt", "Nested file")

        # Extract archive
        extract_archive(archive_path, extract_dir)

        # Verify files were extracted
        assert (extract_dir / "test.txt").exists()
        assert (extract_dir / "test.txt").read_text() == "Hello World"
        assert (extract_dir / "subdir" / "file.txt").exists()
        assert (extract_dir / "subdir" / "file.txt").read_text() == "Nested file"

    def test_extract_archive_tar_gz(self, tmp_path) -> None:
        """Test extracting tar.gz archive."""
        # Create a test tar.gz file
        archive_path = tmp_path / "test.tar.gz"
        extract_dir = tmp_path / "extract"

        # Create test files
        test_dir = tmp_path / "test_content"
        test_dir.mkdir()
        (test_dir / "test.txt").write_text("Hello World")
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("Nested file")

        # Create tar.gz archive
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(test_dir / "test.txt", arcname="test.txt")
            tf.add(subdir / "file.txt", arcname="subdir/file.txt")

        # Extract archive
        extract_archive(archive_path, extract_dir)

        # Verify files were extracted
        assert (extract_dir / "test.txt").exists()
        assert (extract_dir / "test.txt").read_text() == "Hello World"
        assert (extract_dir / "subdir" / "file.txt").exists()
        assert (extract_dir / "subdir" / "file.txt").read_text() == "Nested file"

    def test_extract_archive_tar(self, tmp_path) -> None:
        """Test extracting plain tar archive."""
        # Create a test tar file
        archive_path = tmp_path / "test.tar"
        extract_dir = tmp_path / "extract"

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        # Create tar archive
        with tarfile.open(archive_path, "w") as tf:
            tf.add(test_file, arcname="test.txt")

        # Extract archive
        extract_archive(archive_path, extract_dir)

        # Verify file was extracted
        assert (extract_dir / "test.txt").exists()
        assert (extract_dir / "test.txt").read_text() == "Hello World"

    def test_extract_archive_nonexistent(self, tmp_path) -> None:
        """Test extracting non-existent archive."""
        from provide.foundation.errors import ResourceError

        archive_path = tmp_path / "nonexistent.zip"
        extract_dir = tmp_path / "extract"

        with pytest.raises(ResourceError, match="Archive not found"):
            extract_archive(archive_path, extract_dir)

    def test_extract_archive_unsupported(self, tmp_path) -> None:
        """Test extracting unsupported archive type."""
        archive_path = tmp_path / "test.unknown"
        archive_path.write_text("Not an archive")
        extract_dir = tmp_path / "extract"

        with pytest.raises(Exception, match="Unsupported archive format"):
            extract_archive(archive_path, extract_dir)

    def test_extract_archive_path_traversal_zip(self, tmp_path) -> None:
        """Test ZIP extraction prevents path traversal."""
        archive_path = tmp_path / "malicious.zip"
        extract_dir = tmp_path / "extract"

        # Create malicious ZIP with path traversal
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("../evil.txt", "Evil content")

        with pytest.raises(Exception, match="Unsafe path in archive"):
            extract_archive(archive_path, extract_dir)

    def test_extract_archive_path_traversal_tar(self, tmp_path) -> None:
        """Test TAR extraction prevents path traversal."""
        archive_path = tmp_path / "malicious.tar.gz"
        extract_dir = tmp_path / "extract"

        # Create malicious tar.gz
        import io

        with tarfile.open(archive_path, "w:gz") as tf:
            # Add file with malicious name
            info = tarfile.TarInfo(name="../evil.txt")
            content = b"Evil content"
            info.size = len(content)
            tf.addfile(info, fileobj=io.BytesIO(content))

        with pytest.raises(Exception, match="Unsafe path in archive"):
            extract_archive(archive_path, extract_dir)


class TestExecutableOperations:
    """Test executable-related operations."""

    def test_make_executable_unix(self, tmp_path) -> None:
        """Test making file executable on Unix."""
        test_file = tmp_path / "script.sh"
        test_file.write_text("#!/bin/sh\necho hello")

        # Ensure file is not executable initially
        test_file.chmod(0o644)

        with patch("platform.system", return_value="Linux"):
            make_executable(test_file)

        # Check file is now executable
        assert test_file.stat().st_mode & stat.S_IXUSR
        assert test_file.stat().st_mode & stat.S_IXGRP
        assert test_file.stat().st_mode & stat.S_IXOTH

    def test_make_executable_windows(self, tmp_path) -> None:
        """Test making file executable on Windows (no-op)."""
        test_file = tmp_path / "script.bat"
        test_file.write_text("echo hello")

        initial_mode = test_file.stat().st_mode

        with patch("platform.system", return_value="Windows"):
            make_executable(test_file)

        # Mode should not change on Windows
        assert test_file.stat().st_mode == initial_mode

    def test_make_executable_nonexistent(self, tmp_path) -> None:
        """Test making non-existent file executable."""
        from provide.foundation.errors import ResourceError

        test_file = tmp_path / "nonexistent.sh"

        with pytest.raises(ResourceError, match="File not found"):
            make_executable(test_file)

    def test_is_executable_unix(self, tmp_path) -> None:
        """Test checking if file is executable on Unix."""
        test_file = tmp_path / "script.sh"
        test_file.write_text("#!/bin/sh\necho hello")

        with patch("platform.system", return_value="Linux"):
            # Not executable initially
            test_file.chmod(0o644)
            assert not is_executable(test_file)

            # Make executable
            test_file.chmod(0o755)
            assert is_executable(test_file)

    def test_is_executable_windows(self, tmp_path) -> None:
        """Test checking if file is executable on Windows."""
        with patch("platform.system", return_value="Windows"):
            # .exe file should be executable
            exe_file = tmp_path / "program.exe"
            exe_file.write_text("binary")
            assert is_executable(exe_file)

            # .bat file should be executable
            bat_file = tmp_path / "script.bat"
            bat_file.write_text("echo hello")
            assert is_executable(bat_file)

            # .txt file should not be executable
            txt_file = tmp_path / "readme.txt"
            txt_file.write_text("readme")
            assert not is_executable(txt_file)

    def test_is_executable_nonexistent(self, tmp_path) -> None:
        """Test checking if non-existent file is executable."""
        test_file = tmp_path / "nonexistent.sh"
        assert not is_executable(test_file)


class TestFileOperations:
    """Test file operation functionality."""

    def test_copy_file_success(self, tmp_path) -> None:
        """Test successful file copy."""
        source = tmp_path / "source.txt"
        source.write_text("Hello World")
        source.chmod(0o755)

        dest = tmp_path / "dest" / "target.txt"

        copy_file(source, dest)

        # Verify file was copied
        assert dest.exists()
        assert dest.read_text() == "Hello World"
        # Permissions should be preserved by default
        assert dest.stat().st_mode == source.stat().st_mode

    def test_copy_file_no_preserve_permissions(self, tmp_path) -> None:
        """Test file copy without preserving permissions."""
        source = tmp_path / "source.txt"
        source.write_text("Hello World")
        source.chmod(0o755)

        dest = tmp_path / "target.txt"

        copy_file(source, dest, preserve_permissions=False)

        # Verify file was copied
        assert dest.exists()
        assert dest.read_text() == "Hello World"
        # Permissions might differ

    def test_copy_file_nonexistent_source(self, tmp_path) -> None:
        """Test copying non-existent file."""
        source = tmp_path / "nonexistent.txt"
        dest = tmp_path / "dest.txt"

        with pytest.raises(FileNotFoundError, match="Source file does not exist"):
            copy_file(source, dest)

    def test_create_symlink_success(self, tmp_path) -> None:
        """Test creating symbolic link."""
        target = tmp_path / "target.txt"
        target.write_text("Hello World")

        link = tmp_path / "link.txt"

        create_symlink(target, link)

        # Verify symlink was created
        assert link.exists()
        assert link.is_symlink()
        assert link.read_text() == "Hello World"

    def test_create_symlink_overwrites_existing(self, tmp_path) -> None:
        """Test creating symlink overwrites existing link."""
        target1 = tmp_path / "target1.txt"
        target1.write_text("First")

        target2 = tmp_path / "target2.txt"
        target2.write_text("Second")

        link = tmp_path / "link.txt"

        # Create first link
        create_symlink(target1, link)
        assert link.read_text() == "First"

        # Overwrite with second link
        create_symlink(target2, link)
        assert link.read_text() == "Second"

    def test_create_symlink_nonexistent_target(self, tmp_path) -> None:
        """Test creating symlink to non-existent target."""
        from provide.foundation.errors import ResourceError

        target = tmp_path / "nonexistent.txt"
        link = tmp_path / "link.txt"

        with pytest.raises(ResourceError, match="Target does not exist"):
            create_symlink(target, link)

    def test_create_symlink_windows_fallback(self, tmp_path) -> None:
        """Test symlink falls back to copy on Windows."""
        target = tmp_path / "target.txt"
        target.write_text("Hello World")

        link = tmp_path / "link.txt"

        with (
            patch("platform.system", return_value="Windows"),
            patch("pathlib.Path.symlink_to", side_effect=OSError("Permission denied")),
        ):
            create_symlink(target, link)

        # Should have copied instead
        assert link.exists()
        assert not link.is_symlink()
        assert link.read_text() == "Hello World"

    def test_get_file_size(self, tmp_path) -> None:
        """Test getting file size."""
        test_file = tmp_path / "test.txt"
        content = "Hello World"
        test_file.write_text(content)

        size = get_file_size(test_file)
        assert size == len(content)

    def test_get_file_size_nonexistent(self, tmp_path) -> None:
        """Test getting size of non-existent file."""
        from provide.foundation.errors import ResourceError

        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(ResourceError, match="File not found"):
            get_file_size(test_file)


class TestDirectoryOperations:
    """Test directory operation functionality."""

    def test_ensure_directory_creates_new(self, tmp_path) -> None:
        """Test ensuring directory creates new directory."""
        test_dir = tmp_path / "new" / "nested" / "dir"

        ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_existing(self, tmp_path) -> None:
        """Test ensuring directory with existing directory."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()

        # Should not raise error
        ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_file_exists(self, tmp_path) -> None:
        """Test ensuring directory when file exists at path."""
        test_path = tmp_path / "file.txt"
        test_path.write_text("I'm a file")

        with pytest.raises(Exception, match="Path exists but is not a directory"):
            ensure_directory(test_path)

    def test_clean_directory_removes_files(self, tmp_path) -> None:
        """Test cleaning directory removes files."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create files and subdirs
        (test_dir / "file1.txt").write_text("content")
        (test_dir / "file2.txt").write_text("content")
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("content")

        clean_directory(test_dir)

        # Directory should exist but be empty
        assert test_dir.exists()
        assert len(list(test_dir.iterdir())) == 0

    def test_clean_directory_keeps_hidden(self, tmp_path) -> None:
        """Test cleaning directory keeps hidden files by default."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create files
        (test_dir / "file.txt").write_text("content")
        (test_dir / ".hidden").write_text("hidden")

        clean_directory(test_dir, keep_hidden=True)

        # Only hidden file should remain
        assert not (test_dir / "file.txt").exists()
        assert (test_dir / ".hidden").exists()

    def test_clean_directory_remove_hidden(self, tmp_path) -> None:
        """Test cleaning directory can remove hidden files."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create files
        (test_dir / "file.txt").write_text("content")
        (test_dir / ".hidden").write_text("hidden")

        clean_directory(test_dir, keep_hidden=False)

        # All files should be removed
        assert len(list(test_dir.iterdir())) == 0

    def test_clean_directory_nonexistent(self, tmp_path) -> None:
        """Test cleaning non-existent directory."""
        test_dir = tmp_path / "nonexistent"

        # Should not raise error
        clean_directory(test_dir)

    def test_clean_directory_not_directory(self, tmp_path) -> None:
        """Test cleaning path that's not a directory."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("I'm a file")

        with pytest.raises(Exception, match="Path is not a directory"):
            clean_directory(test_file)


# 🧰🌍🔚
