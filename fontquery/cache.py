# Copyright (C) 2024-2026 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Module to deal with cache file"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from xdg import BaseDirectory


class FontQueryCache:
    """cache handling class"""

    def __init__(self, platform: str, release: str, target: str) -> None:
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
        res = subprocess.run(
            ['podman', 'images', '-a', '--no-trunc', '--format', '{{.ID}}',
             self._repo],
            capture_output=True, check=False)
        if res.returncode != 0:
            sys.tracebacklimit = 0
            raise RuntimeError(f'`podman images\' failed with '
                               f'the error code {res.returncode}')
        lines = res.stdout.decode('utf-8').strip().splitlines()
        if not lines:
            raise RuntimeError(f'No images available: {self._repo}')
        return lines[0]

    def read(self) -> Optional[str]:
        try:
            fn = self.filename
        except RuntimeError:
            return None
        try:
            return fn.read_text(encoding='utf-8')
        except FileNotFoundError:
            return None

    def save(self, s: str) -> bool:
        try:
            fn = self.filename
        except RuntimeError:
            return False
        fn.write_text(s, encoding='utf-8')
        return True

    def delete(self) -> None:
        try:
            self.filename.unlink(missing_ok=True)
        except RuntimeError:
            pass
