# Fontquery
[![pip version badge](https://img.shields.io/pypi/v/fontquery)](https://pypi.org/project/fontquery/)
[![tag badge](https://img.shields.io/github/v/tag/fedora-i18n/fontquery)](https://github.com/fedora-i18n/fontquery/tags)
[![license badge](https://img.shields.io/github/license/fedora-i18n/fontquery)](./LICENSE)

fontquery is a tool to query fonts in the certain Fedora release.

## How to install

``` shell
$ pip3 install fontquery
```

Or in Fedora,

``` shell
# dnf install fontquery
```

## How to install from git

``` shell
$ pip3 install --user build wheel
$ python3 -m build
$ pip3 install --user dist/fontquery*.whl
```

Or in Fedora,

``` shell
# dnf install python3-build python3-wheel
$ python3 -m build
$ pip3 install --user dist/fontquery*.whl
```

## Usage

```
usage: fontquery [-h] [-C] [--disable-cache] [-f FILENAME_FORMAT] [-r RELEASE] [-l LANG]
                 [-m {fcmatch,fclist,json,html}] [-O OUTPUT_DIR] [-t {minimal,extra,all}] [-T TITLE] [-v] [-V]
                 [args ...]

Query fonts

positional arguments:
  args                  Queries (default: None)

options:
  -h, --help            show this help message and exit
  -C, --clean-cache     Clean caches before processing (default: False)
  --disable-cache       Enforce processing everything even if not updating (default: False)
  -f FILENAME_FORMAT, --filename-format FILENAME_FORMAT
                        Output filename format. only take effects with --mode=html (default:
                        {platform}-{release}-{target}.{mode})
  -r RELEASE, --release RELEASE
                        Release number such as "rawhide" and "39". "local" to query from current environment
                        instead of images (default: ['local'])
  -l LANG, --lang LANG  Language list to dump fonts data into JSON (default: None)
  -m {fcmatch,fclist,json,html}, --mode {fcmatch,fclist,json,html}
                        Action to perform for query (default: fcmatch)
  -O OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: .)
  -t {minimal,extra,all}, --target {minimal,extra,all}
                        Query fonts from (default: minimal)
  -T TITLE, --title TITLE
                        Page title format. only take effects with --mode=html (default: {platform} {release}:
                        {target})
  -v, --verbose         Show more detailed logs (default: 0)
  -V, --version         Show version (default: False)
```

```
usage: fontquery-diff [-h] [-C] [--disable-cache] [--disable-update] [-l LANG] [--loose-comparison] [-o OUTPUT] [-P {fedora,centos}]
                      [-R {html,text}] [-t {minimal,extra,all}] [-v] [-V]
                      [compare_a] [compare_b]

Show difference between releases

positional arguments:
  compare_a             Release to compare (default: rawhide)
  compare_b             Release to compare (default: local)

options:
  -h, --help            show this help message and exit
  -C, --clean-cache     Clean up caches before processing (default: False)
  --diff-only           Show diff only (default: False)
  --disable-cache       Enforce processing everything even if not updating (default: False)
  --disable-update      Do not update the container image (default: False)
  -l, --lang LANG       Language list to dump fonts data into JSON (default: None)
  --loose-comparison    Do not compare results accurately (default: False)
  -o, --output OUTPUT   Output file (default: -)
  -P, --product {fedora,centos}
                        Product name to operate (default: fedora)
  -R, --render {html,text}
  -t, --target {minimal,extra,all}
                        Query fonts from (default: minimal)
  -v, --verbose         Show more detailed logs (default: 0)
  -V, --version         Show version (default: False)
```

```
usage: fontquery-pkgdiff [-h] [-C] [--disable-cache] [--disable-update] [-r RELEASE] [-l LANG] [--loose-comparison] [-o OUTPUT]
                         [-P {fedora,centos}] [-R {html,text}] [-t {minimal,extra,all}] [-v] [-V]
                         package [package ...]

Check if a given package makes any difference

positional arguments:
  package               Test package to see difference

options:
  -h, --help            show this help message and exit
  -C, --clean-cache     Clean up caches before processing (default: False)
  --diff-only           Show diff only (default: False)
  --disable-cache       Enforce processing everything even if not updating (default: False)
  --disable-update      Do not update the container image (default: False)
  -r, --release RELEASE
                        Target release to check (default: rawhide)
  -l, --lang LANG       Language list to dump fonts data into JSON (default: None)
  --loose-comparison    Do not compare results accurately (default: False)
  -o, --output OUTPUT   Output file (default: -)
  -P, --product {fedora,centos}
                        Product name to operate (default: fedora)
  -R, --render {html,text}
  -t, --target {minimal,extra,all}
                        Query fonts from (default: minimal)
  -v, --verbose         Show more detailed logs (default: 0)
  -V, --version         Show version (default: False)
```

To query sans-serif for Hindi on Fedora 36,

``` shell
$ fontquery -r 36 sans-serif:lang=hi
Lohit-Devanagari.ttf: "Lohit Devanagari" "Regular"
```

To generate JSON from default-fonts installed environment:

``` shell
$ fontquery -m json -t minimal
...
```

To generate html table:

``` shell
$ fontquery -m json -t minimal | fq2html -o minimal.html -
```

Or simply

``` shell
$ fontquery -m html -t minimal -r 40
```

To check difference between local and reference:

``` shell
$ fontquery-diff -R text rawhide local
```

To check difference but ignore insignificant changes such as filename:

``` shell
$ fontquery-diff --loose-comparison -R text
```

To check difference with certain packages:

``` shell
$ fontquery-pkgdiff /path/to/package ...
```

## For developers

Before committing something into git repository, you may want to do:

``` shell
$ git config core.hooksPath hooks
```

to make sure our hook scripts works.
