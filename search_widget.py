from __future__ import annotations
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Input, Label, ListItem, ListView, Static, TextArea
from textual.widgets.text_area import Selection

from themes import register_css_template

EDITOR_SEARCH_CSS = """
EditorSearch {
    height: auto;
    dock: top;
    background: #141820;
    border-bottom: solid #1f2a3a;
    padding: 0 1;
    layout: horizontal;
}
#es-label {
    width: auto;
    height: 3;
    content-align: center middle;
    color: #5ac1fe;
    padding: 0 1;
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
#es-nav-hint {
    width: auto;
    height: 3;
    content-align: center middle;
    color: #3f4043;
    padding: 0 1;
}
"""
register_css_template("editor_search", EDITOR_SEARCH_CSS)

_SEARCH_MATCH_KEY = "search.match"
_SEARCH_ACTIVE_KEY = "search.match.active"


def _inject_search_highlights(ta: TextArea, matches: list[tuple[int, int, int]], active_idx: int) -> None:
    """Inject all search match highlights directly into TextArea._highlights."""
    from rich.style import Style

    try:
        theme = ta._theme  # type: ignore[attr-defined]
        if theme is not None:
            theme.syntax_styles[_SEARCH_MATCH_KEY] = Style(bgcolor="#2d4a6e", color="#bfbdb6")
            theme.syntax_styles[_SEARCH_ACTIVE_KEY] = Style(bgcolor="#5ac1fe", color="#0d1016", bold=True)
    except Exception:
        pass

    if not hasattr(ta, "_search_backup_highlights"):
        ta._search_backup_highlights = {}  # type: ignore[attr-defined]

    _restore_search_highlights(ta)

    ta._search_backup_highlights = {row: list(entries) for row, entries in ta._highlights.items()}  # type: ignore[attr-defined]

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
        yield Label("🔍", id="es-label")
        yield Input(id="search-input", placeholder="Search in file…")
        yield Static("", id="search-count")
        yield Static("↑↓ navigate  Enter next  Esc close", id="es-nav-hint")

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
            count_label.update(f"[#5ac1fe]1[/#5ac1fe] / {len(self._matches)}")
            self._jump(0)
        else:
            count_label.update("[#ef7177]no results[/#ef7177]")
            _restore_search_highlights(ta)

    def _step(self, direction: int) -> None:
        if not self._matches:
            return
        self._idx = (self._idx + direction) % len(self._matches)
        self.query_one("#search-count", Static).update(
            f"[#5ac1fe]{self._idx + 1}[/#5ac1fe] / {len(self._matches)}"
        )
        self._jump(self._idx)

    def _jump(self, idx: int) -> None:
        if not self._matches:
            return
        row, col_start, col_end = self._matches[idx]
        ta = self._get_editor()
        ta.selection = Selection((row, col_start), (row, col_end))
        ta.scroll_cursor_visible()
        _inject_search_highlights(ta, self._matches, idx)


GLOBAL_SEARCH_CSS = """
GlobalSearch {
    height: auto;
    dock: top;
    background: #141820;
    border-bottom: solid #1f2a3a;
    padding: 0 1;
    layout: vertical;
}
#gs-header {
    height: auto;
    layout: horizontal;
    margin-bottom: 0;
}
#gs-label {
    width: auto;
    height: 3;
    content-align: center middle;
    color: #5ac1fe;
    padding: 0 1;
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
#gs-count {
    width: auto;
    height: 3;
    content-align: center middle;
    color: #4b4c4e;
    padding: 0 1;
}
#global-results {
    height: 10;
    background: #0d1016;
    border: solid #1f2a3a;
}
GlobalSearch ListItem {
    padding: 0 1;
    color: #bfbdb6;
    background: #0d1016;
    height: auto;
}
GlobalSearch ListItem:hover {
    background: #1f2430;
}
GlobalSearch ListView:focus > ListItem.--highlight {
    background: #1f4a6e;
    color: #5ac1fe;
}
"""
register_css_template("global_search", GLOBAL_SEARCH_CSS)


class GlobalSearch(Widget):
    """Global search bar docked inside the files panel."""

    DEFAULT_CSS = GLOBAL_SEARCH_CSS

    def compose(self) -> ComposeResult:
        with Horizontal(id="gs-header"):
            yield Label("🔎", id="gs-label")
            yield Input(id="global-search-input", placeholder="Search in files…")
            yield Static("", id="gs-count")
        yield ListView(id="global-results")

    def on_mount(self) -> None:
        self.display = False
        self._results: list[tuple[Path, int, str]] = []

    def open(self) -> None:
        self.display = True
        self.query_one("#global-search-input", Input).focus()

    def close(self) -> None:
        self.display = False
        self.query_one("#global-search-input", Input).value = ""
        self.query_one("#global-results", ListView).clear()
        self.query_one("#gs-count", Static).update("")
        self._results = []

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.close()
            event.prevent_default()

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value
        lv = self.query_one("#global-results", ListView)
        lv.clear()
        self._results = []
        count_label = self.query_one("#gs-count", Static)
        if not query or len(query) < 2:
            count_label.update("")
            return
        count_label.update("[#5ac1fe]searching…[/#5ac1fe]")
        self._run_search(query)

    @work(thread=True, exclusive=True)
    def _run_search(self, query: str) -> None:
        """Search files in a background thread to prevent TUI blocking."""
        try:
            tree = self.app.query_one("DirectoryTree")
            root = Path(str(tree.path))
        except Exception:
            return

        q_lower = query.lower()
        results: list[tuple[Path, int, str]] = []
        hit_count = 0

        # Excluded dirs/files for performance
        _SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox", "dist", "build"}
        _BINARY_SUFFIXES = {
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
            ".mp4", ".mp3", ".wav", ".pdf", ".zip", ".tar", ".gz",
            ".exe", ".so", ".dll", ".pyc",
        }

        for fpath in sorted(root.rglob("*")):
            if any(part in _SKIP_DIRS for part in fpath.parts):
                continue
            if not fpath.is_file():
                continue
            if fpath.suffix.lower() in _BINARY_SUFFIXES:
                continue
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lines = text.splitlines()
            for lineno, line in enumerate(lines):
                if q_lower in line.lower():
                    results.append((fpath, lineno, line.strip()))
                    hit_count += 1
                    if hit_count >= 200:
                        break
            if hit_count >= 200:
                break

        # Update UI on the main thread
        self.app.call_from_thread(self._display_results, results, query, hit_count)

    def _display_results(self, results: list, query: str, hit_count: int) -> None:
        """Display search results (runs on main thread via call_from_thread)."""
        try:
            lv = self.query_one("#global-results", ListView)
            count_label = self.query_one("#gs-count", Static)
        except Exception:
            return

        try:
            tree = self.app.query_one("DirectoryTree")
            root = Path(str(tree.path))
        except Exception:
            root = Path(".")

        lv.clear()
        self._results = results

        for fpath, lineno, line in results:
            try:
                rel = fpath.relative_to(root)
            except ValueError:
                rel = fpath
            snippet = line[:50]
            label = f"[#5ac1fe]{rel}[/#5ac1fe][#3f4043]:{lineno + 1}[/#3f4043]  {snippet}"
            lv.append(ListItem(Static(label, markup=True)))

        if hit_count == 0:
            count_label.update("[#ef7177]no results[/#ef7177]")
        elif hit_count >= 200:
            count_label.update(f"[#e6b450]200+ results[/#e6b450]")
        else:
            count_label.update(f"[#5ac1fe]{hit_count}[/#5ac1fe]")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is None or idx >= len(self._results):
            return
        fpath, lineno, _ = self._results[idx]
        try:
            content = fpath.read_text(encoding="utf-8")
        except Exception:
            return
        try:
            from main import TrixApp
            app: TrixApp = self.app  # type: ignore
            app._open_in_tab(fpath, content)
        except Exception:
            pass
        ta = self.app.query_one("#editor", TextArea)
        try:
            line_text = ta.document.get_line(lineno)
            ta.selection = Selection((lineno, 0), (lineno, len(line_text)))
        except Exception:
            pass
        ta.scroll_cursor_visible()
        ta.focus()
        self.close()
