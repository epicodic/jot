"""Tiny inline editor for git commit messages and quick notes."""

from __future__ import annotations

import argparse
import os
import re
import select
import sys
import termios
import tty
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, TextArea


def get_terminal_background() -> str | None:
    """Query terminal background color via OSC 11. Returns hex string like '#1e1e1e' or None."""
    if not sys.stdin.isatty():
        return None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdout.write("\033]11;?\007")
        sys.stdout.flush()
        chunks: list[bytes] = []
        timeout = 0.2  # longer wait for first chunk
        while select.select([fd], [], [], timeout)[0]:
            chunks.append(os.read(fd, 4096))
            timeout = 0.05  # short wait for subsequent chunks
        resp = b"".join(chunks).decode(errors="replace")

        # Response looks like: \033]11;rgb:RRRR/GGGG/BBBB\007
        m = re.search(r"rgb:([0-9a-fA-F]+)/([0-9a-fA-F]+)/([0-9a-fA-F]+)", resp)
        if m:
            r, g, b = [int(x[:2], 16) for x in m.groups()]  # take high byte
            return f"#{r:02x}{g:02x}{b:02x}"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return None


class JotApp(App[None]):
    """Inline Textual editor. Renders inside the terminal scroll buffer."""

    # {bg_color} is substituted at runtime with the detected terminal background.
    CSS = """
    Screen {
        background: {bg_color};
        border: none;
    }
    TextArea {
        height: 5;
        background: transparent;
    }
    Footer {
        height: 1;
        background: transparent;
    }
    """

    INLINE_PADDING = 0  # suppress the default blank line Textual adds above inline apps

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "quit_cancel", "Cancel", priority=True, show=True),
    ]

    def __init__(
        self, filepath: Path | None, initial_text: str, bg_color: str | None
    ) -> None:
        self.filepath = filepath
        self.initial_text = initial_text
        self.bg_color = bg_color
        self.saved = False
        # Inject the background color before Textual parses the CSS.
        self.CSS = self.CSS.replace("{bg_color}", bg_color or "transparent")
        super().__init__()

    def compose(self) -> ComposeResult:
        yield TextArea(
            self.initial_text,
            show_line_numbers=True,
            tab_behavior="indent",
            soft_wrap=True,
            compact=True,  # removes border including the :focus override
        )
        yield Footer(compact=True, show_command_palette=False)

    def on_mount(self) -> None:
        self.query_one(TextArea).focus()

    def action_save(self) -> None:
        """Write the edited text and exit with success."""
        text = self.query_one(TextArea).text
        if self.filepath:
            self.filepath.write_text(text)
        else:
            sys.stdout.write(text)
        self.saved = True
        self.exit()

    def action_quit_cancel(self) -> None:
        """Exit without saving. Caller checks app.saved to detect cancellation."""
        self.exit()


def main() -> None:
    """Entry point. Detects terminal background, opens the editor, exits 1 on cancel."""
    bg_color = get_terminal_background()

    parser = argparse.ArgumentParser(
        description="Tiny inline editor — Ctrl+S to save, Ctrl+Q/Esc to cancel"
    )
    parser.add_argument("file", nargs="?", help="File to edit (e.g. git commit msg)")
    args = parser.parse_args()

    filepath = Path(args.file) if args.file else None
    initial_text = filepath.read_text() if filepath and filepath.exists() else ""

    app = JotApp(filepath, initial_text, bg_color)
    app.run(inline=True)

    if not app.saved:
        sys.exit(1)


if __name__ == "__main__":
    main()
