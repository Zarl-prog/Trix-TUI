from __future__ import annotations
from collections import defaultdict
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Input, Label, ListItem, ListView, Static, TextArea
from textual.widgets.text_area import Selection


from themes import register_css_template

EDITOR_SEARCH_CSS = """
EditorSearch {
    height: auto;
    dock: top;
    background: #1f2127;
    border-bottom: solid #3f4043;
    padding: 0 1;
    layout: horizontal;
}
EditorSearch Input {
    width: 1fr;
    height: 3;
    border: solid #3f4043;
    background: #0d1016;
    color: #bfbdb6;
}
EditorSearch Input:focus {
    border: solid #5ac1fe;
}
#search-count {
    width: auto;
    height: 3;
    content-align: center middle;
    color: #4b4c4e;
    padding: 0 1;
}
"""
register_css_template("editor_search", EDITOR_SEARCH_CSS)

_SEARCH_MATCH_KEY = "search.match"
_SEARCH_ACTIVE_KEY = "search.match.active"


def _inject_search_highlights(ta: TextArea, matches: list[tuple[int, int, int]], active_idx: int) -> None:
    """Inject all search match highlights directly into TextArea._highlights."""
    from rich.style import Style

    # Register custom highlight styles on the active theme
    try:
        theme = ta._theme  # type: ignore[attr-defined]
        if theme is not None:
            theme.syntax_styles[_SEARCH_MATCH_KEY] = Style(bgcolor="#2d4a6e", color="#bfbdb6")
            theme.syntax_styles[_SEARCH_ACTIVE_KEY] = Style(bgcolor="#5ac1fe", color="#0d1016", bold=True)
    except Exception:
        pass

    # Back up original highlights (syntax) if not already done
    if not hasattr(ta, "_search_backup_highlights"):
        ta._search_backup_highlights = {}  # type: ignore[attr-defined]

    # Build per-row original highlights backup (first time only)
    # We always work on a fresh copy: restore clean then re-inject
    _restore_search_highlights(ta)

    # Backup current _highlights state
    ta._search_backup_highlights = {row: list(entries) for row, entries in ta._highlights.items()}  # type: ignore[attr-defined]

    # Inject our highlights on top
    for i, (row, col_start, col_end) in enumerate(matches):
        key = _SEARCH_ACTIVE_KEY if i == active_idx else _SEARCH_MATCH_KEY
        ta._highlights[row].append((col_start, col_end, key))  # type: ignore[attr-defined]

    ta.refresh()


def _restore_search_highlights(ta: TextArea) -> None:
    """Remove injected search highlights, restoring original syntax highlights."""
    backup = getattr(ta, "_search_backup_highlights", None)
    if backup is not None:
        ta._highlights.clear()  # type: ignore[attr-defined]
        ta._highlights.update(backup)  # type: ignore[attr-defined]
        ta._search_backup_highlights = {}  # type: ignore[attr-defined]
        ta.refresh()


class EditorSearch(Widget):
    """Inline search bar docked inside the editor panel."""

    DEFAULT_CSS = EDITOR_SEARCH_CSS

    def compose(self) -> ComposeResult:
        yield Input(id="search-input", placeholder="Search…")
        yield Static("", id="search-count")

    def on_mount(self) -> None:
        self.display = False
        self._matches: list[tuple[int, int, int]] = []
        self._idx = 0

    def open(self) -> None:
        self.display = True
        self.query_one("#search-input", Input).focus()
        self._matches = []
        self._idx = 0

    def close(self) -> None:
        self.display = False
        inp = self.query_one("#search-input", Input)
        inp.value = ""
        self.query_one("#search-count", Static).update("")
        # Clear all search highlights from editor
        try:
            _restore_search_highlights(self._get_editor())
        except Exception:
            pass
        self._matches = []
        self._idx = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        self._run_search(event.value)

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.close()
            self._get_editor().focus()
            event.prevent_default()
        elif event.key == "enter":
            self._step(1)
            event.prevent_default()
        elif event.key == "shift+enter":
            self._step(-1)
            event.prevent_default()

    def _get_editor(self) -> TextArea:
        return self.app.query_one("#editor", TextArea)

    def _run_search(self, query: str) -> None:
        self._matches = []
        self._idx = 0
        count_label = self.query_one("#search-count", Static)
        ta = self._get_editor()

        if not query:
            count_label.update("")
            _restore_search_highlights(ta)
            return

        text = ta.text
        q_lower = query.lower()
        lines = text.split("\n")
        for row, line in enumerate(lines):
            col = 0
            line_lower = line.lower()
            while True:
                found = line_lower.find(q_lower, col)
                if found == -1:
                    break
                self._matches.append((row, found, found + len(query)))
                col = found + 1

        if self._matches:
            count_label.update(f"1 of {len(self._matches)}")
            self._jump(0)
        else:
            count_label.update("No results")
            _restore_search_highlights(ta)

    def _step(self, direction: int) -> None:
        if not self._matches:
            return
        self._idx = (self._idx + direction) % len(self._matches)
        self.query_one("#search-count", Static).update(
            f"{self._idx + 1} of {len(self._matches)}"
        )
        self._jump(self._idx)

    def _jump(self, idx: int) -> None:
        if not self._matches:
            return
        row, col_start, col_end = self._matches[idx]
        ta = self._get_editor()
        ta.selection = Selection((row, col_start), (row, col_end))
        ta.scroll_cursor_visible()
        # Redraw all highlights with updated active index
        _inject_search_highlights(ta, self._matches, idx)



GLOBAL_SEARCH_CSS = """
GlobalSearch {
    height: auto;
    dock: top;
    background: #1f2127;
    border-bottom: solid #3f4043;
    padding: 0 1;
    layout: vertical;
}
GlobalSearch Input {
    width: 1fr;
    height: 3;
    border: solid #3f4043;
    background: #0d1016;
    color: #bfbdb6;
}
GlobalSearch Input:focus {
    border: solid #5ac1fe;
}
#global-results {
    height: 10;
    background: #0d1016;
    border: solid #3f4043;
}
GlobalSearch ListItem {
    padding: 0 1;
    color: #bfbdb6;
    background: #0d1016;
}
GlobalSearch ListItem:hover {
    background: #3f4043;
}
GlobalSearch ListView:focus > ListItem.--highlight {
    background: #5ac1fe;
}
"""
register_css_template("global_search", GLOBAL_SEARCH_CSS)


class GlobalSearch(Widget):
    """Global search bar docked inside the files panel."""

    DEFAULT_CSS = GLOBAL_SEARCH_CSS

    def compose(self) -> ComposeResult:
        yield Input(id="global-search-input", placeholder="Search in files…")
        yield ListView(id="global-results")

    def on_mount(self) -> None:
        self.display = False
        self._results: list[tuple[Path, int, str]] = []  # (path, line_no, line_text)

    def open(self) -> None:
        self.display = True
        self.query_one("#global-search-input", Input).focus()

    def close(self) -> None:
        self.display = False
        self.query_one("#global-search-input", Input).value = ""
        self.query_one("#global-results", ListView).clear()
        self._results = []

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.close()
            event.prevent_default()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._run_search(event.value)

    def _run_search(self, query: str) -> None:
        lv = self.query_one("#global-results", ListView)
        lv.clear()
        self._results = []
        if not query or len(query) < 2:
            return
        try:
            tree = self.app.query_one("DirectoryTree")
            root = Path(str(tree.path))
        except Exception:
            return
        q_lower = query.lower()
        for fpath in sorted(root.rglob("*")):
            if not fpath.is_file():
                continue
            try:
                lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue
            for lineno, line in enumerate(lines):
                if q_lower in line.lower():
                    self._results.append((fpath, lineno, line.strip()))
                    rel = fpath.relative_to(root)
                    label = f"{rel}:{lineno + 1}  {line.strip()[:60]}"
                    lv.append(ListItem(Static(label)))
                    if len(self._results) >= 200:
                        return

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is None or idx >= len(self._results):
            return
        fpath, lineno, _ = self._results[idx]
        try:
            content = fpath.read_text(encoding="utf-8")
        except Exception:
            return
        ta = self.app.query_one("#editor", TextArea)
        ta.load_text(content)
        try:
            from main import TrixApp
            app: TrixApp = self.app  # type: ignore
            app._current_file = fpath
            app._has_changes = False
            app._refresh_ui()
        except Exception:
            pass
        line_text = ta.document.get_line(lineno)
        ta.selection = Selection((lineno, 0), (lineno, len(line_text)))
        ta.scroll_cursor_visible()
        ta.focus()
        self.close()
