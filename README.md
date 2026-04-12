# jot

A tiny inline terminal editor built specifically for git commit messages.

Renders directly in the terminal scroll buffer — no full-screen takeover, no context switch.

## Features

- Inline rendering: the editor appears in-place and the shell prompt returns below it when done
- Line numbers, soft wrap, and tab indentation out of the box
- Persists a commit message history and lets you cycle through or search past messages

## Installation

From a releases wheel (download from [GitHub Releases](https://github.com/epicodic/jot/releases)):

```sh
pipx install jot-*.whl
```
As a one-liner (requires `jq`):

> [!TIP]
> With pipx:
> ```sh
> pipx install $(curl -s https://api.github.com/repos/epicodic/jot/releases/latest \
>   | jq -r '.assets[] | select(.name | endswith(".whl")) | .browser_download_url')
> ```
> 
> With uv:
> ```sh
> uv tool install $(curl -s https://api.github.com/repos/epicodic/jot/releases/latest \
>   | jq -r '.assets[] | select(.name | endswith(".whl")) | .browser_download_url')
> ```

Or from source:

```sh
git clone https://github.com/epicodic/jot
cd jot
uv tool install .
```

## Usage

```sh
jot path/to/COMMIT_EDITMSG
```

| Key              | Action                          |
|------------------|---------------------------------|
| Ctrl+Enter       | Save and exit                   |
| Escape           | Cancel                          |
| Page Up          | Cycle to previous message       |
| Page Down        | Cycle to next message           |
| Ctrl+R           | Search history (type to filter) |
| Enter (in search)| Apply top result and close      |
| Escape (in search)| Close search, return to editor |

## History

Every message is saved to `~/.cache/jot/git_history.json` whether you save or
cancel, so nothing is ever lost. Lines starting with `#` (git's own status
comments) are never stored and are preserved in-place when applying a history
entry.

The search panel (Ctrl+R) filters the full history as you type. 
Page Up / Page Down cycles through history entries.

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

## License
MIT License. See [LICENSE](LICENSE) for details.