from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.events import Click
from textual.widgets import DirectoryTree, Input, RichLog, Static, TextArea

from themes import THEMES
from terminal_widget import TerminalWidget
from divider_widget import Divider
from screens import FolderPicker, HelpScreen


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

    #files-panel  { width: 20%; min-width: 10%; }
    #editor-panel { width: 2fr; min-width: 20%; }
    #terminal-panel { width: 2fr; min-width: 20%; }

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

    #term-output:focus {
        border: solid #5ac1fe;
    }

    #term-output .rich-log--highlight {
        background: #1f4a6e;
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

    #help-hint {
        dock: bottom;
        align-horizontal: right;
        width: auto;
        background: #1f2127;
        color: #5ac1fe;
        text-style: bold;
        height: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
        ("ctrl+o", "open_folder", "Open Folder"),
        ("ctrl+t", "cycle_theme", "Cycle Theme"),
        ("ctrl+shift+c", "copy_selection", "Copy"),
        ("ctrl+b", "toggle_filetree", "Toggle File Tree"),
        ("f11", "zen_mode", "Zen Mode"),
        ("question_mark", "show_help", "Help"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False
        self._theme_index = 0
        self._filetree_visible = True
        self._zen_mode = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Container(id="files-panel"):
                yield DirectoryTree(".")
            yield Divider("files-panel", "editor-panel", id="divider-files")
            with Container(id="editor-panel"):
                yield TextArea(id="editor", show_line_numbers=True)
            yield Divider("editor-panel", "terminal-panel")
            with Container(id="terminal-panel"):
                yield TerminalWidget(id="terminal")
        yield Static("  ? Help ", id="help-hint", markup=False)

    async def on_mount(self) -> None:
        for t in THEMES:
            if t["theme"] is not None:
                self.register_theme(t["theme"])
        self.query_one("#files-panel").border_title = " Files "
        self.query_one("#editor-panel").border_title = " Editor "
        self.query_one("#terminal-panel").border_title = " Terminal "

    def on_click(self, event: Click) -> None:
        terminal_panel = self.query_one("#terminal-panel")
        inp = self.query_one("#term-input", Input)
        log = self.query_one("#term-output", RichLog)
        if terminal_panel.region.contains(event.screen_x, event.screen_y):
            if log.region.contains(event.screen_x, event.screen_y):
                log.focus()
            elif self.focused is not inp:
                inp.focus()

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
        try:
            text_area.language = self._detect_language(path)
        except Exception:
            text_area.language = None
        self._current_file = path
        self._has_changes = False
        self._update_editor_title()

    def on_text_area_changed(self) -> None:
        if self._current_file and not self._has_changes:
            self._has_changes = True
            self._update_editor_title()

    def action_zen_mode(self) -> None:
        self._zen_mode = not self._zen_mode
        show = not self._zen_mode
        self.query_one("#files-panel").display = show and self._filetree_visible
        self.query_one("#divider-files").display = show and self._filetree_visible
        self.query_one("#terminal-panel").display = show
        # second divider has no id — query by type, skip first
        dividers = list(self.query(Divider))
        if len(dividers) > 1:
            dividers[1].display = show
        self.query_one("#help-hint").display = show

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_toggle_filetree(self) -> None:
        panel = self.query_one("#files-panel")
        divider = self.query_one("#divider-files")
        self._filetree_visible = not self._filetree_visible
        panel.display = self._filetree_visible
        divider.display = self._filetree_visible

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

    def action_copy_selection(self) -> None:
        text = ""
        focused = self.focused
        if isinstance(focused, TextArea):
            text = focused.selected_text
        elif isinstance(focused, RichLog):
            sel = focused.text_selection
            if sel:
                result = focused.get_selection(sel)
                text = result[0] + result[1] if result else ""
        if text:
            self.copy_to_clipboard(text)
            self.notify("Copied to clipboard")

    async def action_open_folder(self) -> None:
        path_str = await self.push_screen_wait(FolderPicker())
        if path_str is None:
            return
        path = Path(path_str.strip())
        if not path.is_dir():
            self.query_one("#terminal", TerminalWidget).write(f"Invalid path: {path_str}")
            return
        tree = self.query_one(DirectoryTree)
        tree.call_after_refresh(setattr, tree, "path", path)
        self._current_file = None
        self._has_changes = False
        self.query_one("#editor", TextArea).load_text("")
        self._update_editor_title()
        self.query_one("#files-panel").border_title = f" Files — {path.name} "

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
