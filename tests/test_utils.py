# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Tests for utils module."""

import pytest
from unittest.mock import MagicMock, patch
from fontquery.utils import (
    normalize_release,
    build_verbose_flags,
    build_lang_flags,
    get_fontquery_client_path,
)


class TestNormalizeRelease:
    """Tests for normalize_release function."""

    def test_centos_numeric_release(self):
        """Test CentOS numeric release gets 'stream' prefix."""
        assert normalize_release('9', 'centos') == 'stream9'
        assert normalize_release('10', 'centos') == 'stream10'

    def test_centos_development_release(self):
        """Test CentOS development release gets 'stream' prefix."""
        assert normalize_release('9-development', 'centos') == 'stream9-development'

    def test_fedora_release_unchanged(self):
        """Test Fedora releases are not modified."""
        assert normalize_release('40', 'fedora') == '40'
        assert normalize_release('rawhide', 'fedora') == 'rawhide'

    def test_centos_rawhide_unchanged(self):
        """Test CentOS non-numeric releases are not modified."""
        assert normalize_release('rawhide', 'centos') == 'rawhide'
        assert normalize_release('stream9', 'centos') == 'stream9'


class TestBuildVerboseFlags:
    """Tests for build_verbose_flags function."""

    def test_no_verbose(self):
        """Test with verbose=0."""
        assert build_verbose_flags(0) == []

    def test_single_verbose(self):
        """Test with verbose=1."""
        assert build_verbose_flags(1) == []

    def test_double_verbose(self):
        """Test with verbose=2."""
        assert build_verbose_flags(2) == ['-v']

    def test_triple_verbose(self):
        """Test with verbose=3."""
        assert build_verbose_flags(3) == ['-vv']

    def test_multiple_verbose(self):
        """Test with verbose=5."""
        assert build_verbose_flags(5) == ['-vvvv']


class TestBuildLangFlags:
    """Tests for build_lang_flags function."""

    def test_no_languages(self):
        """Test with None."""
        assert build_lang_flags(None) == []

    def test_single_language(self):
        """Test with single language."""
        assert build_lang_flags(['en']) == ['-l=en']

    def test_multiple_languages(self):
        """Test with multiple languages."""
        result = build_lang_flags(['en', 'ja', 'zh_cn'])
        assert result == ['-l=en', '-l=ja', '-l=zh_cn']

    def test_empty_list(self):
        """Test with empty list."""
        assert build_lang_flags([]) == []


class TestGetFontqueryClientPath:
    """Tests for get_fontquery_client_path function."""

    def test_finds_executable_in_path(self):
        """Test finding fontquery-client in PATH."""
        with patch('shutil.which', return_value='/usr/bin/fontquery-client'):
            path = get_fontquery_client_path()
            assert path == '/usr/bin/fontquery-client'

    def test_fallback_to_module(self):
        """Test fallback to module __file__ when not in PATH."""
        with patch('shutil.which', return_value=None):
            with patch('fontquery.utils.client') as mock_client:
                mock_client.__file__ = '/path/to/client.py'
                path = get_fontquery_client_path()
                assert path == '/path/to/client.py'

    def test_raises_when_not_found(self):
        """Test raises RuntimeError when not found."""
        with patch('shutil.which', return_value=None):
            with patch('fontquery.utils.client', None):
                with pytest.raises(RuntimeError, match='fontquery-client not found'):
                    get_fontquery_client_path()
