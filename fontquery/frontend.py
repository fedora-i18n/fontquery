# frontend.py
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
"""Module to perform a frontend application for fontquery."""

import argparse
import importlib.metadata
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from collections import Counter
try:
    import fontquery_debug # noqa: F401
except ModuleNotFoundError:
    pass
import fontquery.htmlformatter # noqa: F401
try:
    from fontquery import client  # noqa: F401
    local_not_supported = False
except ModuleNotFoundError:
    local_not_supported = True
from fontquery.cache import FontQueryCache # noqa: F401
from pathlib import Path
from xdg import BaseDirectory


def run(release, args):
    if args.product == 'centos':
        if re.match(r'\d+(\-development)?$', release):
            release = 'stream' + release
    if release == 'local':
        fqcexec = 'fontquery-client'
        if not shutil.which(fqcexec):
            fqcexec = client.__file__
        else:
            fqcexec = shutil.which(fqcexec)
        cmdline = ['python', fqcexec, '-m', args.mode] + (
            ['-' + ''.join(['v' * (args.verbose - 1)])] if args.verbose > 1
            else []) + ([] if args.lang is None else
                        [' '.join(['-l=' + ls
                                   for ls in args.lang])]) + args.args
    else:
        print('* This may take some time...', file=sys.stderr)
        cmdline = [
            'podman', 'run', '--rm',
            'ghcr.io/fedora-i18n/fontquery/{}/{}:{}'.format(
                args.product, args.target, release), '-m', args.mode
        ] + (['-' + ''.join(['v' * (args.verbose - 1)])] if args.verbose > 1
             else []) + ([] if args.lang is None else
                         [' '.join(['-l=' + ls
                                    for ls in args.lang])]) + args.args

    if args.verbose:
        print('# ' + ' '.join(cmdline), file=sys.stderr)

    result = subprocess.run(cmdline, stdout=subprocess.PIPE)
    if result.returncode != 0:
        sys.tracebacklimit = 0
        raise RuntimeError('`podman run\' failed with the error code {}'.format(result.returncode))

    return result.stdout.decode('utf-8')

def load(release, args, fcache):
    out = None

    if release == 'local':
        out = run(release, args)
    else:
        fqc = FontQueryCache(args.product, release, args.target)
        if args.clean_cache:
            fqc.delete()
        if fcache:
            if args.verbose:
                print('* Reading JSON from cache', file=sys.stderr)
            out = fqc.read()
        if not out:
            out = run(release, args)
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
    """Endpoint to execute fontquery frontend program."""
    defrel = ['local']

    parser = argparse.ArgumentParser(
        description='Query fonts',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-C',
                        '--clean-cache',
                        action='store_true',
                        help='Clean caches before processing')
    parser.add_argument('--disable-cache',
                        action='store_true',
                        help='Enforce processing everything even if not updating')
    parser.add_argument('-f',
                        '--filename-format',
                        default='{product}-{release}-{target}.{mode}',
                        help='Output filename format. only take effects with --mode=html or using multiple --release option')
    parser.add_argument('-r',
                        '--release',
                        default=defrel,
                        action='append',
                        help='Release number such as "rawhide" and "39". "local" to query from current environment instead of images')
    parser.add_argument('-l',
                        '--lang',
                        action='append',
                        help='Language list to dump fonts data into JSON')
    parser.add_argument('-m',
                        '--mode',
                        default='fcmatch',
                        choices=['fcmatch', 'fclist', 'json', 'html'],
                        help='Action to perform for query')
    parser.add_argument('-O',
                        '--output-dir',
                        default='.',
                        help='Output directory')
    parser.add_argument('-P',
                        '--product',
                        default='fedora',
                        choices=['fedora', 'centos'],
                        help='Product name to operate')
    parser.add_argument('-t',
                        '--target',
                        default='minimal',
                        choices=['minimal', 'extra', 'all'],
                        help='Query fonts from')
    parser.add_argument('-T',
                        '--title',
                        default='{product} {release}: {target}',
                        help='Page title format. only take effects with --mode=html')
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        help='Show more detailed logs')
    parser.add_argument('-V',
                        '--version',
                        action='store_true',
                        help='Show version')
    parser.add_argument('args', nargs='*', help='Queries')

    args = parser.parse_args()
    rr = Counter(args.release)
    rr.subtract(defrel)
    rellist = list(rr.elements())
    args.release = rellist if rellist else defrel

    cache = None
    cmdline = []
    out = None
    origmode = args.mode
    redirect = True if args.mode == 'html' else False
    if redirect:
        args.mode = 'json'
    if args.version:
        print(importlib.metadata.version('fontquery'))
        sys.exit(0)
    ofile = str(Path(args.output_dir) / args.filename_format)
    if args.verbose:
        print('* Product: {}'.format(args.product), file=sys.stderr)
        print('* Release: {}'.format(args.release), file=sys.stderr)
        print('* Target: {}'.format(args.target), file=sys.stderr)
        print('* Language: {}'.format(args.lang), file=sys.stderr)
        print('* Mode: {}'.format(args.mode), file=sys.stderr)
        print('* Output: {}'.format(ofile), file=sys.stderr)

    if 'local' in args.release:
        if local_not_supported:
            raise TypeError('local query feature is not available.')
        if args.target != parser.get_default('target'):
            warnings.warn("target option won't take any effects on local mode", RuntimeWarning, stacklevel=2)
    else:
        if not shutil.which('podman'):
            print('podman is not installed')
            sys.exit(1)

    for r in args.release:
        out = load(r, args, not args.lang and not args.disable_cache and args.mode == 'json')
        if redirect:
            with tempfile.NamedTemporaryFile(mode='w+') as tmp:
                tmp.write(out)
                tmp.seek(0)
                with open(ofile.format(product=args.product, release=r,
                                       target=args.target, mode=origmode), 'w') as fw:
                    fontquery.htmlformatter.run('table', tmp, None, fw, fontquery.htmlformatter.HtmlRenderer(),
                                                args.title.format(product=args.product,
                                                                  release=r,
                                                                  target=args.target))
        else:
            if len(args.release) == 1:
                print(out)
            else:
                with open(ofile.format(product=args.product, release=r,
                                       target=args.target, mode=origmode), 'w') as fw:
                    fw.write(out)


if __name__ == '__main__':
    main()
