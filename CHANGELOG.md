# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-18

### Added

- Installable Python package metadata and typed public API.
- `format_r` for producing reusable string representations.
- Circular-reference detection, deterministic set formatting, slotted-object support, and
  case-insensitive field redaction.
- Automated tests and a multi-version GitHub Actions workflow.

### Changed

- ANSI colors now default to automatic terminal detection in `print_r`.
- Namedtuples and dataclasses retain their field names when formatted.
- Formatting and output responsibilities are separated while preserving the original
  `print_r` positional calling convention.

### Fixed

- Boolean values use their intended color instead of the integer color.
- Disabling ANSI colors now applies consistently at every nesting level.
- Circular values no longer terminate formatting with `RecursionError`.

[Unreleased]: https://github.com/Fidelissimus/print_r/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Fidelissimus/print_r/releases/tag/v0.1.0
