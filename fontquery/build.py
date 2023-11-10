# build.py
# Copyright (C) 2022-2023 Red Hat, Inc.
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

import sys
import os
import argparse
import subprocess
import shutil
from importlib.resources import files


class ContainerImage:
    """Image Builder"""

    def __init__(self, platform: str, version: str, verbose: bool = False):
        self.__platform = platform
        self.__version = version
        self.__target = None
        self.__verbose = verbose

    def _get_namespace(self) -> str:
        if not self.__target:
            raise RuntimeError('No target is set')
        return 'fontquery/{}/{}:{}'.format(self.__platform, self.__target, self.__version)

    @property
    def target(self) -> str:
        return self.__target

    @target.setter
    def target(self, v: str) -> None:
        self.__target = v

    def exists(remote = True) -> bool:
        """Whether the image is available or not"""
        if not remote:
            cmdline = [
                'buildah', 'images', 'ghcr.io/fedora-i18n/{}'.format(self._get_namespace())
            ]
        else:
            cmdline = [
                'buildah', 'pull', 'ghcr.io/fedora-i18n/{}'.format(self._get_namespace())
            ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline), file=sys.stderr)
        try:
            subprocess.run(cmdline, check=True)
        except subprocess.CalledProcessError:
            return False
        return True

    def build(self, *args, **kwargs) -> None:
        """Build an image"""
        if self.exists(remote=False):
            print('Warning: {} is already available on local. You may want to remove older images manually.'.format(self._get_namespace()), file=sys.stderr)
        abssetup = files('fontquery.scripts').joinpath('fontquery-setup.sh')
        setuppath = str(abssetup.parent)
        setup = str(abssetup.name)
        cmdline = [
            'buildah', 'build', '-f', str(files('fontquery.data').joinpath('Containerfile.base')),
            '--build-arg', 'release={}'.format(self.__version),
            '--build-arg', 'setup={}'.format(setup),
            '--target', self.target, '-t',
            'ghcr.io/fedora-i18n/{}'.format(self._get_namespace()),
            setuppath
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            subprocess.run(cmdline)

    def update(self, *args, **kwargs) -> None:
        """Update an image"""
        if not self.exists(remote=True):
            raise RuntimeError("Image isn't yet available. try build first: {}".format(self._get_namespace()))
        abssetup = files('fontquery.scripts').joinpath('fontquery-setup.sh')
        setuppath = str(abssetup.parent)
        setup = str(abssetup.name)

    def clean(self, *args, **kwargs) -> None:
        """Clean up an image"""
        if not self.exists(remote=False):
            print("Warning: {} isn't available on local. You don't need to clean up.".format(self._get_namespace()), file=sys.stderr)
            return
        cmdline = [
            'buildah', 'rmi',
            'ghcr.io/fedora-i18n/{}'.format(self._get_namespace())
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            subprocess.run(cmdline)

    def push(self, *args, **kwargs) -> None:
        """Publish an image to registry"""
        if not self.exists(remote=False):
            print("Warning: {} isn't available on local.".format(self._get_namespace()))
            return
        cmdline = [
            'buildah', 'push',
            'ghcr.io/fedora-i18n/{}'.format(self._get_namespace())
        ]
        if self.__verbose:
            print('# ' + ' '.join(cmdline))
        if not ('try_run' in kwargs and kwargs['try_run']):
            subprocess.run(cmdline)


def main():
    """Endpoint to execute fontquery-build."""
    parser = argparse.ArgumentParser(
        description='Build fontquery image',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r',
                        '--release',
                        default='rawhide',
                        help='Release number')
    parser.add_argument('--rmi',
                        action='store_true',
                        help='Remove image before building')
    parser.add_argument('-p', '--push', action='store_true', help='Push image')
    parser.add_argument('-s',
                        '--skip-build',
                        action='store_true',
                        help='Do not build image')
    parser.add_argument('-t',
                        '--target',
                        choices=['minimal', 'extra', 'all'],
                        help='Take an action for the specific target only')
    parser.add_argument('--try-run',
                        action='store_true',
                        help='Do not take any actions')
    parser.add_argument('-u',
                        '--update',
                        action='store_true',
                        help='Do the incremental update')
    parser.add_argument('-v',
                        '--verbose',
                        action='store_true',
                        help='Show more detailed logs')

    args = parser.parse_args()

    if not os.path.isfile(files('fontquery.data').joinpath('Containerfile')):
        print('Containerfile is missing')
        sys.exit(1)

    if not shutil.which('buildah'):
        print('buildah is not installed')
        sys.exit(1)

    bldr = ContainerImage('fedora', args.release, args.verbose)
    if args.update and args.rmi:
        print('Warning: --rmi and --update option are conflict each other. Disabling --rmi.')
        args.rmi = False
    if args.skip_build and args.update:
        print('Warning: --skip-build and --update option are conflict each other. Disabling --update.')
        args.update = False
    if args.target:
        bldr.target = args.target
        if not args.skip_build:
            if args.rmi:
                bldr.clean(args)
            if args.update:
                bldr.update(args)
            else:
                bldr.build(args)
        if args.push:
            bldr.push(args)
    else:
        target = ['minimal', 'extra', 'all']
        if not args.skip_build:
            for t in target:
                bldr.target = t
                if args.rmi:
                    bldr.clean(args)
                if args.update:
                    bldr.update(args)
                else:
                    bldr.build(args)
        if args.push:
            for t in target:
                bldr.target = t
                bldr.push(args)


if __name__ == '__main__':
    main()
