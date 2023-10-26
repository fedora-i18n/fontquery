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
"""Module to deai with formatting JSON format for fontquery."""

import argparse
import atexit
import json
import markdown
import os
import re
import sys
from termcolor import colored
from typing import Any, IO, Iterator

class DataRenderer:
    """Abstract class for renderer"""

    def __init__(self):
        self.__title = None
        self.__imagetype = None
        self.__imagedifftype = None

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, v: str):
        self.__title = v

    @property
    def imagetype(self):
        return self.__imagetype

    @imagetype.setter
    def imagetype(self, v: str):
        self.__imagetype = v

    @property
    def imagedifftype(self):
        return self.__imagedifftype

    @imagedifftype.setter
    def imagedifftype(self, v: str):
        self.__imagedifftype = v

    def __diff__(self, data: dict[str, Any],
                    missing_a: dict[str, Any],
                    missing_b: dict[str, Any],
                    diffdata: dict[str, Any]):
        pass

    def __table__(self, data: dict[str, Any]):
        pass

    def render_diff(self, data: dict[str, Any],
                    missing_a: dict[str, Any],
                    missing_b: dict[str, Any],
                    diffdata: dict[str, Any]):
        return self.__diff__(data, missing_a, missing_b, diffdata)

    def render_table(self, data: dict[str, Any]):
        return self.__table__(data)


class HtmlRenderer(DataRenderer):
    """Render html"""

    def __init__(self):
        super().__init__()

    def __diff__(self, data: dict[str, Any],
                    missing_a: dict[str, Any],
                    missing_b: dict[str, Any],
                    diffdata: dict[str, Any]):
        diff_templ = [
            '<tr>',
            '<td class="lang" rowspan="2">{lang}</td>',
            '<td class="original symbol">-</td>',
            '<td class="original">{old_sans}</td>',
            '<td class="original">{old_serif}</td>',
            '<td class="original">{old_mono}</td>',
            '</tr>',
            '<tr>',
            '<td class="diff symbol">+</td>',
            '<td class="diff">{new_sans}</td>',
            '<td class="diff">{new_serif}</td>',
            '<td class="diff">{new_mono}</td>',
            '</tr>',
        ]
        nodiff_templ = [
            '<tr>',
            '<td class="lang">{lang}</td>',
            '<td></td>',
            '<td>{sans}</td>',
            '<td>{serif}</td>',
            '<td>{mono}</td>',
            '</tr>',
        ]
        header_templ = [
            '<table><thead><tr>',
            '<th>Language</th>',
            '<th></th>',
            '<th>default sans</th>',
            '<th>default serif</th>',
            '<th>default mono</th>',
            '</tr></thead>',
            '<tbody>',
        ]
        tables = []

        tables.append('\n'.join(header_templ))
        aliases = ['sans-serif', 'serif', 'monospace']
        aliasids = ['sans', 'serif', 'mono']

        for k in sorted(data.keys()):
            templ = '\n'.join(nodiff_templ)
            lang = ','.join(['{}({})'.format(ls, data[k][ls]['sans-serif']['lang']) for ls in data[k].keys()])
            kk = list(data[k].keys())[0]
            s = templ.format(**{'lang': lang,
                                'sans': data[k][kk]['sans-serif']['family'],
                                'serif': data[k][kk]['serif']['family'],
                                'mono': data[k][kk]['monospace']['family']
                                })
            tables.append(s)

        for k in sorted(missing_b.keys()):
            lang = '{}({})'.format(k, missing_b[k]['sans-serif']['lang'])
            templ = '\n'.join(diff_templ)
            s = templ.format(**{'lang': lang,
                                'old_sans': missing_b[k]['sans-serif']['family'],
                                'old_serif': missing_b[k]['serif']['family'],
                                'old_mono': missing_b[k]['monospace']['family'],
                                'new_sans': 'N/A',
                                'new_serif': 'N/A',
                                'new_mono': 'N/A'
                                })
            tables.append(s)

        for k in sorted(missing_a.keys()):
            lang = '{}({})'.format(k, missing_a[k]['sans-serif']['lang'])
            templ = '\n'.join(diff_templ)
            s = templ.format(**{'lang': lang,
                                'old_sans': 'N/A',
                                'old_serif': 'N/A',
                                'old_mono': 'N/A',
                                'new_sans': missing_a[k]['sans-serif']['family'],
                                'new_serif': missing_a[k]['serif']['family'],
                                'new_mono': missing_a[k]['monospace']['family'],
                                })
            tables.append(s)

        for k in diffdata.keys():
            line = ['<tr>']
            lang = ','.join(['{}({})'.format(ls, diffdata[k][ls][0]['sans-serif']['lang']) for ls in diffdata[k].keys()])
            line.append('<td class="lang" rowspan="2">{}'.format(lang))
            line.append('<td class="original symbol">-</td>')
            diff = []
            kk = list(diffdata[k].keys())[0]
            vv = diffdata[k][kk]
            for a in aliases:
                if vv[0][a]['family'] == vv[1][a]['family']:
                    diff.append(None)
                    attr = 'rowspan="2"'
                else:
                    diff.append(vv[1][a])
                    attr = 'class="original"'
                line.append('<td {attr}>{family}</td>'.format(**{
                    'attr': attr,
                    'family': vv[0][a]['family']
                }))
            line.append('</tr><tr>')
            line.append('<td class="diff symbol">+</td>')
            for x in diff:
                if x is None:
                    pass
                else:
                    line.append('<td class="diff">{}</td>'.format(x['family']))
            tables.append('\n'.join(line))

        header = [
            ('<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\"'
             ' \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">'),
            '<html>',
            ('<head><title>Fonts table for %(title)s</title>'
             '<style type=\"text/css\">'),
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
            '  color: red',
            '}',
            '.diff {',
            '  color: green',
            '}',
            '</style></head>',
            '<body>',
        ]
        header.append(('<div name="note" style="font-size: 10px; color: gray;"'
                       '>Note: No symbols at 2nd column means no difference.'
                       ' -/+ symbols means there are difference between {} '
                       'and {}</div>').format(self.imagetype,
                                              self.imagedifftype))
        header.append(('<div name="note" selftyle="font-size: 10px; color: gray;"'
                       f">Legend: - ({self.imagetype}),"
                       f" + ({self.imagedifftype})</div>"))
        footer = [
            '</tr>',
            '</tbody>',
            '</table>',
            ('<div name=\"footer\" style=\"text-align:right;float:right;'
             'font-size:10px;color:gray;\">Generated by fontquery'
             '(%(image)s image) + %(progname)s</div>'),
            '</body>',
            '</html>'
        ]
        yield '\n'.join(header) % {'title': self.title}
        yield from tables
        yield '\n'.join(footer) % {'progname': os.path.basename(__file__),
                                   'image': self.imagetype}


    def __table__(self, data: dict[str, Any]):
        md = [
            'Language | default sans | default serif | default mono',
            '-------- | ------------ | ------------- | ------------',
        ]
        for k in sorted(data.keys()):
            aliases = {
                'sans-serif': 'sans',
                'serif': 'serif',
                'monospace': 'mono'
            }
            s = '{}({}) '.format(k, data[k]['sans-serif']['lang'])
            for kk, vv in aliases.items():
                if re.search(r'(?i:{})'.format(vv), data[k][kk]['family']):
                    attr = '.match'
                else:
                    attr = '.notmatch'
                    s += '| {} {{ {} }}'.format(data[k][kk]['family'], attr)
            md.append(s)

        header = [
            ('<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\"'
             ' \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">'),
            '<html>',
            ('<head><title>Fonts table for %(title)s</title>'
             '<style type=\"text/css\">'),
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
            ('<div name="note" style="font-size: 10px; color: gray;">'
             'Note: orange colored name means needing some attention'
             ' because there are no clue in family name if a font is'
             ' certainly assigned to proper generic alias</div>'),
        ]
        match self.imagetype:
            case 'minimal':
                header.append(('<div name="note" style="font-size: 10px; '
                               'color: gray;">This table was generated '
                               'with minimal default fonts</div>'))
            case 'extra':
                header.append(('<div name="note" style="font-size: 10px; '
                               'color: gray;">This table was generated '
                               'with default fonts + some extra fonts</div>'))
            case 'all':
                header.append(('<div name="note" style="font-size: 10px; '
                               'color: gray;">This table was generated '
                               'with all the fonts available for distribution</div>'))

        footer = [
            '</table>',
            ('<div name=\"footer\" style=\"text-align:right;float:right;'
             'font-size:10px;color:gray;\">Generated by fontquery'
             '(%(image)s image) + %(progname)s</div>'),
            '</body>',
            '</html>'
        ]
        yield '\n'.join(header) % {'title': self.title}
        yield markdown.markdown('\n'.join(md),
                                extensions=['tables', 'attr_list'])
        yield '\n'.join(footer) % {'progname': os.path.basename(__file__),
                                   'image': self.imagetype}


class ColoredText(str):
    """A Class to handle colored text"""

    def __new__(cls, *args, **kw):
        text = kw['text'] if 'text' in kw else args[0]
        retval = str.__new__(cls, text)
        if 'color' not in kw:
            kw['color'] = args[1] if len(args) > 1 else None
        if 'on_color' not in kw:
            kw['on_color'] = args[2] if len(args) > 2 else None
        if 'attrs' not in kw:
            kw['attrs'] = args[3] if len(args) > 3 else None
        retval.__color = kw['color']
        retval.__on_color = kw['on_color']
        retval.__attrs = kw['attrs']
        return retval

    def cstr(self):
        return colored(self.__str__(), self.__color, self.__on_color, self.__attrs)


class TextRenderer(DataRenderer):
    """Render text"""

    def __init__(self):
        super().__init__()

    @classmethod
    def format_line(cls, column: list[ColoredText]) -> Iterator[str]:
        l = []
        retval = ''
        for i, s in enumerate(column):
            n = len(s)
            s = s.cstr() + ' '*(15-n)
            l.append(s)
            if n >= 16:
                yield ' '.join(l)
                l = []
                for n in range(i+1):
                    l.append(' '*15)
        retval = ' '.join(l)
        if retval.strip():
            yield retval

    def __diff__(self, data: dict[str, Any],
                    missing_a: dict[str, Any],
                    missing_b: dict[str, Any],
                    diffdata: dict[str, Any]):
        out = []
        for s in TextRenderer.format_line([ColoredText('Language', attrs=['bold']),
                                           ColoredText('default sans', attrs=['bold']),
                                           ColoredText('default serif', attrs=['bold']),
                                           ColoredText('default mono', attrs=['bold'])
                                           ]):
            out.append('  ' + s)
        aliases = ['sans-serif', 'serif', 'monospace']
        for k in sorted(data.keys()):
            lang = ','.join(['{}({})'.format(ls, data[k][ls]['sans-serif']['lang']) for ls in data[k].keys()])
            cols = [ColoredText(lang)]
            kk = list(data[k].keys())[0]
            for a in aliases:
                cols.append(ColoredText(data[k][kk][a]['family']))
            for s in TextRenderer.format_line(cols):
                out.append('  ' + s)
        for k in sorted(missing_b.keys()):
            lang = '{}({})'.format(k, missing_b[k]['sans-serif']['lang'])
            cols = [ColoredText(lang)]
            for a in aliases:
                cols.append(ColoredText(missing_b[k][a]['family']))
            for s in TextRenderer.format_line(cols):
                out.append(colored('- ' + s, 'red'))
            for s in TextRenderer.format_line([ColoredText(''),
                                               ColoredText('N/A'),
                                               ColoredText('N/A'),
                                               ColoredText('N/A')]):
                out.append(colored('+ ' + s, 'green'))
        for k in sorted(missing_a.keys()):
            lang = '{}({})'.format(k, missing_a[k]['sans-serif']['lang'])
            cols = [ColoredText(lang)]
            for a in aliases:
                cols.append(ColoredText(missing_a[k][a]['family']))
            for s in TextRenderer.format_line([ColoredText(''),
                                               ColoredText('N/A'),
                                               ColoredText('N/A'),
                                               ColoredText('N/A')]):
                out.append(colored('- ' + s, 'red'))
            for s in TextRenderer.format_line(cols):
                out.append(colored('+ ' + s, 'green'))
        for k in diffdata.keys():
            lang = ','.join(['{}({})'.format(ls, diffdata[k][ls][0]['sans-serif']['lang']) for ls in diffdata[k].keys()])
            origcol = [ColoredText(lang)]
            diffcol = [ColoredText('')]
            kk = list(diffdata[k].keys())[0]
            vv = diffdata[k][kk]
            for a in aliases:
                if vv[0][a]['family'] == vv[1][a]['family']:
                    diffcol.append(ColoredText(''))
                    origcol.append(ColoredText(vv[0][a]['family']))
                else:
                    diffcol.append(ColoredText(vv[1][a]['family'], 'green'))
                    origcol.append(ColoredText(vv[0][a]['family'], 'red'))
            for s in TextRenderer.format_line(origcol):
                out.append(colored('- ', 'red') + s)
            for s in TextRenderer.format_line(diffcol):
                out.append(colored('+ ', 'green') + s)

        yield '\n'.join(out) + '\n'

    def __table__(self, data: dict[str, Any]):
        out = []
        for s in TextRenderer.format_line([ColoredText('Language', attrs=['bold']),
                                           ColoredText('default sans', attrs=['bold']),
                                           ColoredText('default serif', attrs=['bold']),
                                           ColoredText('default mono', attrs=['bold'])
                                           ]):
            out.append(s)
        for k in sorted(data.keys()):
            aliases = {
                'sans-serif': 'sans',
                'serif': 'serif',
                'monospace': 'mono'
            }
            cols = [ColoredText('{}({})'.format(k, data[k]['sans-serif']['lang']))]
            for kk, vv in aliases.items():
                if re.search(r'(?i:{})'.format(vv), data[k][kk]['family']):
                    cols.append(ColoredText(data[k][kk]['family']))
                else:
                    cols.append(ColoredText(data[k][kk]['family'], 'red'))
            for s in TextRenderer.format_line(cols):
                out.append(s)

        yield '\n'.join(out) + '\n'


def json2data(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Restructure JSON format."""
    retval = {}
    for d in data['fonts']:
        key = d['lang_name']
        if key not in retval:
            retval[key] = {}
        alias = d['alias']
        retval[key][alias] = d

    return retval


def json2langgroup(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Restructure JSON format by language group."""
    retval = {}
    for k, v in data.items():
        key = '{}|{}|{}'.format(v['sans-serif']['family'],
                                v['serif']['family'],
                                v['monospace']['family'])
        if key not in retval:
            retval[key] = {}
        retval[key][k] = v

    return retval


def json2langgroupdiff(data: dict[str, Any],
                       diffdata: dict[str, Any]) -> dict[str, dict[str, list[Any, Any]]]:
    """Restructure JSON format data."""
    retval = {}
    aliases = ['sans-serif', 'serif', 'monospace']
    for k, v in data.items():
        key = ''
        for a in aliases:
            key += '|{}'.format(v[a]['family'])
        for a in aliases:
            key += '|{}'.format(diffdata[k][a]['family'])
        if key not in retval:
            retval[key] = {}
        retval[key][k] = [v, diffdata[k]]

    return retval


def generate_table(renderer: DataRenderer, title: str, data: dict[str, Any]) -> Iterator[str]:
    """Format data to HTML."""
    sorteddata = json2data(data)
    renderer.title = title
    renderer.imagetype = data['pattern']
    yield from renderer.render_table(sorteddata)


def generate_diff(renderer: DataRenderer, title: str, data: dict[str, Any],
                  diffdata: dict[str, Any]) -> Iterator[str]:
    """Format difference between two JSONs to HTML."""
    sorteddata = json2data(data)
    sorteddiffdata = json2data(diffdata)
    matched = {}
    notmatched = {}
    missing_b = {}
    for k in sorted(sorteddata.keys()):
        if k not in sorteddiffdata:
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
    langdiffdata = json2langgroupdiff(notmatched, sorteddiffdata)

    renderer.title = title
    renderer.imagetype = data['pattern']
    renderer.imagedifftype = diffdata['pattern']

    yield from renderer.render_diff(langdata, missing_a, missing_b, langdiffdata)


def main():
    """Endpoint to execute fq2html program."""
    fmc = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=('HTML formatter '
                                                  'for fontquery'),
                                     formatter_class=fmc)
    renderer = {'html': HtmlRenderer,
                'text': TextRenderer}

    parser.add_argument('-o', '--output',
                        type=argparse.FileType('w'),
                        default='-',
                        help='Output file')
    parser.add_argument('-t', '--title',
                        help='Set title name')
    parser.add_argument('-d', '--diff',
                        type=argparse.FileType('r'),
                        help=('Output difference between FILE and DIFF'
                              ' as secondary'))
    parser.add_argument('-R', '--render',
                        default='html',
                        choices=renderer.keys())
    parser.add_argument('FILE',
                        type=argparse.FileType('r'),
                        help='JSON file to read or - to read from stdin')

    args = parser.parse_args()
    atexit.register(args.FILE.close)

    data = None
    with args.FILE:
        data = json.load(args.FILE)

    if args.diff is None:
        with args.output:
            for s in generate_table(renderer[args.render](), args.title, data):
                args.output.write(s)
    else:
        with args.diff:
            diffdata = json.load(args.diff)

        with args.output:
            for s in generate_diff(renderer[args.render](), args.title, data, diffdata):
                args.output.write(s)


if __name__ == '__main__':
    main()
