# Fontquery Test Suite

This directory contains the test suite for fontquery.

## Running Tests

### Install test dependencies

```bash
pip install -e ".[dev]"
```

### Run all tests

```bash
pytest
```

### Run tests with coverage

```bash
pytest --cov=fontquery --cov-report=html
```

### Run specific test file

```bash
pytest tests/test_cache.py
```

### Run specific test

```bash
pytest tests/test_cache.py::TestFontQueryCache::test_save_and_read
```

## Test Structure

- `conftest.py` - Shared fixtures and pytest configuration
- `test_cache.py` - Tests for cache module
- `test_version.py` - Tests for version module
- `test_utils.py` - Tests for utils module
- `test_htmlformatter.py` - Tests for htmlformatter module
- `test_package.py` - Tests for package module

## Writing Tests

When writing new tests:

1. Follow the existing naming conventions (`test_*.py`, `Test*` classes, `test_*` functions)
2. Use fixtures from `conftest.py` when possible
3. Mock external dependencies (subprocess, file I/O, network calls)
4. Test both success and failure cases
5. Use descriptive test names that explain what is being tested

## Test Coverage

The test suite aims to cover:

- Core functionality (cache, version, utils)
- Helper functions (htmlformatter)
- Error handling and edge cases
- Package management utilities

Note: Integration tests that require podman/containers are not included in this suite
to keep tests fast and portable. Those should be run manually or in CI.
