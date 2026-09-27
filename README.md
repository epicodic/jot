# jot

[![PyPI](https://img.shields.io/pypi/v/jot-editor)](https://pypi.org/project/jot-editor/)
[![Python versions](https://img.shields.io/pypi/pyversions/jot-editor)](https://pypi.org/project/jot-editor/)
[![CI](https://github.com/epicodic/jot/actions/workflows/ci.yml/badge.svg)](https://github.com/epicodic/jot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/epicodic/jot/blob/main/LICENSE)

A tiny inline terminal editor built specifically for git commit messages.

It renders directly in your terminal's scroll buffer, so there's no full-screen
takeover and no context switch. Write the message, hit <kbd>Ctrl</kbd>+<kbd>S</kbd>,
and your shell prompt comes back right below it.

![jot editing a commit message inline](https://raw.githubusercontent.com/epicodic/jot/main/docs/screenshot.svg)

## Features

- **Inline rendering**: the editor appears in place, below your `git commit`, and
  blends into your terminal's background color.
- **Batteries included**: line numbers, soft wrap, and tab indentation out of the box.
- **Message history**: every message you write is remembered, even if you cancel,
  so a failed commit hook never eats your text.
- **Cycle and search**: flip through past messages with <kbd>PgUp</kbd>/<kbd>PgDn</kbd>,
  or fuzzy-search them with <kbd>Ctrl</kbd>+<kbd>R</kbd>.

![Searching the message history with Ctrl+R](https://raw.githubusercontent.com/epicodic/jot/main/docs/screenshot-search.svg)

## Installation

jot is a command-line tool, so install it in its own isolated environment with
[uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/):

```sh
uv tool install jot-editor
# or
pipx install jot-editor
```

This puts the `jot` command on your `PATH`. The package on PyPI is named
`jot-editor`.

To try it without installing:

```sh
uvx --from jot-editor jot
```

## Usage

### As your git editor

```sh
git config --global core.editor jot
```

Or for a single commit:

```sh
GIT_EDITOR=jot git commit
```

Git's `#` comment lines stay visible while you type. If you cancel with
<kbd>Esc</kbd>, jot exits with status 1 and git aborts the commit. This also
applies to `git commit --amend`, `git rebase -i`, and so on.

### Standalone

```sh
jot path/to/file     # edit a file in place
jot                  # write a quick note; the text goes to stdout on save
jot > note.txt       # ...so you can redirect or pipe it
```

### Key bindings

| Key                              | Action                                      |
|----------------------------------|---------------------------------------------|
| <kbd>Ctrl</kbd>+<kbd>S</kbd>     | Save and exit                               |
| <kbd>Esc</kbd>                   | Cancel (exit status 1)                      |
| <kbd>PgUp</kbd>                  | Previous (older) message from history       |
| <kbd>PgDn</kbd>                  | Next (newer) message; past the newest restores your draft |
| <kbd>Ctrl</kbd>+<kbd>R</kbd>     | Search history (type to filter)             |
| <kbd>Enter</kbd> (in search)     | Apply the selected result and close search  |
| <kbd>Esc</kbd> (in search)       | Close search and return to the editor       |

## History

Every message is saved to `~/.cache/jot/git_history.json` when you save *or*
cancel, so nothing is ever lost. jot keeps the most recent 100 messages and
skips consecutive duplicates.

Lines starting with `#` (git's status comments) are never stored. When you apply
a history entry, only the message part is replaced and the comment lines in the
current file are kept.

The search panel matches the first line of each message and also the full text.
Results are listed newest first.

## Requirements

- Python 3.12 or newer
- Linux or macOS (jot uses POSIX terminal APIs; Windows isn't supported)
- For seamless blending with your theme, a terminal that answers the OSC 11
  background color query (most modern terminals do). Otherwise jot falls back to
  the default background.

## Contributing

Bug reports and pull requests are welcome. See [CONTRIBUTING.md](https://github.com/epicodic/jot/blob/main/CONTRIBUTING.md)
for the development setup.

## License

MIT. See [LICENSE](https://github.com/epicodic/jot/blob/main/LICENSE) for details.
