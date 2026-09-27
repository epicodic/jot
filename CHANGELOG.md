# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0]

### Added

- Published on PyPI as `jot-editor` (`uv tool install jot-editor`).
- `--version` flag.
- Test suite and CI on Linux and macOS for Python 3.12 to 3.14.

### Changed

- Cancelling with Esc now exits with status 1, so git aborts the commit
  instead of reusing the previous message (for example with `--amend`).
- Without a file argument, the saved text is printed to stdout after the
  editor has closed instead of while it is still drawing.

## [0.1.0]

- Initial release: inline editor with line numbers, soft wrap, message history,
  PgUp/PgDn cycling, and Ctrl+R search.

[Unreleased]: https://github.com/epicodic/jot/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/epicodic/jot/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/epicodic/jot/releases/tag/v0.1.0
