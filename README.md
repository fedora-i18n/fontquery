# Fontquery

fontquery is a tool to query fonts in the certain Fedora release.

## Usage

```
usage: fontquery [-h] [-r RELEASE] [-m {fcmatch,fclist}] [-v] [args ...]

Query fonts

positional arguments:
  args                  Queries (default: None)

options:
  -h, --help            show this help message and exit
  -r RELEASE, --release RELEASE
                        Release number (default: rawhide)
  -m {fcmatch,fclist}, --mode {fcmatch,fclist}
                        Action to perform for query (default: fcmatch)
  -v, --verbose         Show more detailed logs (default: False)
```

To query sans-serif for Hindi on Fedora 36,

```
$ fontquery -r 36 sans-serif:lang=hi
Lohit-Devanagari.ttf: "Lohit Devanagari" "Regular"
```
