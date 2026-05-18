from pathlib import Path
import asyncio
import json
import sys

import pyte
import winpty

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Click, Key
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import DirectoryTree, Input, Label, RichLog, TextArea
from textual.theme import Theme


# ── Theme loading ─────────────────────────────────────────────────────────────

def _load_themes() -> list[dict]:
    try:
        data = json.loads((Path(__file__).parent / "ayu.json").read_text())
    except Exception:
        return []
    result = []
    for t in data["themes"]:
        s = t["style"]
        name = t["name"]
        slug = name.lower().replace(" ", "-")
        dark = t.get("appearance", "dark") == "dark"
        theme = Theme(
            name=slug,
            primary=s.get("text.accent", "#5ac1fe")[:7],
            secondary=s.get("text.muted", "#8a8986")[:7],
            accent=s.get("text.accent", "#5ac1fe")[:7],
            background=s.get("background", "#313337")[:7],
            surface=s.get("surface.background", "#1f2127")[:7],
            panel=s.get("elevated_surface.background", "#1f2127")[:7],
            foreground=s.get("text", "#bfbdb6")[:7],
            error=s.get("error", "#ef7177")[:7],
            success=s.get("success", "#aad84c")[:7],
            warning=s.get("warning", "#e6b450")[:7],
            dark=dark,
        )
        result.append({"name": name, "slug": slug, "theme": theme})
    return result


THEMES = _load_themes() or [{"name": "Ayu Dark", "slug": "textual-dark", "theme": None}]

# Key name → bytes to send to PTY
_KEY_MAP: dict[str, bytes] = {
    "enter":      b"\r",
    "backspace":  b"\x7f",
    "delete":     b"\x1b[3~",
    "tab":        b"\t",
    "escape":     b"\x1b",
    "up":         b"\x1b[A",
    "down":       b"\x1b[B",
    "right":      b"\x1b[C",
    "left":       b"\x1b[D",
    "home":       b"\x1b[H",
    "end":        b"\x1b[F",
    "pageup":     b"\x1b[5~",
    "pagedown":   b"\x1b[6~",
    "ctrl+c":     b"\x03",
    "ctrl+d":     b"\x04",
    "ctrl+l":     b"\x0c",
    "ctrl+a":     b"\x01",
    "ctrl+e":     b"\x05",
    "ctrl+u":     b"\x15",
    "ctrl+k":     b"\x0b",
    "ctrl+w":     b"\x17",
    "ctrl+z":     b"\x1a",
}


# ── Embedded terminal widget ──────────────────────────────────────────────────

class TerminalWidget(Widget, can_focus=True):
    """Embedded PowerShell terminal using winpty PTY + pyte screen emulator."""

    COLS = 200
    ROWS = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pty: winpty.PtyProcess | None = None
        self._screen = pyte.Screen(self.COLS, self.ROWS)
        self._stream = pyte.ByteStream(self._screen)
        self._read_task: asyncio.Task | None = None
        self._history: list[str] = []
        self._hist_idx: int = -1

    def compose(self) -> ComposeResult:
        yield RichLog(id="term-output", auto_scroll=True, markup=False, highlight=False)
        yield Input(id="term-input", placeholder="PowerShell>")

    def on_mount(self) -> None:
        self._start_pty()
        self.query_one("#term-input", Input).focus()

    def _start_pty(self) -> None:
        try:
            self._pty = winpty.PtyProcess.spawn(
                "powershell.exe",
                dimensions=(self.ROWS, self.COLS),
            )
            self._read_task = asyncio.get_event_loop().create_task(self._read_loop())
        except Exception as e:
            self.query_one("#term-output", RichLog).write(f"Failed to start PowerShell: {e}")

    async def _read_loop(self) -> None:
        log = self.query_one("#term-output", RichLog)
        loop = asyncio.get_event_loop()
        while self._pty and self._pty.isalive():
            try:
                data = await loop.run_in_executor(None, self._pty.read, 4096)
                if not data:
                    await asyncio.sleep(0.01)
                    continue
                raw = data.encode("utf-8", errors="replace") if isinstance(data, str) else data
                self._stream.feed(raw)
                # Render dirty lines from pyte screen
                for line_idx in sorted(self._screen.dirty):
                    line = self._screen.buffer[line_idx]
                    text = "".join(c.data for c in (line[col] for col in range(self._screen.columns))).rstrip()
                    if text:
                        log.write(text)
                self._screen.dirty.clear()
            except Exception:
                await asyncio.sleep(0.05)

    def on_key(self, event: Key) -> None:
        key = event.key
        inp = self.query_one("#term-input", Input)

        # History navigation
        if key == "up" and self._history:
            self._hist_idx = min(self._hist_idx + 1, len(self._history) - 1)
            inp.value = self._history[-(self._hist_idx + 1)]
            inp.cursor_position = len(inp.value)
            event.prevent_default()
            return
        if key == "down":
            if self._hist_idx > 0:
                self._hist_idx -= 1
                inp.value = self._history[-(self._hist_idx + 1)]
            else:
                self._hist_idx = -1
                inp.value = ""
            inp.cursor_position = len(inp.value)
            event.prevent_default()
            return

        # Forward special keys to PTY
        if key in _KEY_MAP:
            event.prevent_default()
            self._write_pty(_KEY_MAP[key])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value
        inp = self.query_one("#term-input", Input)
        inp.clear()
        if cmd:
            self._history.append(cmd)
        self._hist_idx = -1
        self._write_pty((cmd + "\r").encode())

    def _write_pty(self, data: bytes) -> None:
        if self._pty and self._pty.isalive():
            try:
                self._pty.write(data.decode("utf-8", errors="replace"))
            except Exception:
                pass

    def write(self, text: str) -> None:
        """Allow external code to write a message into the terminal log."""
        self.query_one("#term-output", RichLog).write(text)

    async def on_unmount(self) -> None:
        if self._read_task:
            self._read_task.cancel()
        if self._pty and self._pty.isalive():
            self._pty.terminate()


# ── Folder picker modal ───────────────────────────────────────────────────────

class FolderPicker(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    FolderPicker {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #dialog {
        width: 50;
        height: auto;
        padding: 2;
        background: #1f2127;
        border: solid #5ac1fe;
    }
    Label {
        width: 100%;
        margin-bottom: 1;
        color: #bfbdb6;
    }
    #folder-path { width: 100%; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Enter folder path:")
            yield Input(id="folder-path", placeholder="/path/to/folder")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Main app ──────────────────────────────────────────────────────────────────

class TrixApp(App):
    CSS = """
    Screen {
        layout: horizontal;
        background: #313337;
    }

    Container {
        border: solid #3f4043;
        border-title-align: center;
        background: #1f2127;
    }

    Container:focus-within {
        border: solid #5ac1fe;
    }

    #files-panel  { width: 20%; }
    #editor-panel { width: 2fr; }
    #terminal-panel { width: 2fr; }

    DirectoryTree {
        height: 100%;
        background: #1f2127;
    }

    DirectoryTree > .tree--cursor    { background: #3e4043; }
    DirectoryTree > .tree--highlight { background: #3e4043; }

    TextArea {
        height: 100%;
        background: #0d1016;
        color: #bfbdb6;
    }

    TextArea .text-area--gutter    { background: #0d1016; color: #4b4c4e; }
    TextArea .text-area--cursor    { background: #5ac1fe; }
    TextArea .text-area--selection { background: #1f2127; }

    TerminalWidget {
        height: 1fr;
        layout: vertical;
    }

    #term-output {
        height: 1fr;
        background: #0d1016;
        color: #bfbdb6;
    }

    #term-input {
        height: 3;
        dock: bottom;
        background: #0d1016;
        color: #bfbdb6;
        border: solid #3f4043;
    }

    #term-input:focus {
        border: solid #5ac1fe;
    }

    Input {
        background: #0d1016;
        color: #bfbdb6;
        border: solid #3f4043;
    }

    Input:focus {
        border: solid #5ac1fe;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
        ("ctrl+o", "open_folder", "Open Folder"),
        ("ctrl+t", "cycle_theme", "Cycle Theme"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False
        self._theme_index = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Container(id="files-panel"):
                yield DirectoryTree(".")
            with Container(id="editor-panel"):
                yield TextArea(id="editor", show_line_numbers=True)
            with Container(id="terminal-panel"):
                yield TerminalWidget(id="terminal")

    async def on_mount(self) -> None:
        for t in THEMES:
            if t["theme"] is not None:
                self.register_theme(t["theme"])
        self.query_one("#files-panel").border_title = " Files "
        self.query_one("#editor-panel").border_title = " Editor "
        self.query_one("#terminal-panel").border_title = " Terminal "

    # ── Click: focus terminal input when clicking terminal panel ──────────────

    def on_click(self, event: Click) -> None:
        terminal_panel = self.query_one("#terminal-panel")
        if terminal_panel.region.contains(event.screen_x, event.screen_y):
            inp = self.query_one("#term-input", Input)
            if self.focused is not inp:
                inp.focus()

    # ── File tree ─────────────────────────────────────────────────────────────

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return
        text_area = self.query_one("#editor", TextArea)
        text_area.load_text(content)
        text_area.language = self._detect_language(path)
        self._current_file = path
        self._has_changes = False
        self._update_editor_title()

    def on_text_area_changed(self) -> None:
        if self._current_file and not self._has_changes:
            self._has_changes = True
            self._update_editor_title()

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_save(self) -> None:
        if self._current_file is None:
            self.query_one("#terminal", TerminalWidget).write("[No file open]")
            return
        self._current_file.write_text(
            self.query_one("#editor", TextArea).text, encoding="utf-8"
        )
        self._has_changes = False
        self._update_editor_title()

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(THEMES)
        t = THEMES[self._theme_index]
        self.theme = t["slug"]
        self.query_one("#terminal", TerminalWidget).write(f"Theme: {t['name']}")

    async def action_open_folder(self) -> None:
        path_str = await self.push_screen_wait(FolderPicker())
        if path_str is None:
            return
        path = Path(path_str.strip())
        if not path.is_dir():
            self.query_one("#terminal", TerminalWidget).write(f"Invalid path: {path_str}")
            return
        self.query_one(DirectoryTree).path = path
        self._current_file = None
        self._has_changes = False
        self.query_one("#editor", TextArea).load_text("")
        self._update_editor_title()
        self.query_one("#files-panel").border_title = f" Files — {path.name} "

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_editor_title(self) -> None:
        panel = self.query_one("#editor-panel")
        if self._current_file is None:
            panel.border_title = " Editor "
        else:
            suffix = " *" if self._has_changes else ""
            panel.border_title = f" Editor — {self._current_file.name}{suffix} "

    def _detect_language(self, path: Path) -> str | None:
        return {
            ".py": "python", ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript", ".json": "json",
            ".html": "html", ".htm": "html", ".css": "css", ".md": "markdown",
            ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".sql": "sql",
            ".rs": "rust", ".go": "go", ".c": "c", ".cpp": "cpp",
            ".h": "c", ".hpp": "cpp", ".java": "java", ".sh": "bash",
            ".bash": "bash", ".rb": "ruby", ".php": "php",
            ".xml": "xml", ".svg": "xml",
        }.get(path.suffix.lower())


if __name__ == "__main__":
    TrixApp().run()
