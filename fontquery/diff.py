# diff.py
# Copyright (C) 2023 Red Hat, Inc.
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
"""Module to perform a diff application for fontquery."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import warnings
try:
    import _debugpath # noqa: F401
except ModuleNotFoundError:
    pass
try:
    from fontquery import container  # noqa: F401
    local_not_supported = False
except ModuleNotFoundError:
    local_not_supported = True
from fontquery import htmlformatter # noqa: F401
from pathlib import Path
from xdg import BaseDirectory

def main():
    """Endpoint to execute fontquery diff program."""
    renderer = {'html': htmlformatter.HtmlRenderer,
                'text': htmlformatter.TextRenderer}

    parser = argparse.ArgumentParser(
        description='Show difference between local and reference',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--disable-cache',
                        action='store_true',
                        help='Enforce processing everything even if not updating')
    parser.add_argument('-r',
                        '--release',
                        default='rawhide',
                        help='Release number such as "rawhide" and "39".')
    parser.add_argument('-l',
                        '--lang',
                        action='append',
                        help='Language list to dump fonts data into JSON')
    parser.add_argument('-o', '--output',
                        type=argparse.FileType('w'),
                        default='-',
                        help='Output file')
    parser.add_argument('-R', '--render',
                        default='text',
                        choices=renderer.keys())
    parser.add_argument('-t',
                        '--target',
                        default='minimal',
                        choices=['minimal', 'extra', 'all'],
                        help='Query fonts from')
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        help='Show more detailed logs')
    parser.add_argument('args', nargs='*', help='Queries')

    args = parser.parse_args()
    if local_not_supported:
        raise TypeError('local query feature is not available.')
    if not shutil.which('podman'):
        print('podman is not installed')
        sys.exit(1)

    cache = None
    out = None
    retval_a = None
    if not args.lang:
        cachedir = BaseDirectory.save_cache_path('fontquery')
        cache = Path(cachedir) / 'fedora-{}-{}.json'.format(args.release, args.target)
        try:
            with open(cache) as f:
                out = f.read()
        except FileNotFoundError:
            pass
    if args.disable_cache or not cache or not cache.exists():
        print('This may take some time...', file=sys.stderr)
        cmdline = [
            'podman', 'run', '--rm',
            'ghcr.io/fedora-i18n/fontquery/fedora/{}:{}'.format(
                args.target, args.release), '-m', 'json'
        ] + (['-' + ''.join(['v' * (args.verbose - 1)])] if args.verbose > 1
             else []) + ([] if args.lang is None else
                         [' '.join(['-l ' + ls
                                    for ls in args.lang])]) + args.args
        if args.verbose:
            print('# ' + ' '.join(cmdline))

        retval_a = subprocess.run(cmdline, stdout=subprocess.PIPE)
        out = retval_a.stdout.decode('utf-8')

    cmdline = ['fontquery-container', '-m', 'json'] + (
        ['-' + ''.join(['v' * (args.verbose - 1)])] if args.verbose > 1
        else []) + ([] if args.lang is None else
                    [' '.join(['-l ' + ls
                               for ls in args.lang])]) + args.args
    if args.verbose:
        print('# ' + ' '.join(cmdline))

    retval_b = subprocess.run(cmdline, stdout=subprocess.PIPE)

    with args.output:
        for s in htmlformatter.generate_diff(renderer[args.render](), '',
                                             json.loads(out),
                                             json.loads(retval_b.stdout.decode('utf-8'))):
            args.output.write(s)

    if cache and retval_a:
        with open(cache, 'w') as f:
            f.write(out)

if __name__ == '__main__':
    main()
