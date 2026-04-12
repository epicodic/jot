# jot

A tiny inline terminal editor for git commit messages and quick notes.

Renders directly in the terminal scroll buffer — no full-screen takeover, no context switch.

## Features

- Inline rendering: the editor appears in-place and the shell prompt returns below it when done
- Blends with your terminal: queries the terminal background color via OSC 11 and matches it
- Line numbers, soft wrap, and tab indentation out of the box
- Exits with code 1 on cancel so git aborts the commit cleanly

## Installation

From a releases wheel (download from [GitHub Releases](https://github.com/epicodic/jot/releases)):

```sh
pip install jot-*.whl
```

Or from source:

```sh
git clone https://github.com/epicodic/jot
cd jot
uv tool install .
```

## Usage

Edit a file:

```sh
jot path/to/file.txt
```

With no argument, edited text is written to stdout:

```sh
jot > note.txt
```

| Key     | Action          |
|---------|-----------------|
| Ctrl+S  | Save and exit   |
| Escape  | Cancel (exit 1) |

## Use as `$GIT_EDITOR`

```sh
git config --global core.editor jot
```

Or for a single session:

```sh
GIT_EDITOR=jot git commit
```

## Requirements

- Python 3.12+
- A terminal that supports OSC 11 (background color query) for seamless blending; falls back gracefully otherwise
