# Fontquery - Project Documentation for Claude Code

## Project Overview

**fontquery** is a Python tool for querying and comparing fonts across Fedora/CentOS releases. It uses container images to provide isolated environments for testing font availability and configuration across different OS versions.

- **Language:** Python 3.11+
- **License:** MIT
- **Maintainer:** Akira TAGOH (Red Hat)
- **Repository:** https://github.com/fedora-i18n/fontquery
- **Current Version:** 1.33 (see pyproject.toml:7)

### Purpose

- Query fonts from Fedora/CentOS releases using containerized environments
- Compare font differences between releases
- Test package changes impact on font availability
- Generate reports in multiple formats (JSON, HTML, fcmatch, fclist)

## Architecture

### Component Overview

```
fontquery/
├── frontend.py       # Main CLI entry point (fontquery command)
├── client.py         # Font querying logic (runs inside containers)
├── container.py      # Podman/Buildah container management
├── diff.py           # Release comparison (fontquery-diff)
├── pkgdiff.py        # Package impact testing (fontquery-pkgdiff)
├── build.py          # Container image building (fontquery-build)
├── cache.py          # JSON caching system
├── package.py        # RPM package metadata handling
├── htmlformatter.py  # HTML table generation (fq2html)
├── version.py        # Version utilities
├── data/             # Containerfile definitions
└── scripts/          # Shell scripts (fontquery-setup.sh)
```

### Execution Flow

1. **Frontend Layer** (`frontend.py`): Parses CLI args, manages releases
2. **Container Layer** (`container.py`): Pulls/runs podman containers
3. **Client Layer** (`client.py`): Executes fc-match/fc-list inside containers
4. **Cache Layer** (`cache.py`): Stores results in `~/.cache/fontquery/`

### Container Architecture

The tool uses multi-stage Containerfile builds with three targets:
- **minimal**: Default Fedora fonts (from comps groups)
- **extra**: Minimal + langpacks-fonts-* extras
- **all**: Everything including all available font packages

Images are hosted at: `ghcr.io/fedora-i18n/fontquery/{product}/{target}:{release}`

## Key Components

### Entry Points (pyproject.toml:38-44)

- `fontquery` → `frontend.py:main()` - Main query tool
- `fontquery-client` → `client.py:main()` - Container-internal querying
- `fontquery-diff` → `diff.py:main()` - Compare two releases
- `fontquery-pkgdiff` → `pkgdiff.py:main()` - Test package impact
- `fontquery-build` → `build.py:main()` - Build container images
- `fq2html` → `htmlformatter.py:main()` - Convert JSON to HTML

### Mode System

The `--mode` flag controls output format:
- `fcmatch`: Run fc-match queries (default)
- `fcmatchaliases`: fc-match with alias expansion
- `fclist`: List all fonts
- `json`: Structured data output
- `html`: HTML table (internally converts json→html)

### Target System

The `--target` flag selects font package sets:
- `minimal`: Base system fonts
- `extra`: Minimal + language-specific extras
- `all`: All available fonts

### Local vs Remote Queries

- **local**: Query fonts on current system (no containers)
- **release number**: Use containerized environment (requires podman)

## Development Workflow

### Building from Source

```bash
# Install build tools
pip3 install --user build wheel

# Build wheel
python3 -m build

# Install locally
pip3 install --user dist/fontquery*.whl
```

### Version Bumping

Version is defined in **one place**: `pyproject.toml:7`

The version number follows: MAJOR.MINOR format (e.g., 1.33)

**Container Images:** When building container images, `version.txt` is automatically updated with the build timestamp in `YYYYMMDDHHmmss` format (UTC). This allows tracking of exact container build dates independently of the package version.

### Container Development

Build development containers with local code:

```bash
# Build the wheel first
python3 -m build

# Build container with --debug flag
fontquery-build -r rawhide -t minimal --debug
```

The `--debug` flag copies your local wheel into the container instead of using PyPI.

## Dependencies (pyproject.toml:26-32)

- `markdown`: HTML formatting
- `langtable`: Language/locale handling
- `pyxdg`: XDG directory support (cache paths)
- `termcolor`: Colored terminal output
- `pyyaml`: YAML configuration

Runtime dependencies (inside containers):
- `fontconfig`: fc-match, fc-list commands
- `dnf`/`rpm`: Package management

## Conventions

### Code Style

- **Formatting**: Standard Python conventions
- **Imports**: Group by stdlib, third-party, local (see client.py:26-42)
- **Type hints**: Present in newer code (container.py uses typing)
- **Docstrings**: Use triple-quoted format with description

### Error Handling

- Use `sys.tracebacklimit = 0` to suppress full tracebacks for user-facing errors
- Raise `RuntimeError` with descriptive messages for execution failures
- Return exit codes via `sys.exit()` for CLI commands

### Verbose Logging

All major commands support `-v/--verbose` flag:
- Prints command lines being executed with `# ` prefix
- Uses `file=sys.stderr` for all debug output
- Multiple `-v` flags increase verbosity (counted with `action='count'`)

### File Paths

- Use `pathlib.Path` for all path operations (not string concatenation)
- Respect XDG cache directory: `~/.cache/fontquery/`
- Container resources use `importlib.resources.files()` with fallback

## Testing

### Manual Testing Workflow

```bash
# Test local fonts
fontquery -r local sans-serif:lang=hi

# Test against Fedora 40
fontquery -r 40 monospace

# Generate JSON and HTML
fontquery -r rawhide -t minimal -m html

# Compare releases
fontquery-diff -R text rawhide local

# Test package impact
fontquery-pkgdiff /path/to/font-package.rpm
```

### Quality Checks

The pre-commit hook likely runs:
- Linting checks
- Code formatting validation
- Import sorting

## Common Tasks

### Adding a New Mode

1. Add choice to `frontend.py:158` `--mode` choices
2. Implement logic in `client.py` (for container execution)
3. Handle output format in `frontend.py:main()`

### Supporting New OS Products

1. Update `container.py:64-74` registry mapping
2. Add product to `--product` choices in frontends
3. Update Containerfile if needed

### Modifying Cache Behavior

Cache logic is in `cache.py`:
- Cache path: `~/.cache/fontquery/{product}-{release}-{target}.json`
- Use `--disable-cache` to bypass reading
- Use `--clean-cache/-C` to delete before running

### Filename Format

Output files use format strings (frontend.py:141):
- Default: `{product}-{release}-{target}.{mode}`
- Override with `-f/--filename-format`
- Variables: `product`, `release`, `target`, `mode`

## Gotchas and Important Notes

### Container Requirements

- **Requires podman**: Not docker! The code explicitly uses `podman` commands
- **Buildah for building**: Image building uses `buildah`, not `podman build`
- **podman unshare**: Used for file operations (container.py:265)

### Target Option on Local Mode

⚠️ The `--target` option has **no effect** when using `-r local` mode. A runtime warning is emitted (frontend.py:217-219).

### Release Naming

CentOS Stream releases need special handling:
- Input: `9` → Becomes: `stream9`
- Logic in container.py:71-72 and frontend.py:51-53

### Image Registry

Different registries by product/version:
- Fedora ELN: `quay.io/fedoraci/fedora`
- Fedora: `quay.io/fedora/fedora`
- CentOS: `quay.io/centos/centos`

### Terminal Size Handling

Recent fix (PR #14): Use `shutil.get_terminal_size()` for better error handling instead of direct terminal queries.

### Debug Module

The code attempts to import `fontquery_debug` (optional):
- Excluded from packaging (pyproject.toml:51)
- For development/debugging only
- Import failures are caught and ignored

### JSON Output Files

The `.gitignore` excludes `*.json` and `*.html` files (lines 54-55) since these are generated artifacts.

## Release Process

1. Update version in `pyproject.toml:7`
2. Commit: "Bump the version to X.Y"
3. Build wheel: `python3 -m build`
4. Tag release: `git tag vX.Y`
5. Push to PyPI (maintainer only)
6. Fedora packaging: Update `python-fontquery.spec`

## Useful File Locations

- **Cache directory**: `~/.cache/fontquery/`
- **Container images**: `ghcr.io/fedora-i18n/fontquery/`
- **Setup script**: `fontquery/scripts/fontquery-setup.sh` (runs inside containers)
- **Containerfile**: `fontquery/data/Containerfile`

## External Resources

- **GitHub Issues**: https://github.com/fedora-i18n/fontquery/issues
- **PyPI Package**: https://pypi.org/project/fontquery/
- **Container Registry**: ghcr.io/fedora-i18n/fontquery/

## Language Support

Default language list (~150 languages) is defined in `client.py:47-72`. It falls back to a hardcoded list if `pyanaconda.localization` is unavailable.

Languages use langtable format: `lang_REGION` (e.g., `zh_cn`, `pt`, `hi`)

---

**Last Updated:** 2026-04-16 (v1.33)
