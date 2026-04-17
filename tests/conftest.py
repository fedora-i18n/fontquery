# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Pytest configuration and shared fixtures."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Provide a temporary cache directory."""
    cache_dir = tmp_path / "fontquery"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def sample_json_data():
    """Provide sample JSON data for testing."""
    return {
        "en": {
            "sans-serif": "Noto Sans",
            "serif": "Noto Serif",
            "monospace": "Noto Sans Mono"
        },
        "ja": {
            "sans-serif": "Noto Sans CJK JP",
            "serif": "Noto Serif CJK JP",
            "monospace": "Noto Sans Mono CJK JP"
        }
    }


@pytest.fixture
def sample_html_output():
    """Provide sample HTML output for testing."""
    return """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head><title>Test Fonts</title></head>
<body>
<table>
<tr><td>Test</td></tr>
</table>
</body>
</html>"""


@pytest.fixture
def mock_podman_images():
    """Mock podman images command."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'sha256:1234567890abcdef\n'
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_version_file(tmp_path):
    """Create a mock version.txt file."""
    version_file = tmp_path / "version.txt"
    version_file.write_text("1.33\n")
    return version_file
