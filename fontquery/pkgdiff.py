# Copyright (C) 2025 fontquery Authors
# SPDX-License-Identifier: MIT

"""Module to check differences with package installation"""

import argparse
import importlib.metadata
import json
import shutil
import sys
try:
    import fontquery_debug  # noqa: F401
except ModuleNotFoundError:
    pass
from fontquery import htmlformatter  # noqa: F401
from fontquery.cache import FontQueryCache  # noqa: F401
from fontquery.container import ContainerImage  # noqa: F401


def load_json(release, packages, args, fcache):
    out = None
    fqc = None

    c = ContainerImage(args.product, release, args.verbose)
    c.target = args.target
    if not args.disable_update:
        if not c.pull(args):
            raise RuntimeError('`podman pull\' failed')
    if packages is None:
        fqc = FontQueryCache(args.product, release, args.target)
        if args.clean_cache:
            fqc.delete()
        if fcache:
            if args.verbose:
                print('* Reading JSON from cache', file=sys.stderr)
            out = fqc.read()
    if not out:
        if packages is None:
            kw = vars(args)
            out = c.get_json(**kw)
            if fcache:
                if args.verbose:
                    print('* Storing cache...', file=sys.stderr, end='')
                if fqc.save(out):
                    if args.verbose:
                        print('done', file=sys.stderr)
                else:
                    if args.verbose:
                        print('failed', file=sys.stderr)
        else:
            kw = vars(args)
            del kw['package']
            out = c.get_json_after_install(packages, **kw)

    return out


def main():
    """Endpoint to execute fontquery instcheck program."""
    renderer = htmlformatter.get_renderer()

    parser = argparse.ArgumentParser(
        description='Check if a given package makes any difference',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-C',
                        '--clean-cache',
                        action='store_true',
                        help='Clean up caches before processing')
    parser.add_argument('--diff-only',
                        action='store_true',
                        help='Show diff only')
    parser.add_argument('--disable-cache',
                        action='store_true',
                        help='Enforce processing everything '
                        'even if not updating')
    parser.add_argument('--disable-update',
                        action='store_true',
                        help='Do not update the container image')
    parser.add_argument('-r', '--release',
                        default='rawhide',
                        help='Target release to check')
    parser.add_argument('-l',
                        '--lang',
                        action='append',
                        help='Language list to dump fonts data into JSON')
    parser.add_argument('--loose-comparison',
                        action='store_true',
                        help='Do not compare results accurately')
    parser.add_argument('-o', '--output',
                        type=argparse.FileType('w'),
                        default='-',
                        help='Output file')
    parser.add_argument('-P', '--product',
                        default='fedora',
                        choices=['fedora', 'centos'],
                        help='Product name to operate')
    parser.add_argument('-R', '--render',
                        default=list(renderer.keys())[0],
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
    parser.add_argument('-V',
                        '--version',
                        action='store_true',
                        help='Show version')
    parser.add_argument('package', nargs='+',
                        help='Test package to see difference')

    args = parser.parse_args()
    if args.version:
        print(importlib.metadata.version('fontquery'))
        sys.exit(0)
    if not shutil.which('podman'):
        print('podman is not installed', file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f'* Target: {args.target}', file=sys.stderr)
        print(f'* Language: {args.lang}', file=sys.stderr)
        print(file=sys.stderr)

    print(f'* Comparison on {args.release}', file=sys.stderr)
    if args.verbose:
        print(f'* Package(s) being installed: {' '.join(args.package)}',
              file=sys.stderr)

    retval_a = load_json(args.release, None, args,
                         not args.disable_cache and not args.lang)
    retval_b = load_json(args.release, args.package, args,
                         not args.disable_cache and not args.lang)

    with args.output:
        g = htmlformatter.generate_diff(renderer[args.render](), '',
                                        json.loads(retval_a),
                                        json.loads(retval_b),
                                        not args.loose_comparison,
                                        args.diff_only)
        for s in next(g):
            args.output.write(s)
        ret = next(g)
    sys.exit(0 if ret else 1)


if __name__ == '__main__':
    main()
