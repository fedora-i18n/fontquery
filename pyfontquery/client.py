# client.py
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

import argparse
import re
import shutil
import subprocess
import sys
from pyfontquery import container

def main():
    parser = argparse.ArgumentParser(description='Query fonts',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--release',
                        default='rawhide',
                        help='Release number')
    parser.add_argument('-l', '--lang',
                        action='append',
                        help='Language list to dump fonts data into JSON')
    parser.add_argument('-m', '--mode',
                        default='fcmatch',
                        choices=['fcmatch', 'fclist', 'json'],
                        help='Action to perform for query')
    parser.add_argument('-t', '--target',
                        default='langpacks',
                        choices=['comps', 'langpacks', 'both', 'all'],
                        help='Query fonts from')
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Show more detailed logs')
    parser.add_argument('args',
                        nargs='*',
                        help='Queries')

    args = parser.parse_args()
    if args.release == 'local':
        cmdline = ['fontquery-container', '-m', args.mode] + (['-'+''.join(['v'*(args.verbose-1)])] if args.verbose > 1 else []) + ([] if args.lang is None else [' '.join(['-l '+l for l in args.lang])]) + args.args
    else:
        if not shutil.which('podman'):
            print('podman is not installed')
            sys.exit(1)

        cmdline = ['podman', 'run', '--rm', 'ghcr.io/fedora-i18n/fontquery-{}:{}'.format(args.target, args.release), '-m', args.mode] + (['-'+''.join(['v'*(args.verbose-1)])] if args.verbose > 1 else []) + ([] if args.lang is None else [' '.join(['-l '+l for l in args.lang])]) + args.args

    if args.verbose:
        print('# '+' '.join(cmdline))

    retval = subprocess.run(cmdline, stdout=subprocess.PIPE)

    print(retval.stdout.decode('utf-8'))
