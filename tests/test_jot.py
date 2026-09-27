import asyncio
import json
from pathlib import Path

import pytest
from textual.widgets import Input, TextArea

from jot import main as jot_main
from jot.main import JotApp, _extract_message, load_git_history, save_to_git_history

TEMPLATE = "\n# Please enter the commit message for your changes.\n# On branch main\n"


@pytest.fixture(autouse=True)
def history_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "cache" / "git_history.json"
    monkeypatch.setattr(jot_main, "GIT_HISTORY_FILE", path)
    return path


def run_app(app: JotApp, *keys: str) -> str | None:
    """Run the app headlessly, press keys, and return the app's result."""

    async def drive() -> None:
        async with app.run_test() as pilot:
            await pilot.press(*keys)

    asyncio.run(drive())
    return app.return_value


# ── History storage ──────────────────────────────────────────────────────────


def test_extract_message_drops_comment_lines() -> None:
    assert _extract_message("fix: bug\n\nbody\n# comment\n") == "fix: bug\n\nbody"


def test_history_roundtrip(history_file: Path) -> None:
    save_to_git_history("first" + TEMPLATE)
    save_to_git_history("second")
    assert load_git_history() == ["first", "second"]
    assert json.loads(history_file.read_text()) == ["first", "second"]


def test_history_skips_empty_and_consecutive_duplicates() -> None:
    save_to_git_history(TEMPLATE)
    save_to_git_history("same")
    save_to_git_history("same")
    assert load_git_history() == ["same"]


def test_history_is_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jot_main, "MAX_HISTORY", 3)
    for i in range(5):
        save_to_git_history(f"msg {i}")
    assert load_git_history() == ["msg 2", "msg 3", "msg 4"]


def test_corrupt_history_is_ignored(history_file: Path) -> None:
    history_file.parent.mkdir(parents=True)
    history_file.write_text("{not json")
    assert load_git_history() == []


# ── Editor ───────────────────────────────────────────────────────────────────


def test_save_writes_file(tmp_path: Path) -> None:
    msg_file = tmp_path / "COMMIT_EDITMSG"
    app = JotApp(msg_file, TEMPLATE, bg_color=None)
    result = run_app(app, *"feat: hi", "ctrl+s")
    assert result == "feat: hi" + TEMPLATE
    assert msg_file.read_text() == result
    assert load_git_history() == ["feat: hi"]


def test_escape_cancels_but_keeps_history(tmp_path: Path) -> None:
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(TEMPLATE)
    app = JotApp(msg_file, TEMPLATE, bg_color=None)
    assert run_app(app, *"draft", "escape") is None
    assert msg_file.read_text() == TEMPLATE
    assert load_git_history() == ["draft"]


def test_history_cycling_preserves_comments_and_restores_draft() -> None:
    for msg in ["old", "new"]:
        save_to_git_history(msg)
    app = JotApp(None, "draft" + TEMPLATE, bg_color=None)

    async def drive() -> None:
        def text() -> str:
            return app.query_one(TextArea).text

        async with app.run_test() as pilot:
            await pilot.press("pageup")
            assert text() == "new" + TEMPLATE.rstrip("\n")
            await pilot.press("pageup")
            assert text().startswith("old\n#")
            await pilot.press("pagedown", "pagedown")
            assert text() == "draft" + TEMPLATE

    asyncio.run(drive())


def test_search_applies_matching_entry() -> None:
    for msg in ["fix: parser crash\n\ndetails", "docs: readme"]:
        save_to_git_history(msg)
    app = JotApp(None, "", bg_color=None)

    async def drive() -> None:
        async with app.run_test() as pilot:
            await pilot.press("ctrl+r", *"parser")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert app.query_one(TextArea).text == "fix: parser crash\n\ndetails"
            assert not app.query_one("#search-input", Input).display

    asyncio.run(drive())
