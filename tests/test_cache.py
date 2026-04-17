# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Tests for cache module."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from fontquery.cache import FontQueryCache


class TestFontQueryCache:
    """Tests for FontQueryCache class."""

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_init_creates_cache_dir(self, mock_cache_path, mock_run, tmp_path):
        """Test that initialization creates cache directory."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()  # Create the base directory first
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'sha256:abc123\n'
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')

        expected_dir = cache_base / 'fedora-40-minimal'
        assert expected_dir.exists()

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_filename_property(self, mock_cache_path, mock_run, tmp_path):
        """Test that filename property returns correct path."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'sha256:1234567890abcdef\n'
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')
        filename = cache.filename

        assert str(filename).endswith('sha256:1234567890abcdef.json')
        assert 'fedora-40-minimal' in str(filename)

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_save_and_read(self, mock_cache_path, mock_run, tmp_path):
        """Test saving and reading cache data."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'sha256:test123\n'
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')

        test_data = '{"test": "data"}'
        result = cache.save(test_data)
        assert result is True

        read_data = cache.read()
        assert read_data == test_data

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_read_nonexistent_file(self, mock_cache_path, mock_run, tmp_path):
        """Test reading nonexistent cache file returns None."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'sha256:nonexistent\n'
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')
        data = cache.read()
        assert data is None

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_delete(self, mock_cache_path, mock_run, tmp_path):
        """Test deleting cache file."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'sha256:delete_test\n'
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')

        # Save some data
        cache.save('{"test": "data"}')
        assert cache.filename.exists()

        # Delete it
        cache.delete()
        assert not cache.filename.exists()

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_podman_failure_raises_error(self, mock_cache_path, mock_run, tmp_path):
        """Test that podman command failure raises RuntimeError."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')

        with pytest.raises(RuntimeError, match='podman images.*failed'):
            _ = cache.filename

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_no_images_available_raises_error(self, mock_cache_path, mock_run, tmp_path):
        """Test that no available images raises RuntimeError."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b''
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')

        with pytest.raises(RuntimeError, match='No images available'):
            _ = cache.filename

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_save_fails_gracefully_when_podman_fails(self, mock_cache_path, mock_run, tmp_path):
        """Test that save returns False when podman fails."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')
        result = cache.save('{"test": "data"}')
        assert result is False

    @patch('subprocess.run')
    @patch('fontquery.cache.BaseDirectory.save_cache_path')
    def test_read_fails_gracefully_when_podman_fails(self, mock_cache_path, mock_run, tmp_path):
        """Test that read returns None when podman fails."""
        cache_base = tmp_path / "cache"
        cache_base.mkdir()
        mock_cache_path.return_value = str(cache_base)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        cache = FontQueryCache('fedora', '40', 'minimal')
        data = cache.read()
        assert data is None
