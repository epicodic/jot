"""Tiny inline editor for git commit messages."""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import sys
import termios
import tty
from pathlib import Path

from textual.app import App, ComposeResult, format_key
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Footer, Input, TextArea
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

GIT_HISTORY_FILE = Path.home() / ".cache" / "jot" / "git_history.json"
MAX_HISTORY = 100


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


def _extract_message(text: str) -> str:
    """Return non-comment lines from text, stripped of leading/trailing whitespace."""
    return "\n".join(
        line for line in text.splitlines() if not line.startswith("#")
    ).strip()


def load_git_history() -> list[str]:
    """Load git message history from the cache file."""
    if GIT_HISTORY_FILE.exists():
        try:
            data = json.loads(GIT_HISTORY_FILE.read_text())
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_to_git_history(text: str) -> None:
    """Extract non-comment lines from text and append to git history."""
    message = _extract_message(text)
    if not message:
        return
    history = load_git_history()
    if history and history[-1] == message:
        return  # avoid saving identical consecutive entries
    history.append(message)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    GIT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    GIT_HISTORY_FILE.write_text(json.dumps(history, indent=2))


class HistoryAutoComplete(AutoComplete):
    """AutoComplete that searches full commit messages but shows only their first line."""

    class Completed(Message):
        """Posted when the user picks a history entry."""

        def __init__(self, message: str) -> None:
            self.message = message
            super().__init__()

    def __init__(self, target: Input, history: list[str]) -> None:
        # Build newest-first, deduplicated candidates.
        # _lookup maps first_line → full_message (latest entry wins for duplicates).
        self._lookup: dict[str, str] = {}
        candidates: list[DropdownItem] = []
        seen: set[str] = set()
        for msg in reversed(history):  # reversed so newest comes first
            first_line = msg.split("\n")[0]
            if first_line not in seen:
                seen.add(first_line)
                self._lookup[first_line] = msg
                candidates.append(DropdownItem(first_line))
        super().__init__(target, candidates=candidates)

    def match(self, query: str, candidate: str) -> tuple[float, tuple[int, ...]]:
        """Match against the full commit message; highlight what matched in the first line."""
        # Try matching the first line — gives proper character highlights in the dropdown.
        score, offsets = self._fuzzy_search.match(query, candidate)
        if score > 0:
            return float(score), tuple(offsets)
        # Fall back: match anywhere in the full message (no per-character highlights).
        full_msg = self._lookup.get(candidate, candidate)
        full_score, _ = self._fuzzy_search.match(query, full_msg)
        if full_score > 0:
            return float(full_score) * 0.5, ()
        return 0.0, ()

    def apply_completion(self, value: str, state: TargetState) -> None:
        """Intercept selection: notify the app with the full commit text."""
        full_msg = self._lookup.get(value)
        if full_msg:
            self.post_message(self.Completed(full_msg))
        # Don't call super() — the app handles applying the text to the TextArea.


class JotApp(App[None]):
    """Inline Textual editor for git commit messages."""

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
    #search-input {
        display: none;
        background: $boost;
        height: 1;
        padding: 0;
        border: none;
    }
    Footer {
        height: 1;
        background: transparent;
    }
    """

    INLINE_PADDING = 0  # suppress the default blank line Textual adds above inline apps

    BINDINGS = [
        Binding("ctrl+enter", "save", "Save"),
        Binding("ctrl+r", "search", "Search history"),
        Binding("escape", "quit_cancel", "Cancel", priority=True, show=True),
        Binding("pageup", "history_prev", "Prev msg", priority=True, show=True),
        Binding("pagedown", "history_next", "Next msg", priority=True, show=True),
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
        self.git_history = load_git_history()
        # Index past the end means "current" (not browsing history).
        self.history_index = len(self.git_history)
        # Saved when the user first starts cycling, so we can restore it.
        self._pre_cycle_text: str | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        search_input = Input(placeholder="Search history…", id="search-input")
        yield search_input
        yield HistoryAutoComplete(search_input, self.git_history)
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

    def get_key_display(self, binding: Binding) -> str:
        if binding.key_display:
            return binding.key_display
        modifiers, key = binding.parse_key()
        key = format_key(key)
        if "ctrl" in modifiers:
            modifiers.remove("ctrl")
            key = f"Ctrl+{key.upper()}"
        return "+".join(modifiers + [key])

    def _apply_history(self, message: str) -> None:
        """Replace non-comment lines in the editor with message, preserving # lines."""
        ta = self.query_one(TextArea)
        comment_lines = [line for line in ta.text.splitlines() if line.startswith("#")]
        if comment_lines:
            new_text = message + "\n" + "\n".join(comment_lines)
        else:
            new_text = message
        ta.load_text(new_text)

    # ── History cycling ───────────────────────────────────────────────────────

    def action_history_prev(self) -> None:
        """Cycle to the previous (older) git message."""
        if not self.git_history:
            return
        if self.history_index == len(self.git_history):
            # Snapshot the user's current text before we start cycling.
            self._pre_cycle_text = self.query_one(TextArea).text
        if self.history_index > 0:
            self.history_index -= 1
            self._apply_history(self.git_history[self.history_index])

    def action_history_next(self) -> None:
        """Cycle to the next (newer) git message."""
        if self.history_index >= len(self.git_history):
            return
        self.history_index += 1
        if self.history_index == len(self.git_history):
            # Stepped past the newest entry — restore the pre-cycle text.
            if self._pre_cycle_text is not None:
                self.query_one(TextArea).load_text(self._pre_cycle_text)
        else:
            self._apply_history(self.git_history[self.history_index])

    # ── History search ────────────────────────────────────────────────────────

    def action_search(self) -> None:
        """Toggle the history search input."""
        search_input = self.query_one("#search-input", Input)
        if search_input.display:
            self._close_search()
            return
        search_input.display = True
        search_input.focus()

    def _close_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.display = False
        search_input.value = ""
        self.query_one(TextArea).focus()

    def on_history_auto_complete_completed(
        self, event: HistoryAutoComplete.Completed
    ) -> None:
        self._apply_history(event.message)
        self._close_search()

    # ── Save / cancel ─────────────────────────────────────────────────────────

    def action_save(self) -> None:
        """Write the edited text and exit with success."""
        text = self.query_one(TextArea).text
        save_to_git_history(text)
        if self.filepath:
            self.filepath.write_text(text)
        else:
            sys.stdout.write(text)
        self.saved = True
        self.exit()

    def action_quit_cancel(self) -> None:
        """Escape: close search if open, otherwise cancel the editor."""
        if self.query_one("#search-input", Input).display:
            self._close_search()
            return
        save_to_git_history(self.query_one(TextArea).text)
        self.exit()


def main() -> None:
    """Entry point. Detects terminal background, opens the editor, exits 1 on cancel."""
    bg_color = get_terminal_background()

    parser = argparse.ArgumentParser(
        description="Tiny inline git commit editor — Ctrl+S to save, Esc to cancel"
    )
    parser.add_argument("file", nargs="?", help="File to edit (git commit message)")
    args = parser.parse_args()

    filepath = Path(args.file) if args.file else None
    initial_text = filepath.read_text() if filepath and filepath.exists() else ""

    app = JotApp(filepath, initial_text, bg_color)
    app.run(inline=True)


if __name__ == "__main__":
    main()
