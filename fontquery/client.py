# client.py
# Copyright (C) 2022-2025 Red Hat, Inc.
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
"""Module to deal with client for fontquery."""

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
import langtable
try:
    import fontquery_debug  # noqa: F401
except ModuleNotFoundError:
    pass
from fontquery import version
from fontquery.package import PackageRepoCache, PackageRepo, Font2Package, PackageNotFound
try:
    from pyanaconda import localization
    defaultLangList = list(localization.get_available_translations())
except ModuleNotFoundError:
    defaultLangList = [
        'aa', 'ab', 'af', 'ak', 'am', 'an', 'ar', 'as', 'ast', 'av', 'ay',
        'az_az', 'az_ir', 'ba', 'be', 'ber_dz', 'ber_ma', 'bg', 'bh', 'bho',
        'bi', 'bin', 'bm', 'bn', 'bo', 'br', 'brx', 'bs', 'bua', 'byn', 'ca',
        'ce', 'ch', 'chm', 'chr', 'co', 'crh', 'cs', 'csb', 'cu', 'cv', 'cy',
        'da', 'de', 'doi', 'dv', 'dz', 'ee', 'el', 'en', 'eo', 'es', 'et',
        'eu', 'fa', 'fat', 'ff', 'fi', 'fil', 'fj', 'fo', 'fr', 'fur', 'fy',
        'ga', 'gd', 'gez', 'gl', 'gn', 'gu', 'gv', 'ha', 'haw', 'he', 'hi',
        'hne', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie',
        'ig', 'ii', 'ik', 'io', 'is', 'it', 'iu', 'ja', 'jv', 'ka', 'kaa',
        'kab', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'kok', 'kr', 'ks',
        'ku_am', 'ku_iq', 'ku_ir', 'ku_tr', 'kum', 'kv', 'kw', 'kwm', 'ky',
        'la', 'lah', 'lb', 'lez', 'lg', 'li', 'ln', 'lo', 'lt', 'lv', 'mai',
        'mg', 'mh', 'mi', 'mk', 'ml', 'mn_cn', 'mn_mn', 'mni', 'mo', 'mr',
        'ms', 'mt', 'my', 'na', 'nb', 'nds', 'ne', 'ng', 'nl', 'nn', 'no',
        'nqo', 'nr', 'nso', 'nv', 'ny', 'oc', 'om', 'or', 'os', 'ota', 'pa',
        'pa_pk', 'pap_an', 'pap_aw', 'pes', 'pl', 'prs', 'ps_af', 'ps_pk',
        'pt', 'qu', 'quz', 'rm', 'rn', 'ro', 'ru', 'rw', 'sa', 'sah', 'sat',
        'sc', 'sco', 'sd', 'se', 'sel', 'sg', 'sh', 'shs', 'si', 'sid', 'sk',
        'sl', 'sm', 'sma', 'smj', 'smn', 'sms', 'sn', 'so', 'sq', 'sr', 'ss',
        'st', 'su', 'sv', 'sw', 'syr', 'ta', 'te', 'tg', 'th', 'ti_er',
        'ti_et', 'tig', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty',
        'tyv', 'ug', 'uk', 'und_zmth', 'und_zsye', 'ur', 'uz', 've', 'vi',
        'vo', 'vot', 'wa', 'wal', 'wen', 'wo', 'xh', 'yap', 'yi', 'yo', 'za',
        'zh_cn', 'zh_hk', 'zh_mo', 'zh_sg', 'zh_tw', 'zu'
    ]


def get_version(os_release) -> str:
    if os_release['ID'] == 'fedora':
        if ('VARIANT_ID' in os_release and os_release['VARIANT_ID'] == 'eln') or\
           os_release['REDHAT_SUPPORT_PRODUCT_VERSION'] == 'rawhide':
            return 'rawhide'
        return os_release['VERSION_ID']
    return os_release['VERSION_ID']


def dump(params: object) -> str:
    """Dump fontquery result in JSON."""
    p = Path('/etc/os-release')
    with open(p, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='=')
        os_release = dict(reader)
    langname = {
        lang:
        langtable.language_name(languageId=re.sub(r'_([a-zA-Z]*)$',
                                                  lambda r: r.group(0).upper(),
                                                  lang.replace('-', '_')),
                                languageIdQuery='en')
        for lang in params.lang
    }
    fqver = version.fontquery_version()
    if not shutil.which('fc-match'):
        print('fc-match is not installed', file=sys.stderr)
        sys.exit(1)
    jsons = {
        'id': os_release['ID'],
        'version_id': os_release['VERSION_ID'],
        'pattern': params.pattern,
        'fq_id': fqver,
        'fonts': [],
    }
    cache = PackageRepoCache(product=os_release['ID'])
    for i, ls in enumerate(params.lang, 1):
        print(f'* This may take some time...({i}/{len(params.lang)})\r',
              end="", file=sys.stderr)
        for f in params.family:
            cmdline = [
                'fc-match', '-f',
                ('%{file:-<unknown filename>},'
                 '%{family[0]:-<unknown family>},'
                 '%{style[0]:-<unknown style>}\\n'),
                f':family={f}:lang={ls.replace("_", "-")}'
            ]
            if params.verbose:
                print('# ' + ' '.join(cmdline), flush=True, file=sys.stderr)
            retval = subprocess.run(cmdline, capture_output=True,
                                    check=False)

            cond_empty = re.compile(r'^$')
            out = [
                s for s in retval.stdout.decode('utf-8').split('\n')
                if not cond_empty.match(s)
            ]
            data = [item.split(',') for item in out][0]
            is_default = 2
            try:
                pkgname = list(Font2Package.get_package_name_from_file(data[0]))[0]
                repo = PackageRepo(cache, pkgname, data[1], get_version(os_release))
                ll = ls.replace('-', '_')
                if ll in repo.languages:
                    if f == 'sans-serif':
                        is_default = repo.is_default_sans(data[1], ll)
                    elif f == 'serif':
                        is_default = repo.is_default_serif(data[1], ll)
                    elif f == 'monospace':
                        is_default = repo.is_default_mono(data[1], ll)
                    elif f == 'system-ui':
                        is_default = repo.is_default_systemui(data[1], ll)
                    else:
                        is_default = 2
                else:
                    is_default = 2
            except PackageNotFound:
                pass
            jsons['fonts'].append({
                'lang': ls,
                'lang_name': langname[ls],
                'alias': f,
                'file': Path(data[0]).name,
                'family': data[1],
                'style': data[2],
                'is_default': is_default
            })
    print('', file=sys.stderr)

    return json.dumps(jsons, indent=4)


def fcmatchaliases(params: object) -> str:
    """Show results of generic aliases"""
    results = []
    if not shutil.which('fc-match'):
        print('fc-match is not installed', file=sys.stderr)
        sys.exit(1)
    for i, ls in enumerate(params.lang, 1):
        print(f'* This may take some time...({i}/{len(params.lang)})\r',
              end="", file=sys.stderr)
        if len(params.lang) > 1:
            results.append(f"{ls}:")
        for a in ['sans-serif', 'serif', 'monospace', 'system-ui']:
            cmdline = [
                'fc-match', '-f',
                (f'  ({a}):\t  \"%{{family[0]:-<unknown family>}}\" '
                 '\"%{style[0]:-<unknown style>}\"'),
                f':family={a}:lang={ls.replace("_", "-")}'
            ]
            if params.verbose:
                print('# ' + ' '.join(cmdline), flush=True, file=sys.stderr)
            retval = subprocess.run(cmdline, capture_output=True,
                                    check=False)

            cond_empty = re.compile(r'^$')
            out = [
                s for s in retval.stdout.decode('utf-8').split('\n')
                if not cond_empty.match(s)
            ]
            results += out
    print('', file=sys.stderr)

    return "\n".join(results)


def checkupdate(params: object) -> None:
    if not shutil.which('fontquery-setup.sh'):
        print('fontquery-setup.sh is not installed')
        sys.exit(1)
    cmdline = [
        'fontquery-setup.sh', '-c'
    ]
    if params.verbose:
        print('# ' + ' '.join(cmdline), flush=True, file=sys.stderr)
    res = subprocess.run(cmdline, check=False)
    sys.exit(res.returncode)


def update(params: object) -> None:
    if not shutil.which('fontquery-setup.sh'):
        print('fontquery-setup.sh is not installed')
        sys.exit(1)
    cmdline = [
        'fontquery-setup.sh', '-u'
    ]
    if params.verbose:
        print('# ' + ' '.join(cmdline), flush=True, file=sys.stderr)
    res = subprocess.run(cmdline, check=False)
    sys.exit(res.returncode)


def install(params: object) -> None:
    if not shutil.which('fontquery-setup.sh'):
        print('fontquery-setup.sh is not installed')
        sys.exit(1)
    cmdline = [
        'fontquery-setup.sh', '-i'
    ] + params.args
    if params.verbose:
        print('# ' + ' '.join(cmdline), flush=True, file=sys.stderr)
    res = subprocess.run(cmdline, check=False)
    sys.exit(res.returncode)


def main():
    """Endpoint to execute fontquery-client program."""
    fccmd = {'fcmatch': 'fc-match',
             'fclist': 'fc-list',
             'fcmatchaliases': fcmatchaliases,
             'json': dump,
             'update': update,
             'checkupdate': checkupdate,
             'install': install,
             }
    fclang_ll_cc = [
        'az_az', 'az_ir', 'ber_dz', 'ber_ma', 'ku_am', 'ku_iq', 'ku_ir',
        'ku_tr', 'mn_cn', 'mn_mn', 'pa_pk', 'pap_an', 'pap_aw', 'ps_af',
        'ps_pk', 'ti_er', 'ti_et', 'und_zmth', 'und_zsye', 'zh_cn', 'zh_hk',
        'zh_mo', 'zh_sg', 'zh_tw'
    ]
    families = ['sans-serif', 'serif', 'monospace', 'system-ui']
    fclangs = []
    for lang in defaultLangList:
        added = False
        for ls in fclang_ll_cc:
            ll = re.sub('_.*', '', ls)
            if lang == ll:
                fclangs.append(ls.replace('_', '-'))
                added = True
        if not added:
            fclangs.append(lang)

    parser = argparse.ArgumentParser(
        description='Query fonts',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-f',
                        '--family',
                        action='append',
                        default=families,
                        help='Families to dump fonts data into JSON')
    parser.add_argument('-l',
                        '--lang',
                        action='append',
                        default=fclangs,
                        help='Language list to dump fonts data into JSON')
    parser.add_argument('-m',
                        '--mode',
                        default='fcmatchaliases',
                        choices=list(fccmd.keys()),
                        help='Action to perform for query')
    parser.add_argument('-p',
                        '--pattern',
                        help='Query pattern to identify fonts data into JSON')
    parser.add_argument('-V',
                        '--version',
                        action='store_true',
                        help='Show image version')
    parser.add_argument('-v',
                        '--verbose',
                        action='store_true',
                        help='Show more detailed logs')
    parser.add_argument('args',
                        nargs='*',
                        help='Arguments to the corresponding action')

    args = parser.parse_args()

    if args.version:
        print(version.fontquery_version())
        sys.exit(0)
    # Pick up langs only set by args
    ll = Counter(args.lang)
    ll.subtract(fclangs)
    langlist = list(ll.elements())
    args.lang = langlist if langlist else fclangs
    if isinstance(fccmd[args.mode], types.FunctionType):
        print(fccmd[args.mode](args))
    else:
        if not shutil.which(fccmd[args.mode]):
            print(f'{fccmd[args.mode]} is not installed',
                  file=sys.stderr)
            sys.exit(1)

        if args.lang != fclangs:
            print('W: lang option does not take any effects. '
                  'Please use :lang fcpattern instead',
                  flush=True, file=sys.stderr)
        cmdline = [fccmd[args.mode]] + args.args
        if args.verbose:
            print('# ' + ' '.join(cmdline), flush=True, file=sys.stderr)

        subprocess.run(cmdline, check=False)


if __name__ == '__main__':
    main()
