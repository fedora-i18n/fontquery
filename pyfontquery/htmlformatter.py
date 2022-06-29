# formatter.py
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
import atexit
import json
import markdown
import os
import re
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'cell_row_span')))
from cell_row_span import *

def json2data(data):
    retval = {}
    for d in data['fonts']:
        key = d['lang_name']
        if not key in retval:
            retval[key] = {}
        alias = d['alias']
        if not alias in retval[key]:
            retval[key][alias] = {}
        retval[key][alias] = d

    return retval

def json2langgroup(data):
    retval = {}
    for k, v in data.items():
        key = '{}|{}|{}'.format(v['sans-serif']['family'], v['serif']['family'], v['monospace']['family'])
        if not key in retval:
            retval[key] = {}
        retval[key][k] = v

    return retval

def json2langgroupdiff(data, diffdata):
    retval = {}
    aliases = [ 'sans-serif', 'serif', 'monospace' ]
    for k, v in data.items():
        key = ''
        for a in aliases:
            key += '|{}'.format(v[a]['family'])
        for a in aliases:
            key += '|{}'.format(diffdata[k][a]['family'])
        if not key in retval:
            retval[key] = {}
        retval[key][k] = [v, diffdata[k]]

    return retval

def output_table(out, title, data):
    sorteddata = json2data(data)
    md = [
        'Language | default sans | default serif | default mono',
        '-------- | ------------ | ------------- | ------------',
    ]
    for k in sorted(sorteddata.keys()):
        aliases = {
            'sans-serif': 'sans',
            'serif': 'serif',
            'monospace': 'mono'
        }
        s = '{}({}) '.format(k, sorteddata[k]['sans-serif']['lang'])
        for kk, vv in aliases.items():
            if re.search(r'(?i:{})'.format(vv), sorteddata[k][kk]['family']):
                attr = '.match'
            else:
                attr = '.notmatch'
            s += '| {} {{ {} }}'.format(sorteddata[k][kk]['family'], attr)

        md.append(s)

    with out:
        header = [
            '<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">',
            '<html>',
            '<head><title>Fonts table for %(title)s</title><style type=\"text/css\">',
            'table {',
            '  border-collapse: collapse;',
            '}',
            'table, th, td {',
            '  border-style: solid;',
            '  border-width: 1px;',
            '  border-color: #000000;',
            '}',
            '.match {',
            '}',
            '.notmatch {',
            '  color: orange',
            '}',
            '</style></head>',
            '<body>',
            '<div name="note" style="font-size: 10px; color: gray;">Note: orange colored name means needing some attention because there are no clue in family name if a font is certainly assigned to proper generic alias</div>',
        ]
        match data['pattern']:
          case 'comps':
            header.append('<div name="note" style="font-size: 10px; color: gray;">This table was generated according to the result on environment where all the packages in fonts group has been installed.</div>')
          case 'langpacks':
            header.append('<div name="note" style="font-size: 10px; color: gray;">This table was generated according to the result on environment where all the langpacks packages has been installed.</div>')
          case 'both':
            header.append('<div name="note" style="font-size: 10px; color: gray;">This table was generated according to the result on environment where all the packages in fonts group and all the langpacks packages has been installed.</div>')
          case 'all':
            header.append('<div name="note" style="font-size: 10px; color: gray;">This table was generated according to the result on environment where all the *-fonts packages has been installed with --skip-broken to dnf.</div>')

        footer = [
            '</table>',
            '<div name=\"footer\" style=\"text-align:right;float:right;font-size:10px;color:gray;\">Generated by fontquery(%(image)s image) + %(progname)s</div>',
            '</body>',
            '</html>'
        ]
        out.write('\n'.join(header) % {'title': title})
        out.write(markdown.markdown('\n'.join(md), extensions=['tables', 'attr_list']))
        out.write('\n'.join(footer) % {'progname': os.path.basename(__file__),
                                       'image': data['pattern']})

def output_diff(out, title, data, diffdata):
    sorteddata = json2data(data)
    sorteddiffdata = json2data(diffdata)
    matched = {}
    notmatched = {}
    missing_b = {}
    for k in sorted(sorteddata.keys()):
        if not k in sorteddiffdata:
            missing_b[k] = sorteddata[k]
        else:
            if sorteddata[k] == sorteddiffdata[k]:
                matched[k] = sorteddata[k]
            else:
                notmatched[k] = sorteddata[k]
    missing_a = {}
    for k in sorted(list(set(sorteddiffdata.keys()) - set(sorteddata.keys()))):
        missing_a[k] = sorteddiffdata[k]
    langdata = json2langgroup(matched)

    md = [
        'Language |   | default sans | default serif | default mono',
        '-------- | - | ------------ | ------------- | ------------',
    ]
    aliases = [ 'sans-serif', 'serif', 'monospace' ]
    for k in sorted(langdata.keys()):
        lang = ','.join(['{}({})'.format(l, langdata[k][l]['sans-serif']['lang']) for l in langdata[k].keys()])
        s = '{} {{ .lang }} | '.format(lang)
        kk = list(langdata[k].keys())[0]
        for a in aliases:
            s += '| {}'.format(langdata[k][kk][a]['family'])

        md.append(s)

    for k in sorted(missing_b.keys()):
        s = '{}({}) {{ .lang }} | - {{ .original .symbol }} '.format(k, missing_b[k]['sans-serif']['lang'])
        for a in aliases:
            s += '| {} {{ .original }} '.format(missing_b[k][a]['family'])

        md.append(s)
        s = '_^ _| + { .diff .symbol } | N/A { .diff } | N/A { .diff } | N/A { .diff } '
        md.append(s)

    for k in sorted(missing_a.keys()):
        s = '{}({}) {{ .lang }} | - {{ .original .symbol }} | N/A {{ .original }} | N/A {{ .original }} | N/A {{ .original }} '.format(k, missing_a[k]['sans-serif']['lang'])
        md.append(s)
        s = '_^ _| + { .diff .symbol } '
        for a in aliases:
            s += '| {} {{ .diff }}'.format(missing_a[k][a]['family'])
        md.append(s)

    langdiffdata = json2langgroupdiff(notmatched, sorteddiffdata)

    for k in langdiffdata.keys():
        lang = ','.join(['{}({})'.format(l, langdiffdata[k][l][0]['sans-serif']['lang']) for l in langdiffdata[k].keys()])
        s = '{} {{ .lang }} | - {{ .original .symbol }} '.format(lang)
        diff = []
        kk = list(langdiffdata[k].keys())[0]
        vv = langdiffdata[k][kk]
        for a in aliases:
            if vv[0][a]['family'] == vv[1][a]['family']:
                diff.append(None)
                attr = ''
            else:
                diff.append(vv[1][a])
                attr = '{ .original }'
            s += '| {} {}'.format(vv[0][a]['family'], attr)
        md.append(s)
        s = '_^ _| + { .diff .symbol } '
        for x in diff:
            if x is None:
                s += '|_^ _'
            else:
                s += '| {} {{ .diff }}'.format(x['family'])
        md.append(s)

    with out:
        header = [
            '<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">',
            '<html>',
            '<head><title>Fonts table for %(title)s</title><style type=\"text/css\">',
            'table {',
            '  border-collapse: collapse;',
            '}',
            'table, th, td {',
            '  border-style: solid;',
            '  border-width: 1px;',
            '  border-color: #000000;',
            '}',
            '.lang {',
            '  word-break: break-all;',
            '  width: 40%%;',
            '}',
            '.symbol {',
            '  min-width: 10px;',
            '  width: 1%%',
            '}',
            '.original {',
            '  color: green',
            '}',
            '.diff {',
            '  color: red',
            '}',
            '</style></head>',
            '<body>',
        ]
        header.append('<div name="note" style="font-size: 10px; color: gray;">Note: No symbols at 2nd column means no difference. -/+ symbols means there are difference between {} and {}</div>'.format(data['pattern'], diffdata['pattern']))
        header.append('<div name="note" style="font-size: 10px; color: gray;">Legend: + ({}), - ({})</div>'.format(data['pattern'], diffdata['pattern']))
        footer = [
            '</table>',
            '<div name=\"footer\" style=\"text-align:right;float:right;font-size:10px;color:gray;\">Generated by fontquery(%(image)s image) + %(progname)s</div>',
            '</body>',
            '</html>'
        ]
        out.write('\n'.join(header) % {'title': title})
        out.write(markdown.markdown('\n'.join(md), extensions=['tables', 'attr_list', 'cell_row_span']))
        out.write('\n'.join(footer) % {'progname': os.path.basename(__file__),
                                       'image': data['pattern']})

def main():
    parser = argparse.ArgumentParser(description='HTML formatter for fontquery',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-o', '--output',
                        type=argparse.FileType('w'),
                        default='-',
                        help='Output file')
    parser.add_argument('-t', '--title',
                        help='Set title name')
    parser.add_argument('-d', '--diff',
                        type=argparse.FileType('r'),
                        help='Output difference between FILE and DIFF as secondary')
    parser.add_argument('FILE',
                        type=argparse.FileType('r'),
                        help='JSON file to read or - to read from stdin')

    args = parser.parse_args()
    atexit.register(args.FILE.close)

    data = None
    with args.FILE:
        data = json.load(args.FILE)

    if args.diff is None:
        output_table(args.output, args.title, data)
    else:
        with args.diff:
            diffdata = json.load(args.diff)

        output_diff(args.output, args.title, data, diffdata)
