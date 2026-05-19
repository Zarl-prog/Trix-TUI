from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.events import Click
from textual.widgets import DirectoryTree, Input, RichLog, Static, TextArea

from themes import THEMES
from terminal_widget import TerminalWidget
from divider_widget import Divider
from screens import ConfirmScreen, FolderPicker, HelpScreen, NewFileScreen, RenameScreen


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
        ("ctrl+q", "quit_app", "Quit"),
        ("q", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
        ("ctrl+n", "new_file", "New File"),
        ("ctrl+w", "close_file", "Close File"),
        ("ctrl+o", "open_folder", "Open Folder"),
        ("ctrl+r", "reload_tree", "Reload Tree"),
        ("ctrl+t", "cycle_theme", "Cycle Theme"),
        ("ctrl+shift+c", "copy_selection", "Copy"),
        ("ctrl+b", "toggle_filetree", "Toggle File Tree"),
        ("ctrl+backslash", "zen_mode", "Zen Mode"),
        ("ctrl+1", "focus_files", "Focus Files"),
        ("ctrl+2", "focus_editor", "Focus Editor"),
        ("ctrl+3", "focus_terminal", "Focus Terminal"),
        ("ctrl+right_square_bracket", "cycle_panels", "Cycle Panels"),
        ("ctrl+z", "editor_undo", "Undo"),
        ("ctrl+y", "editor_redo", "Redo"),
        ("ctrl+a", "editor_select_all", "Select All"),
        ("ctrl+underscore", "editor_comment", "Toggle Comment"),
        ("ctrl+d", "editor_duplicate", "Duplicate Line"),
        ("f2", "rename_file", "Rename"),
        ("delete", "delete_file", "Delete"),
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
        editor = self.query_one("#editor-panel")
        self.query_one("#files-panel").display = show and self._filetree_visible
        self.query_one("#divider-files").display = show and self._filetree_visible
        self.query_one("#terminal-panel").display = show
        dividers = list(self.query(Divider))
        if len(dividers) > 1:
            dividers[1].display = show
        self.query_one("#help-hint").display = show
        editor.styles.width = "1fr" if show else "100%"

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
        if not path_str:
            return
        path = Path(path_str.strip())
        if not path.is_dir():
            self.query_one("#terminal", TerminalWidget).write(f"Invalid path: {path_str}")
            return
        tree = self.query_one(DirectoryTree)
        tree.path = path
        self._current_file = None
        self._has_changes = False
        self.query_one("#editor", TextArea).load_text("")
        self._update_editor_title()
        self.query_one("#files-panel").border_title = f" Files — {path.name} "

    # ── Navigation ────────────────────────────────────────────────────────────

    def action_focus_files(self) -> None:
        self.query_one(DirectoryTree).focus()

    def action_focus_editor(self) -> None:
        self.query_one("#editor", TextArea).focus()

    def action_focus_terminal(self) -> None:
        self.query_one("#term-input", Input).focus()

    def action_cycle_panels(self) -> None:
        panels = [self.query_one(DirectoryTree), self.query_one("#editor", TextArea),
                  self.query_one("#term-input", Input)]
        focused = self.focused
        for i, w in enumerate(panels):
            if w is focused or (hasattr(focused, 'id') and focused is w):
                panels[(i + 1) % len(panels)].focus()
                return
        panels[0].focus()

    # ── File operations ───────────────────────────────────────────────────────

    async def action_new_file(self) -> None:
        name = await self.push_screen_wait(NewFileScreen())
        if not name:
            return
        tree = self.query_one(DirectoryTree)
        new_path = Path(tree.path) / name.strip()
        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.touch()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            return
        await tree.reload()
        self.query_one("#editor", TextArea).load_text("")
        self._current_file = new_path
        self._has_changes = False
        self._update_editor_title()

    def action_close_file(self) -> None:
        self.query_one("#editor", TextArea).load_text("")
        self._current_file = None
        self._has_changes = False
        self._update_editor_title()

    async def action_rename_file(self) -> None:
        if self._current_file is None:
            self.notify("No file open to rename", severity="warning")
            return
        new_name = await self.push_screen_wait(RenameScreen(self._current_file.name))
        if not new_name or new_name.strip() == self._current_file.name:
            return
        new_path = self._current_file.parent / new_name.strip()
        try:
            self._current_file.rename(new_path)
        except Exception as e:
            self.notify(f"Rename failed: {e}", severity="error")
            return
        self._current_file = new_path
        self._has_changes = False
        self._update_editor_title()
        await self.query_one(DirectoryTree).reload()

    async def action_delete_file(self) -> None:
        if self._current_file is None:
            self.notify("No file open to delete", severity="warning")
            return
        confirmed = await self.push_screen_wait(
            ConfirmScreen(f"Delete {self._current_file.name}?")
        )
        if not confirmed:
            return
        try:
            self._current_file.unlink()
        except Exception as e:
            self.notify(f"Delete failed: {e}", severity="error")
            return
        self.query_one("#editor", TextArea).load_text("")
        self._current_file = None
        self._has_changes = False
        self._update_editor_title()
        await self.query_one(DirectoryTree).reload()

    async def action_quit_app(self) -> None:
        if self._has_changes:
            confirmed = await self.push_screen_wait(
                ConfirmScreen("Unsaved changes. Quit anyway?")
            )
            if not confirmed:
                return
        self.exit()

    def action_reload_tree(self) -> None:
        self.query_one(DirectoryTree).reload()

    # ── Editor actions ────────────────────────────────────────────────────────

    def action_editor_undo(self) -> None:
        ta = self.query_one("#editor", TextArea)
        ta.action_undo()

    def action_editor_redo(self) -> None:
        ta = self.query_one("#editor", TextArea)
        ta.action_redo()

    def action_editor_select_all(self) -> None:
        ta = self.query_one("#editor", TextArea)
        ta.action_select_all()

    def action_editor_comment(self) -> None:
        ta = self.query_one("#editor", TextArea)
        row, _ = ta.cursor_location
        line = ta.document.get_line(row)
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("# "):
            new_line = indent + stripped[2:]
        elif stripped.startswith("#"):
            new_line = indent + stripped[1:]
        else:
            new_line = indent + "# " + stripped
        ta.replace(new_line, (row, 0), (row, len(line)))

    def action_editor_duplicate(self) -> None:
        ta = self.query_one("#editor", TextArea)
        row, _ = ta.cursor_location
        line = ta.document.get_line(row)
        ta.replace(line + "\n" + line, (row, 0), (row, len(line)))

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
