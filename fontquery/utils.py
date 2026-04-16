# utils.py
# Copyright (C) 2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Shared utility functions for fontquery."""

import argparse
import re
import shutil
import subprocess
import sys
from typing import List, Optional

try:
    from fontquery import client  # noqa: F401
except ModuleNotFoundError:
    client = None


def normalize_release(release: str, product: str) -> str:
    """Normalize release name for CentOS Stream."""
    if product == 'centos' and re.match(r'\d+(\-development)?$', release):
        return 'stream' + release
    return release


def build_verbose_flags(verbose: int) -> List[str]:
    """Build verbose flags for command line."""
    if verbose > 1:
        return ['-' + ''.join(['v' * (verbose - 1)])]
    return []


def build_lang_flags(lang: Optional[List[str]]) -> List[str]:
    """Build language flags for command line."""
    if lang is None:
        return []
    return ['-l=' + ls for ls in lang]


def get_fontquery_client_path() -> str:
    """Get path to fontquery-client executable."""
    fqcexec = 'fontquery-client'
    if not shutil.which(fqcexec):
        if client is not None:
            return client.__file__
        raise RuntimeError('fontquery-client not found')
    return shutil.which(fqcexec)


def run_container_query(release: str, args: argparse.Namespace, mode: str,
                       extra_args: Optional[List[str]] = None) -> str:
    """
    Run fontquery query in container or locally.

    Args:
        release: Release name (e.g., 'rawhide', 'local', '40')
        args: Parsed command line arguments
        mode: Query mode (e.g., 'json', 'fcmatch')
        extra_args: Additional arguments to pass to query

    Returns:
        Query output as string

    Raises:
        RuntimeError: If query execution fails
    """
    release = normalize_release(release, args.product)
    extra_args = extra_args or []

    if release == 'local':
        fqcexec = get_fontquery_client_path()
        cmdline = ['python', fqcexec, '-m', mode] + \
                  build_verbose_flags(args.verbose) + \
                  build_lang_flags(args.lang) + \
                  extra_args
    else:
        cmdline = [
            'podman', 'run', '--rm',
            f'ghcr.io/fedora-i18n/fontquery/{args.product}/{args.target}:{release}',
            '-m', mode
        ] + build_verbose_flags(args.verbose) + \
            build_lang_flags(args.lang) + \
            extra_args

    if args.verbose:
        print('# ' + ' '.join(cmdline), file=sys.stderr)

    result = subprocess.run(cmdline, stdout=subprocess.PIPE, check=False)
    if result.returncode != 0:
        sys.tracebacklimit = 0
        raise RuntimeError(f'Query command failed with error code {result.returncode}')

    return result.stdout.decode('utf-8')
