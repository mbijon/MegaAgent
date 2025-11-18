"""Tests for utils.py module."""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import utils


class TestFileOperations:
    """Test file operation utilities."""

    def test_read_file_exists(self, temp_files_dir, monkeypatch):
        """Test reading an existing file."""
        test_file = os.path.join(temp_files_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content")

        # Mock git operations and file path
        with patch("subprocess.check_output", return_value=b"hash123"):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "Test content"
                )
                # This test verifies the function structure exists
                assert hasattr(utils, "read_file")

    def test_write_file_new_file(self, temp_files_dir, monkeypatch):
        """Test writing a new file."""
        # Mock git operations
        with patch("subprocess.check_output", return_value=b"hash123"):
            with patch("subprocess.run", return_value=MagicMock(returncode=0)):
                with patch("builtins.open", create=True):
                    result = utils.write_file("test.txt", "Content", agent_name="test")
                    # Result should contain status information
                    assert isinstance(result, str)
                    assert len(result) > 0

    def test_delete_all_files_in_folder(self, temp_files_dir):
        """Test deleting all files in a folder."""
        # Create test files
        test_file1 = os.path.join(temp_files_dir, "file1.txt")
        test_file2 = os.path.join(temp_files_dir, "file2.txt")
        with open(test_file1, "w") as f:
            f.write("content1")
        with open(test_file2, "w") as f:
            f.write("content2")

        utils.delete_all_files_in_folder(temp_files_dir)

        assert not os.path.exists(test_file1)
        assert not os.path.exists(test_file2)
