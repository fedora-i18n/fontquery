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
from fontquery.cache import FontQueryCache # noqa: F401
from pathlib import Path
from xdg import BaseDirectory

def get_json(release, args):
    if release == 'local':
        cmdline = ['fontquery-container', '-m', 'json'] + (
            ['-' + ''.join(['v' * (args.verbose - 1)])] if args.verbose > 1
            else []) + ([] if args.lang is None else
                        [' '.join(['-l=' + ls
                                   for ls in args.lang])])
    else:
        print('* This may take some time...', file=sys.stderr)
        cmdline = [
            'podman', 'run', '--rm',
            'ghcr.io/fedora-i18n/fontquery/fedora/{}:{}'.format(
                args.target, release), '-m', 'json'
        ] + (['-' + ''.join(['v' * (args.verbose - 1)])] if args.verbose > 1
             else []) + ([] if args.lang is None else
                         [' '.join(['-l=' + ls
                                    for ls in args.lang])])

    if args.verbose:
        print('# ' + ' '.join(cmdline), file=sys.stderr)

    out = subprocess.run(cmdline, stdout=subprocess.PIPE).stdout.decode('utf-8')

    return out

def load_json(release, args, fcache):
    out = None

    if release == 'local':
        out = get_json(release, args)
    else:
        fqc = FontQueryCache('fedora', release, args.target)
        if args.clean_cache:
            fqc.delete()
        if fcache:
            if args.verbose:
                print('* Reading JSON from cache', file=sys.stderr)
            out = fqc.read()
        if not out:
            out = get_json(release, args)
            if fcache:
                if args.verbose:
                    print('* Storing cache...', file=sys.stderr, end='')
                if fqc.save(out):
                    if args.verbose:
                        print('done', file=sys.stderr)
                else:
                    if args.verbose:
                        print('failed', file=sys.stderr)

    return out

def main():
    """Endpoint to execute fontquery diff program."""
    renderer = {'html': htmlformatter.HtmlRenderer,
                'text': htmlformatter.TextRenderer}

    parser = argparse.ArgumentParser(
        description='Show difference between local and reference',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-C',
                        '--clean-cache',
                        action='store_true',
                        help='Clean up caches before processing')
    parser.add_argument('--disable-cache',
                        action='store_true',
                        help='Enforce processing everything even if not updating')
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
    parser.add_argument('compare_a', nargs='?', help='Release to compare',
                        default='rawhide')
    parser.add_argument('compare_b', nargs='?', help='Release to compare',
                        default='local')

    args = parser.parse_args()
    if local_not_supported:
        raise TypeError('local query feature is not available.')
    if not shutil.which('podman'):
        print('podman is not installed', file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print('* Compare from: {}'.format(args.compare_a))
        print('* Compare to: {}'.format(args.compare_b))
        print('* Target: {}'.format(args.target))
        print('* Language: {}'.format(args.lang))

    retval_a = load_json(args.compare_a, args,
                         not args.disable_cache and not args.lang)
    retval_b = load_json(args.compare_b, args,
                         not args.disable_cache and not args.lang)

    with args.output:
        for s in htmlformatter.generate_diff(renderer[args.render](), '',
                                             json.loads(retval_a),
                                             json.loads(retval_b)):
            args.output.write(s)

if __name__ == '__main__':
    main()
