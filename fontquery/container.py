# container.py
# Copyright (C) 2022-2024 Red Hat, Inc.
#
# Authors:
#   Akira TAGOH  <tagoh@redhat.com>
#
# Permission is hereby granted, without written agreement and without
# license or royalty fees, to use, copy, modify, and distribute this
# software and its documentation for any purpose, provided that the
# above copyright notice and the following two paragraphs appear in
# all copies of this software.
#
# IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES
# ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN
# IF THE COPYRIGHT HOLDER HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# THE COPYRIGHT HOLDER SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE.  THE SOFTWARE PROVIDED HEREUNDER IS
# ON AN "AS IS" BASIS, AND THE COPYRIGHT HOLDER HAS NO OBLIGATION TO
# PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
"""Module to build a container image for fontquery."""

import contextlib
import glob
import sys
import os
import importlib.metadata
import re
import subprocess
import shutil
import tempfile
from importlib.resources import files
from pathlib import Path
from typing import Iterator

try:
    FQ_SCRIPT_PATH = files('fontquery.scripts')
except ModuleNotFoundError:
    FQ_SCRIPT_PATH = Path(__file__).parent / 'scripts'
try:
    FQ_DATA_PATH = files('fontquery.data')
except ModuleNotFoundError:
    FQ_DATA_PATH = Path(__file__).parent / 'data'
try:
    FQ_VERSION = importlib.metadata.version('fontquery')
except ModuleNotFoundError:
    import tomli
    tomlfile = Path(__file__).parent.parent / 'pyproject.toml'
    with open(tomlfile, 'rb', encoding='utf-8') as f:
        FQ_VERSION = tomli.load(f)['project']['version']


class ContainerImage:
    """Container helper"""

    def __init__(self, product: str, version: str, verbose: bool = False):
        self.__product = product
        self.__version = version
        self.__target = None
        self.__verbose = verbose
        if product == 'fedora':
            if version == 'eln':
                self.__registry = 'quay.io/fedoraci/fedora'
            else:
                self.__registry = 'quay.io/fedora/fedora'
        elif product == 'centos':
            self.__registry = 'quay.io/centos/centos'
            if re.match(r'\d+(\-development)?$', version):
                self.__version = 'stream' + version
        else:
            raise RuntimeError('Unknown product')

    def _get_namespace(self) -> str:
        if not self.__target:
            raise RuntimeError('No target is set')
        return f'fontquery/{self.__product}/{self.__target}:{self.__version}'

    def _get_fullnamespace(self) -> str:
        return f'ghcr.io/fedora-i18n/{self._get_namespace()}'

    @property
    def target(self) -> str:
        return self.__target

    @target.setter
    def target(self, v: str) -> None:
        self.__target = v

    def exists(self, remote=True) -> bool:
        """Whether the image is available or not"""
        if not remote:
            cmdline = [
                'buildah', 'images', self._get_fullnamespace()
            ]
        else:
            cmdline = [
                'buildah', 'pull', self._get_fullnamespace()
            ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline), file=sys.stderr)
        try:
            subprocess.run(cmdline, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            return False
        return True

    def pull(self, *args, **kwargs) -> bool:
        cmdline = [
            'podman', 'pull', self._get_fullnamespace()
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            ret = subprocess.run(cmdline, capture_output=True, check=False)
            return ret.returncode == 0

        return True

    def build(self, *args, **kwargs) -> bool:
        """Build an image"""
        retval = True
        if self.exists(remote=False):
            print(f'Warning: {self._get_namespace()} is already'
                  ' available on local. '
                  'You may want to remove older images manually.',
                  file=sys.stderr)
        with tempfile.TemporaryDirectory() as tmpdir:
            abssetup = FQ_SCRIPT_PATH.joinpath('fontquery-setup.sh')
            setup = str(abssetup.name)
            devpath = Path(__file__).parents[1]
            sdist = str(devpath / 'dist' / f'fontquery-{FQ_VERSION}*.whl')
            dist = '' if 'debug' not in kwargs or not kwargs['debug']\
                else glob.glob(sdist)[0]
            containerfile = str(FQ_DATA_PATH.joinpath('Containerfile'))
            if dist:
                # Use all files from development
                containerfile = str(devpath / 'fontquery' / 'data' /
                                    'Containerfile')
                abssetup = str(devpath / 'fontquery' / 'scripts' /
                               'fontquery-setup.sh')
                shutil.copy2(dist, tmpdir)
            shutil.copy2(abssetup, tmpdir)
            cmdline = [
                'buildah', 'build', '-f', containerfile,
                '--build-arg', f'registry={self.__registry}',
                '--build-arg', f'release={self.__version}',
                '--build-arg', f'setup={setup}',
                '--build-arg', f'dist={Path(dist).name}',
                '--target', self.target, '-t',
                f'ghcr.io/fedora-i18n/{self._get_namespace()}',
                tmpdir
            ]
            if self.__verbose:
                print('# ' + ' '.join(cmdline))
            if not ('try_run' in kwargs and kwargs['try_run']):
                ret = subprocess.run(cmdline, cwd=tmpdir, check=False)
                retval = ret.returncode == 0

        return retval

    def clean(self, *args, **kwargs) -> None:
        """Clean up an image"""
        if not self.exists(remote=False):
            print(f"Warning: {self._get_namespace()} isn't available on local."
                  " You don't need to clean up.",
                  file=sys.stderr)
            return
        cmdline = [
            'buildah', 'rmi',
            f'ghcr.io/fedora-i18n/{self._get_namespace()}'
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            subprocess.run(cmdline, check=False)

    def push(self, *args, **kwargs) -> bool:
        """Publish an image to registry"""
        if not self.exists(remote=False):
            print(f"Warning: {self._get_namespace()} isn't"
                  " available on local.")
            return False
        cmdline = [
            'buildah', 'push',
            f'ghcr.io/fedora-i18n/{self._get_namespace()}'
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            ret = subprocess.run(cmdline, check=False)
            return ret.returncode == 0

        return True

    @contextlib.contextmanager
    def _create(self, endpoint_args=[], interactive=False, *args, **kwargs) -> Iterator[str]:
        """Create a container"""
        if not self.exists(remote=True):
            raise RuntimeError("Image isn't yet available. "
                               f"try build first: {self._get_namespace()}")
        if endpoint_args is None:
            endpoint_args = []
        cname = f'fontquery-{os.getpid()}'
        cmdline = [
            'podman', 'create', '-i', '--name', cname
        ]
        if interactive:
            cmdline += ['--entrypoint', '/bin/bash']
        cmdline += [self._get_fullnamespace()]
        cmdline += endpoint_args
        cleancmdline = [
            'podman', 'rm', '-f', cname
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            try:
                res = subprocess.run(cmdline, capture_output=True, check=False)
                if res.returncode == 0:
                    yield cname
            finally:
                if self.__verbose:
                    print('# ' + ' '.join(cleancmdline))
                subprocess.run(cleancmdline, capture_output=True, check=False)

    def _start(self, session='', *args, **kwargs) -> subprocess.CompletedProcess[str]:
        """Start a container"""
        cmdline = f'podman start -a {session}'
        if self.__verbose:
            print('# ' + cmdline)
        res = subprocess.run(cmdline, stdout=subprocess.PIPE,
                             check=False, shell=True)
        return res

    def _exec(self, session='', cmd='/bin/bash', stderr=None, *args, **kwargs) -> subprocess.CompletedProcess[str]:
        """Execute in a container"""
        cmdline = f'podman start {session} > /dev/null;'\
            f' podman exec -i {session} {cmd}'
        if self.__verbose:
            print('# ' + cmdline)
        res = subprocess.run(cmdline, stdout=subprocess.PIPE, stderr=stderr,
                             check=False, shell=True)
        return res

    def _commit(self, session='', *args, **kwargs) -> None:
        """Commit changes in container"""
        cmdline = [
            'podman', 'commit', session,
            self._get_fullnamespace()
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            res = subprocess.run(cmdline, check=False)
            if res.returncode == 0:
                print('** Image has been changed.', file=sys.stderr)
            else:
                print('** Failed to change image.', file=sys.stderr)

    def _copy(self, session='', files=[]) -> bool:
        """Copy files into container"""
        res = subprocess.run(['podman', 'unshare', 'podman', 'mount', session],
                             capture_output=True, check=False)
        if res.returncode != 0:
            print('** Unable to get a working container\'s directory',
                  file=sys.stderr)
            return False
        mnt = res.stdout.decode('utf-8').rstrip('\r\n')
        try:
            cmdline = [
                'podman', 'unshare', 'cp', '-a'
            ] + files + [str(Path(mnt) / 'var' / 'tmp' / 'fontquery')]
            if self.__verbose:
                print('# ' + ' '.join(cmdline))
            res = subprocess.run(cmdline, capture_output=True, check=True)
            if res.returncode != 0:
                print('** Unable to copy files into a container',
                      file=sys.stderr)
                return False
        finally:
            subprocess.run(['podman', 'unshare', 'podman', 'umount', session],
                           capture_output=True, check=False)
        return True

    def update(self, *args, **kwargs) -> bool:
        """Update an image"""
        if not self.exists(remote=True):
            raise RuntimeError("Image isn't yet available. "
                               f"try build first: {self._get_namespace()}")
        with self._create(endpoint_args=['-m', 'checkupdate'], *args, **kwargs) as cname:
            res = self._start(session=cname)
            if res.returncode == 0:
                return False
        if not ('try_run' in kwargs and kwargs['try_run']):
            with self._create(endpoint_args=['-m', 'update'], *args, **kwargs) as cname:
                res = self._start(session=cname)
                if res.returncode != 0:
                    print('** Updating image failed.', file=sys.stderr)
                    return False

                self._commit(cname)

        return True

    def get_json(self, *args, **kwargs) -> str:
        """Get JSON from a container"""
        if not self.exists(remote=True):
            raise RuntimeError("Image isn't yet available. "
                               f"try build first: {self._get_namespace()}")
        eargs = ['-m', 'json']
        if 'lang' in kwargs and kwargs['lang'] is not None:
            a = ['-l=' + ls for ls in kwargs['lang']]
            eargs += a
        if 'verbose' in kwargs and kwargs['verbose'] > 1:
            eargs.append('-' + ''.join(['v' * (kwargs['verbose'] - 1)]))
        if 'extra_args' in kwargs and kwargs['extra_args']:
            eargs += kwargs['extra_args']
        with self._create(endpoint_args=eargs, *args, **kwargs) as cname:
            res = self._start(session=cname)
            if res.returncode != 0:
                sys.tracebacklimit = 0
                raise RuntimeError('`podman run\' failed with '
                                   f'the error code {res.returncode}')
            return res.stdout.decode('utf-8')

    def get_json_after_install(self, package, *args, **kwargs) -> str:
        """Get JSON from a container after installing a package"""
        if not self.exists(remote=True):
            raise RuntimeError("Image isn't yet available. "
                               f"try build first: {self._get_namespace()}")
        eargs = ['-m', 'json']
        if 'lang' in kwargs and kwargs['lang'] is not None:
            a = ['-l=' + ls for ls in kwargs['lang']]
            eargs += a
        if 'verbose' in kwargs and kwargs['verbose'] > 1:
            eargs.append('-' + ''.join(['v' * (kwargs['verbose'] - 1)]))
        if 'extra_args' in kwargs and kwargs['extra_args']:
            eargs += kwargs['extra_args']

        with self._create(interactive=True, *args, **kwargs) as cname:
            cmdline = [
                'podman', 'cp', None, None
            ]
            print('* Copying packages...', file=sys.stderr)
            if not self._copy(cname, package):
                return None
            print('* Installing packages...', file=sys.stderr)
            pkgs = ' '.join([Path(f).name for f in package])
            res = self._exec(session=cname,
                             stderr=subprocess.PIPE,
                             cmd='/usr/local/bin/fontquery-client '
                             f'-m install {pkgs}')
            if res.returncode != 0:
                print('** Unable to install package', file=sys.stderr)
                return None
            res = self._exec(session=cname,
                             cmd='/usr/local/bin/fontquery-client ' +
                             ' '.join(eargs))
            if res.returncode != 0:
                print('** Unable to get a JSON', file=sys.stderr)
                return None
            return res.stdout.decode('utf-8')
