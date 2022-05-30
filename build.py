#! /usr/bin/python3
# build.py
# Copyright (C) 2022 Red Hat, Inc.
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

import sys
import os
import argparse
import subprocess
import shutil

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Build fontquery image',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--release',
                        default='rawhide',
                        help='Release number')
    parser.add_argument('-p', '--push',
                        action='store_true',
                        help='Push image')
    parser.add_argument('-s', '--skip-build',
                        action='store_true',
                        help='Do not build image')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Show more detailed logs')

    args = parser.parse_args()

    if not os.path.isfile('Dockerfile'):
        print('Dockerfile is missing')
        sys.exit(1)

    if not shutil.which('buildah'):
        print('buildah is not installed')
        sys.exit(1)

    cmdline = ['buildah', 'build', '-f', 'Dockerfile', '--build-arg', 'release={}'.format(args.release), '-t', 'ghcr.io/fedora-i18n/fontquery:{}'.format(args.release)]
    if args.verbose:
        print('# '+' '.join(cmdline))
    if not args.skip_build:
        subprocess.run(cmdline)

    cmdline = ['buildah', 'push', 'ghcr.io/fedora-i18n/fontquery:{}'.format(args.release)]
    if args.verbose:
        print('# '+' '.join(cmdline))
    if args.push:
        subprocess.run(cmdline)
