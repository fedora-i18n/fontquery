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

To query sans-serif for Hindi on Fedora 36,

``` shell
$ fontquery -r 36 sans-serif:lang=hi
Lohit-Devanagari.ttf: "Lohit Devanagari" "Regular"
```

To generate JSON from langpacks installed environment:

``` shell
$ fontquery -m json -t langpacks
...
```

To generate html table:

``` shell
$ fontquery -m json -t langpacks | fq2html -o langpacks.html -
```

Or simply

``` shell
$ fontquery -m html -t langpacks -r 40
```

To check difference between local and reference:

``` shell
$ fontquery-diff -R text rawhide local
```

## For developers

Before committing something into git repository, you may want to do:

``` shell
$ git config core.hooksPath hooks
```

to make sure our hook scripts works.
