# build.py
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

import sys
import os
import argparse
import shutil
try:
    import fontquery_debug  # noqa: F401
except ModuleNotFoundError:
    pass
from fontquery import container  # noqa: F401


def do_build(product, release, target, push, args):
    bldr = container.ContainerImage(product, release, args.verbose)
    bldr.target = target
    if not args.skip_build:
        if args.rmi:
            bldr.clean(**vars(args))
        if args.update:
            if not bldr.update(**vars(args)):
                return False
        else:
            if not bldr.build(**vars(args)):
                return False
    if push:
        if not bldr.push(**vars(args)):
            return False
    return True


def do_push(product, release, target, args):
    bldr = container.ContainerImage(product, release, args.verbose)
    bldr.target = target
    if not bldr.push(**vars(args)):
        return False
    return True


def main():
    """Endpoint to execute fontquery-build."""
    parser = argparse.ArgumentParser(
        description='Build fontquery image',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument('-r',
                        '--release',
                        default='rawhide',
                        help='Release number')
    parser.add_argument('--rmi',
                        action='store_true',
                        help='Remove image before building')
    parser.add_argument('-P', '--product',
                        default='fedora',
                        choices=['fedora', 'centos'],
                        help='Product name to build image'
                        )
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
    parser.add_argument('-V',
                        '--version',
                        action='store_true',
                        help='Show version')

    args = parser.parse_args()

    if args.version:
        print(container.FQ_VERSION)
        sys.exit(0)
    if not os.path.isfile(container.FQ_DATA_PATH.joinpath('Containerfile')):
        print('Containerfile is missing')
        sys.exit(1)

    if not shutil.which('buildah'):
        print('buildah is not installed')
        sys.exit(1)

    if args.update and args.rmi:
        print('Warning: --rmi and --update option are conflict each other.'
              ' Disabling --rmi.')
        args.rmi = False
    if args.skip_build and args.update:
        print('Warning: --skip-build and --update option are conflict each'
              ' other. Disabling --update.')
        args.update = False
    if args.target:
        if not do_build(args.product, args.release, args.target,
                        args.push, args):
            sys.exit(1)
    else:
        target = ['minimal', 'extra', 'all']
        for t in target:
            if not do_build(args.product, args.release, t, False, args):
                sys.exit(1)
        if args.push:
            for t in target:
                if not do_push(args.product, args.release, t, args):
                    sys.exit(1)


if __name__ == '__main__':
    main()
