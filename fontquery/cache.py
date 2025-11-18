# Copyright (C) 2024-2025 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Module to deal with cache file"""

import os
import subprocess
import sys
from pathlib import Path
from xdg import BaseDirectory


class FontQueryCache:
    """cache handling class"""

    def __init__(self, platform, release, target):
        self._base_cachedir = BaseDirectory.save_cache_path('fontquery')
        self._cachedir = Path(self._base_cachedir) /\
            f'{platform}-{release}-{target}'
        self._repo = f'ghcr.io/fedora-i18n/fontquery/{platform}/'\
            f'{target}:{release}'
        if not self._cachedir.exists():
            self._cachedir.mkdir()

    @property
    def filename(self) -> os.PathLike:
        tag = self._get_current_revision()
        return self._cachedir / (tag + '.json')

    def _get_current_revision(self) -> str:
        cmdline = [
            'podman', 'images', '-a', '--no-trunc', self._repo
        ]
        res = subprocess.run(cmdline, capture_output=True, check=False)
        if res.returncode != 0:
            sys.tracebacklimit = 0
            raise RuntimeError('`podman images\' failed with'
                               f' the error code {res.returncode}')
        out = res.stdout.decode('utf-8')
        result = []
        for ll in out.splitlines():
            result.append(ll.split())
        if len(result) < 2:
            raise RuntimeError('No images available: {self._repo}')
        tag = result[1][[i for i in range(len(result[0]))
                         if result[0][i] == 'IMAGE'][0]]
        cmdline = [
            'podman', 'inspect', tag
        ]

        return tag

    def read(self) -> str:
        fn = None
        out = None
        try:
            fn = self.filename
        except RuntimeError:
            return None
        try:
            with open(fn, encoding='utf-8') as f:
                out = f.read()
        except FileNotFoundError:
            pass

        return out

    def save(self, s):
        fn = None
        try:
            fn = self.filename
        except RuntimeError:
            return False
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(s)

        return True

    def delete(self):
        try:
            self.filename.unlink(missing_ok=False)
        except FileNotFoundError:
            pass
