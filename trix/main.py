from pathlib import Path
import subprocess

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Click
from textual.widgets import DirectoryTree, Input, RichLog, Static, TextArea

from trix.themes import THEMES
from trix.terminal_widget import TerminalWidget
from trix.divider_widget import Divider
from trix.screens import ConfirmScreen, FolderPicker, HelpScreen, NewFileScreen, RenameScreen

# ── File type icons ───────────────────────────────────────────────────────────
_EXT_ICONS = {
    ".py": "🐍", ".js": "📜", ".json": "📋", ".md": "📝",
    ".txt": "📄", ".toml": "⚙️", ".ts": "📜", ".tsx": "📜",
    ".jsx": "📜", ".html": "🌐", ".htm": "🌐", ".css": "🎨",
    ".rs": "🦀", ".go": "🐹", ".c": "⚡", ".cpp": "⚡",
    ".h": "⚡", ".hpp": "⚡", ".java": "☕", ".sh": "🖥️",
    ".yaml": "⚙️", ".yml": "⚙️", ".sql": "🗄️", ".xml": "📋",
    ".svg": "🖼️", ".png": "🖼️", ".jpg": "🖼️",
}


def _file_icon(path: Path) -> str:
    if path.is_dir():
        return "📁 " if path.name != ".git" else "🔧 "
    return _EXT_ICONS.get(path.suffix.lower(), "📄") + " "


def _git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1
        )
        branch = result.stdout.strip()
        return f" {branch}" if branch else ""
    except Exception:
        return ""


class TrixApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #0d1016;
    }

    /* ── Header ── */
    #header {
        height: 1;
        background: #1f2127;
        layout: horizontal;
        padding: 0 1;
    }
    #header-title {
        width: auto;
        color: #5ac1fe;
        text-style: bold;
        content-align: left middle;
    }
    #header-folder {
        width: 1fr;
        color: #bfbdb6;
        content-align: center middle;
    }
    #header-theme {
        width: auto;
        color: #4b4c4e;
        content-align: right middle;
    }

    /* ── Main panels ── */
    #main-area {
        height: 1fr;
        layout: horizontal;
    }

    Container {
        border: solid #3f4043;
        border-title-align: left;
        background: #1f2127;
    }
    Container:focus-within {
        border: solid #5ac1fe;
    }

    #files-panel  { width: 20%; min-width: 10%; }
    #editor-panel { width: 2fr; min-width: 20%; }
    #terminal-panel { width: 2fr; min-width: 20%; }

    /* ── File tree ── */
    DirectoryTree {
        height: 100%;
        background: #1f2127;
    }
    DirectoryTree > .tree--cursor    { background: #3e4043; color: #5ac1fe; }
    DirectoryTree > .tree--highlight { background: #3e4043; }
    DirectoryTree > .tree--guides    { color: #3f4043; }

    /* ── Editor ── */
    TextArea {
        height: 100%;
        background: #0d1016;
        color: #bfbdb6;
    }
    TextArea .text-area--gutter          { background: #0d1016; color: #4b4c4e; }
    TextArea .text-area--gutter-active   { color: #5ac1fe; }
    TextArea .text-area--cursor          { background: #5ac1fe; }
    TextArea .text-area--cursor-line     { background: #1a1e26; }
    TextArea .text-area--selection       { background: #1f4a6e; }

    /* ── Editor placeholder ── */
    #editor-placeholder {
        height: 100%;
        background: #0d1016;
        color: #4b4c4e;
        content-align: center middle;
        text-align: center;
    }

    /* ── Terminal ── */
    TerminalWidget {
        height: 1fr;
        layout: vertical;
    }
    #term-output {
        height: 1fr;
        background: #0d1016;
        color: #bfbdb6;
    }
    #term-output:focus { border: solid #5ac1fe; }
    #term-output .rich-log--highlight { background: #1f4a6e; }
    #term-input {
        height: 3;
        dock: bottom;
        background: #1f2127;
        color: #bfbdb6;
        border-left: solid #5ac1fe;
        border-top: solid #3f4043;
        border-right: solid #3f4043;
        border-bottom: solid #3f4043;
    }
    #term-input:focus {
        border-left: solid #5ac1fe;
        border-top: solid #5ac1fe;
        border-right: solid #5ac1fe;
        border-bottom: solid #5ac1fe;
    }
    Input {
        background: #1f2127;
        color: #bfbdb6;
        border: solid #3f4043;
    }
    Input:focus { border: solid #5ac1fe; }

    /* ── Status bar ── */
    #statusbar {
        height: 1;
        background: #161a1f;
        layout: horizontal;
        padding: 0 1;
    }
    #status-brand  { width: auto; color: #5ac1fe; text-style: bold; content-align: left middle; }
    #status-file   { width: auto; color: #bfbdb6; content-align: left middle; padding: 0 2; }
    #status-cursor { width: 1fr; color: #8a8986; content-align: center middle; }
    #status-git    { width: auto; color: #8a8986; content-align: right middle; padding: 0 2; }
    #status-lang   { width: auto; color: #bfbdb6; content-align: right middle; padding: 0 1; }
    #status-help   { width: auto; color: #4b4c4e; content-align: right middle; }
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
        self._root_folder: str = "."

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static("T R I X", id="header-title")
            yield Static(".", id="header-folder")
            yield Static(THEMES[0]["name"], id="header-theme")
        with Horizontal(id="main-area"):
            with Container(id="files-panel"):
                yield DirectoryTree(".")
            yield Divider("files-panel", "editor-panel", id="divider-files")
            with Container(id="editor-panel"):
                yield Static(
                    "No file open\n\nOpen a file from the Files panel\nor press Ctrl+O to open a folder",
                    id="editor-placeholder"
                )
                yield TextArea(id="editor", show_line_numbers=True)
            yield Divider("editor-panel", "terminal-panel")
            with Container(id="terminal-panel"):
                yield TerminalWidget(id="terminal")
        with Horizontal(id="statusbar"):
            yield Static("TRIX", id="status-brand")
            yield Static("", id="status-file")
            yield Static("Ln 1, Col 1", id="status-cursor")
            yield Static(_git_branch(), id="status-git")
            yield Static("", id="status-lang")
            yield Static("? Help", id="status-help")

    async def on_mount(self) -> None:
        for t in THEMES:
            if t["theme"] is not None:
                self.register_theme(t["theme"])

        self.query_one("#files-panel").border_title = "󰙅 Files"
        self.query_one("#editor-panel").border_title = " Editor"
        self.query_one("#terminal-panel").border_title = " Terminal"

        # Hide editor, show placeholder initially
        self.query_one("#editor", TextArea).display = False

        self._root_folder = Path(".").resolve().name
        self.query_one("#header-folder", Static).update(self._root_folder)
        self.query_one(DirectoryTree).focus()

    def on_click(self, event: Click) -> None:
        editor_panel = self.query_one("#editor-panel")
        files_panel = self.query_one("#files-panel")
        terminal_panel = self.query_one("#terminal-panel")
        inp = self.query_one("#term-input", Input)
        log = self.query_one("#term-output", RichLog)

        if editor_panel.region.contains(event.screen_x, event.screen_y):
            self.query_one("#editor", TextArea).focus()
        elif files_panel.region.contains(event.screen_x, event.screen_y):
            self.query_one(DirectoryTree).focus()
        elif terminal_panel.region.contains(event.screen_x, event.screen_y):
            if log.region.contains(event.screen_x, event.screen_y):
                log.focus()
            else:
                inp.focus()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return
        ta = self.query_one("#editor", TextArea)
        placeholder = self.query_one("#editor-placeholder", Static)
        ta.load_text(content)
        try:
            ta.language = self._detect_language(path)
        except Exception:
            ta.language = None
        self._current_file = path
        self._has_changes = False
        placeholder.display = False
        ta.display = True
        ta.focus()
        self._update_all()

    def on_text_area_changed(self) -> None:
        if self._current_file and not self._has_changes:
            self._has_changes = True
            self._update_all()

    def on_text_area_selection_changed(self) -> None:
        self._update_cursor_status()

    def _update_all(self) -> None:
        self._update_editor_title()
        self._update_status()

    def _update_editor_title(self) -> None:
        panel = self.query_one("#editor-panel")
        if self._current_file is None:
            panel.border_title = " Editor"
        else:
            suffix = " *" if self._has_changes else ""
            panel.border_title = f" Editor — {self._current_file.name}{suffix}"

    def _update_status(self) -> None:
        # File
        if self._current_file:
            suffix = " *" if self._has_changes else ""
            self.query_one("#status-file", Static).update(
                f"{self._current_file.name}{suffix}"
            )
            lang = self._lang_label(self._current_file)
            self.query_one("#status-lang", Static).update(lang)
        else:
            self.query_one("#status-file", Static).update("")
            self.query_one("#status-lang", Static).update("")
        self._update_cursor_status()

    def _update_cursor_status(self) -> None:
        try:
            ta = self.query_one("#editor", TextArea)
            if ta.display:
                row, col = ta.cursor_location
                self.query_one("#status-cursor", Static).update(
                    f"Ln {row + 1}, Col {col + 1}"
                )
        except Exception:
            pass

    def action_zen_mode(self) -> None:
        self._zen_mode = not self._zen_mode
        show = not self._zen_mode
        self.query_one("#files-panel").display = show and self._filetree_visible
        self.query_one("#divider-files").display = show and self._filetree_visible
        self.query_one("#terminal-panel").display = show
        dividers = list(self.query(Divider))
        if len(dividers) > 1:
            dividers[1].display = show
        self.query_one("#statusbar").display = show
        self.query_one("#header").display = show
        editor = self.query_one("#editor-panel")
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
            self.notify("No file open", severity="warning")
            return
        self._current_file.write_text(
            self.query_one("#editor", TextArea).text, encoding="utf-8"
        )
        self._has_changes = False
        self._update_all()

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(THEMES)
        t = THEMES[self._theme_index]
        self.theme = t["slug"]
        self.query_one("#header-theme", Static).update(t["name"])

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
            self.notify(f"Invalid path: {path_str}", severity="error")
            return
        tree = self.query_one(DirectoryTree)
        tree.path = path
        self._current_file = None
        self._has_changes = False
        ta = self.query_one("#editor", TextArea)
        ta.load_text("")
        ta.display = False
        self.query_one("#editor-placeholder", Static).display = True
        self._root_folder = path.name
        self.query_one("#header-folder", Static).update(path.name)
        self.query_one("#files-panel").border_title = f"󰙅 Files — {path.name}"
        self._update_all()

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
            if w is focused:
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
        ta = self.query_one("#editor", TextArea)
        ta.load_text("")
        ta.display = True
        self.query_one("#editor-placeholder", Static).display = False
        self._current_file = new_path
        self._has_changes = False
        self._update_all()

    def action_close_file(self) -> None:
        ta = self.query_one("#editor", TextArea)
        ta.load_text("")
        ta.display = False
        self.query_one("#editor-placeholder", Static).display = True
        self._current_file = None
        self._has_changes = False
        self._update_all()

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
        self._update_all()
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
        ta = self.query_one("#editor", TextArea)
        ta.load_text("")
        ta.display = False
        self.query_one("#editor-placeholder", Static).display = True
        self._current_file = None
        self._has_changes = False
        self._update_all()
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
        self.query_one("#editor", TextArea).action_undo()

    def action_editor_redo(self) -> None:
        self.query_one("#editor", TextArea).action_redo()

    def action_editor_select_all(self) -> None:
        self.query_one("#editor", TextArea).action_select_all()

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

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lang_label(self, path: Path) -> str:
        return {
            ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
            ".ts": "TypeScript", ".tsx": "TypeScript", ".json": "JSON",
            ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".md": "Markdown",
            ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML", ".sql": "SQL",
            ".rs": "Rust", ".go": "Go", ".c": "C", ".cpp": "C++",
            ".h": "C", ".hpp": "C++", ".java": "Java", ".sh": "Bash",
            ".rb": "Ruby", ".php": "PHP", ".xml": "XML",
        }.get(path.suffix.lower(), path.suffix.upper().lstrip(".") or "Text")

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


def run():
    TrixApp().run()
