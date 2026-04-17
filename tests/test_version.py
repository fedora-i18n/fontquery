# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Tests for version module."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open


def test_fontquery_version():
    """Test that fontquery_version reads version.txt correctly."""
    from fontquery.version import fontquery_version

    # The actual version.txt should exist
    version = fontquery_version()
    assert isinstance(version, str)
    assert len(version) > 0
    # Version should be a non-empty string (actual format may vary)
    assert version.strip() == version  # Should be stripped


def test_fontquery_version_with_mock(tmp_path, monkeypatch):
    """Test fontquery_version with mocked file."""
    from fontquery import version as version_module

    # Create a temporary version file
    version_file = tmp_path / "version.txt"
    version_file.write_text("2.0\n")

    # Patch __file__ to point to our temp directory
    monkeypatch.setattr(version_module, '__file__', str(tmp_path / 'version.py'))

    result = version_module.fontquery_version()
    assert result == "2.0"


def test_fontquery_version_strips_whitespace(tmp_path, monkeypatch):
    """Test that version string is stripped of whitespace."""
    from fontquery import version as version_module

    # Create a temporary version file with whitespace
    version_file = tmp_path / "version.txt"
    version_file.write_text("  1.33  \n")

    # Patch __file__ to point to our temp directory
    monkeypatch.setattr(version_module, '__file__', str(tmp_path / 'version.py'))

    result = version_module.fontquery_version()
    assert result == "1.33"
    assert not result.startswith(' ')
    assert not result.endswith('\n')
