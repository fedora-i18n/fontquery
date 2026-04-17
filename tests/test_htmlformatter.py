# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Tests for htmlformatter module."""

import pytest
from fontquery.htmlformatter import (
    get_for_alias,
    get_family_for_alias,
    get_lang_for_alias,
    get_file_for_alias,
)


class TestHelperFunctions:
    """Tests for helper functions in htmlformatter."""

    def test_get_for_alias_exists(self):
        """Test getting property value when it exists."""
        value = {
            'sans-serif': {
                'family': 'Noto Sans',
                'lang': 'en',
                'file': '/path/to/font.ttf'
            }
        }
        result = get_for_alias(value, 'sans-serif', 'family')
        assert result == 'Noto Sans'

    def test_get_for_alias_missing_symbol(self):
        """Test getting property when symbol doesn't exist."""
        value = {
            'sans-serif': {
                'family': 'Noto Sans'
            }
        }
        result = get_for_alias(value, 'serif', 'family')
        assert result == ''

    def test_get_for_alias_missing_property(self):
        """Test getting property when property doesn't exist."""
        value = {
            'sans-serif': {
                'family': 'Noto Sans'
            }
        }
        result = get_for_alias(value, 'sans-serif', 'lang')
        assert result == ''

    def test_get_family_for_alias(self):
        """Test getting family name."""
        value = {
            'sans-serif': {
                'family': 'Noto Sans',
                'lang': 'en'
            }
        }
        result = get_family_for_alias(value, 'sans-serif')
        assert result == 'Noto Sans'

    def test_get_lang_for_alias(self):
        """Test getting language."""
        value = {
            'sans-serif': {
                'family': 'Noto Sans',
                'lang': 'ja'
            }
        }
        result = get_lang_for_alias(value, 'sans-serif')
        assert result == 'ja'

    def test_get_file_for_alias(self):
        """Test getting file path."""
        value = {
            'serif': {
                'family': 'Noto Serif',
                'file': '/usr/share/fonts/noto/NotoSerif-Regular.ttf'
            }
        }
        result = get_file_for_alias(value, 'serif')
        assert result == '/usr/share/fonts/noto/NotoSerif-Regular.ttf'

    def test_get_for_alias_empty_dict(self):
        """Test getting from empty dictionary."""
        value = {}
        result = get_for_alias(value, 'sans-serif', 'family')
        assert result == ''

    def test_get_family_for_alias_multiple_fonts(self):
        """Test getting family when multiple aliases exist."""
        value = {
            'sans-serif': {'family': 'Noto Sans'},
            'serif': {'family': 'Noto Serif'},
            'monospace': {'family': 'Noto Sans Mono'}
        }
        assert get_family_for_alias(value, 'sans-serif') == 'Noto Sans'
        assert get_family_for_alias(value, 'serif') == 'Noto Serif'
        assert get_family_for_alias(value, 'monospace') == 'Noto Sans Mono'
