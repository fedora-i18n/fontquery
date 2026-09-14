# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Tests for utils module."""

import argparse
import pytest
from unittest.mock import MagicMock, patch
from fontquery.utils import (
    normalize_release,
    build_verbose_flags,
    build_lang_flags,
    get_fontquery_client_path,
    is_inside_container,
    get_podman_command,
    run_container_query,
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


class TestIsInsideContainer:
    """Tests for is_inside_container function."""

    def test_dockerenv_present(self):
        """Test detection via /.dockerenv."""
        with patch('fontquery.utils.Path.is_file', lambda self: True):
            assert is_inside_container() is True

    def test_cgroup_libpod(self):
        """Test detection via cgroup runtime marker."""
        def fake_is_file(self):
            return str(self) == '/proc/self/cgroup'

        with patch('fontquery.utils.Path.is_file', fake_is_file), \
                patch('fontquery.utils.Path.read_text',
                      lambda self, encoding=None: '0::/libpod-abc.scope'):
            assert is_inside_container() is True

    def test_not_in_container(self):
        """Test returns False when no markers are present."""
        with patch('fontquery.utils.Path.is_file', lambda self: False):
            assert is_inside_container() is False


class TestGetPodmanCommand:
    """Tests for get_podman_command function."""

    def test_inside_container(self):
        """Test returns podman-remote inside a container."""
        with patch('fontquery.utils.is_inside_container', return_value=True):
            assert get_podman_command() == 'podman-remote'

    def test_outside_container(self):
        """Test returns podman outside a container."""
        with patch('fontquery.utils.is_inside_container', return_value=False):
            assert get_podman_command() == 'podman'


class TestRunContainerQuery:
    """Tests for run_container_query function."""

    def test_uses_podman_remote_inside_container(self):
        """Test the query command uses the resolved podman command."""
        args = argparse.Namespace(product='fedora', target='minimal',
                                  verbose=0, lang=None)
        completed = MagicMock(returncode=0, stdout=b'output')
        with patch('fontquery.utils.get_podman_command',
                   return_value='podman-remote'), \
                patch('fontquery.utils.subprocess.run',
                      return_value=completed) as mock_run:
            out = run_container_query('rawhide', args, 'json')

        assert out == 'output'
        cmdline = mock_run.call_args[0][0]
        assert cmdline[:3] == ['podman-remote', 'run', '--rm']
