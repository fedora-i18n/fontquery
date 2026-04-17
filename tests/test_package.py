# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Tests for package module."""

import pytest
from unittest.mock import MagicMock, patch
from fontquery.package import (
    FqException,
    NotSupported,
    PackageNotFound,
    NoPackageManager,
    NoPackageRepo,
    NoBranchInPackageRepo,
    InvalidFormat,
    Font2Package,
)


class TestExceptions:
    """Tests for custom exception classes."""

    def test_fq_exception_default_message(self):
        """Test FqException with default message."""
        exc = FqException()
        assert str(exc) == ""

    def test_fq_exception_custom_message(self):
        """Test FqException with custom message."""
        exc = FqException(msg="Custom error: {}")
        assert "Custom error" in str(exc)

    def test_not_supported(self):
        """Test NotSupported exception."""
        with pytest.raises(NotSupported, match="no supported package manager"):
            raise NotSupported()

    def test_package_not_found(self):
        """Test PackageNotFound exception."""
        with pytest.raises(PackageNotFound, match="package not found"):
            raise PackageNotFound()

    def test_no_package_manager(self):
        """Test NoPackageManager exception."""
        with pytest.raises(NoPackageManager, match="no package manager is installed"):
            raise NoPackageManager()

    def test_no_package_repo(self):
        """Test NoPackageRepo exception."""
        with pytest.raises(NoPackageRepo, match="no such package repositories"):
            raise NoPackageRepo()

    def test_no_branch_in_package_repo(self):
        """Test NoBranchInPackageRepo exception."""
        with pytest.raises(NoBranchInPackageRepo, match="no such branches"):
            raise NoBranchInPackageRepo()

    def test_invalid_format(self):
        """Test InvalidFormat exception."""
        with pytest.raises(InvalidFormat, match="Invalid fmf format"):
            raise InvalidFormat()


class TestFont2Package:
    """Tests for Font2Package class."""

    @patch('subprocess.run')
    def test_get_source_package_name_single(self, mock_run):
        """Test getting source package name for a single package."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'1.0-1.fc40|google-noto-fonts-1.0-1.fc40.src.rpm'
        mock_run.return_value = mock_result

        result = list(Font2Package.get_source_package_name('google-noto-sans-fonts'))
        assert result == ['google-noto-fonts']

    @patch('subprocess.run')
    def test_get_source_package_name_list(self, mock_run):
        """Test getting source package names for multiple packages."""
        mock_result1 = MagicMock()
        mock_result1.returncode = 0
        mock_result1.stdout = b'1.0-1.fc40|google-noto-fonts-1.0-1.fc40.src.rpm'

        mock_result2 = MagicMock()
        mock_result2.returncode = 0
        mock_result2.stdout = b'2.0-1.fc40|liberation-fonts-2.0-1.fc40.src.rpm'

        mock_run.side_effect = [mock_result1, mock_result2]

        packages = ['google-noto-sans-fonts', 'liberation-sans-fonts']
        result = list(Font2Package.get_source_package_name(packages))
        assert result == ['google-noto-fonts', 'liberation-fonts']

    @patch('subprocess.run')
    def test_get_source_package_name_not_found(self, mock_run):
        """Test getting source package name when package not found."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        with pytest.raises(PackageNotFound):
            list(Font2Package.get_source_package_name('nonexistent-package'))

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_package_name_from_file(self, mock_run, mock_which):
        """Test getting package name from font file."""
        mock_which.return_value = '/usr/bin/rpm'
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'google-noto-sans-fonts'
        mock_run.return_value = mock_result

        result = list(Font2Package.get_package_name_from_file('/path/to/font.ttf'))
        assert result == ['google-noto-sans-fonts']

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_package_name_from_file_not_found(self, mock_run, mock_which):
        """Test getting package name when file not owned by package."""
        mock_which.return_value = '/usr/bin/rpm'
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        with pytest.raises(PackageNotFound):
            list(Font2Package.get_package_name_from_file('/path/to/font.ttf'))

    @patch('shutil.which')
    def test_get_package_name_from_file_no_rpm(self, mock_which):
        """Test getting package name when rpm is not available."""
        mock_which.return_value = None

        with pytest.raises(NotSupported):
            list(Font2Package.get_package_name_from_file('/path/to/font.ttf'))

    @patch('subprocess.run')
    def test_get_source_package_name_complex_version(self, mock_run):
        """Test parsing source package with complex version string."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'20230101-5.fc40|google-noto-cjk-fonts-20230101-5.fc40.src.rpm'
        mock_run.return_value = mock_result

        result = list(Font2Package.get_source_package_name('google-noto-sans-cjk-jp-fonts'))
        assert result == ['google-noto-cjk-fonts']
