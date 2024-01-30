# Copyright (C) 2024 Red Hat, Inc.
# SPDX-License-Identifier: MIT

"""Module to deal with cache file"""

import os
import subprocess
from pathlib import Path
from xdg import BaseDirectory


class FontQueryCache:
    """cache handling class"""

    def __init__(self, platform, release, target):
        self._base_cachedir = BaseDirectory.save_cache_path('fontquery')
        self._cachedir = Path(self._base_cachedir) / '{}-{}-{}'.format(platform, release, target)
        self._repo = 'ghcr.io/fedora-i18n/fontquery/{}/{}:{}'.format(platform, target, release)
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
        out = subprocess.run(cmdline, stdout=subprocess.PIPE).stdout.decode('utf-8')
        result = []
        for l in out.splitlines():
            result.append(l.split())
        if len(result) < 2:
            raise RuntimeError('No images available: {}'.format(self._repo))
        tag = result[1][[i for i in range(len(result[0])) if result[0][i] == 'IMAGE'][0]]
        cmdline = [
            'podman', 'inspect', tag
        ]

        return tag
