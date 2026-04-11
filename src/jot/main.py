"""Tiny inline editor for git commit messages and quick notes."""

from __future__ import annotations

import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, TextArea


class JotApp(App[None]):
    CSS = """
    TextArea {
        height: 10;
        border: tall $accent;
    }
    Footer {
        height: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+q", "quit_cancel", "Cancel"),
        Binding("escape", "quit_cancel", "Cancel", show=False),
    ]

    def __init__(self, filepath: Path | None, initial_text: str) -> None:
        super().__init__()
        self.filepath = filepath
        self.initial_text = initial_text
        self.saved = False

    def compose(self) -> ComposeResult:
        yield TextArea(
            self.initial_text,
            tab_behavior="indent",
            show_line_numbers=False,
            soft_wrap=True,
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(TextArea).focus()

    def action_save(self) -> None:
        text = self.query_one(TextArea).text
        if self.filepath:
            self.filepath.write_text(text)
        else:
            # Temporarily restore stdout for output before inline app clears lines
            sys.stdout.write(text)
        self.saved = True
        self.exit()

    def action_quit_cancel(self) -> None:
        self.exit()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Tiny inline editor — Ctrl+S to save, Ctrl+Q/Esc to cancel"
    )
    parser.add_argument("file", nargs="?", help="File to edit (e.g. git commit msg)")
    args = parser.parse_args()

    filepath = Path(args.file) if args.file else None
    initial_text = filepath.read_text() if filepath and filepath.exists() else ""

    app = JotApp(filepath, initial_text)
    app.run(inline=True)

    if not app.saved:
        sys.exit(1)


if __name__ == "__main__":
    main()
