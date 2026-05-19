import sys
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.events import Click, Key, MouseDown
from textual.widgets import DirectoryTree, Input, RichLog, Static, TextArea
from textual._work_decorator import work

from themes import THEMES
from terminal_widget import TerminalWidget
from divider_widget import Divider
from screens import ConfirmScreen, FolderPicker, HelpScreen, NewFileScreen, RenameScreen


def _git_branch() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1,
        )
        b = r.stdout.strip()
        return f" {b}" if b else ""
    except Exception:
        return ""


class TrixApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #0d1016;
    }

    #header {
        height: 1;
        background: #1a1e26;
        layout: horizontal;
        padding: 0 1;
    }
    #hdr-title  { width: auto; color: #5ac1fe; text-style: bold; }
    #hdr-folder { width: 1fr;  color: #bfbdb6; text-align: center; content-align: center middle; }
    #hdr-theme  { width: auto; color: #4b4c4e; }

    #main-area {
        height: 1fr;
        layout: horizontal;
    }

    Container {
        border: solid #3f4043;
        border-title-align: left;
        background: #1f2127;
    }
    Container:focus-within { border: solid #5ac1fe; }

    #files-panel    { width: 20%; min-width: 10%; }
    #editor-panel   { width: 2fr; min-width: 20%; }
    #terminal-panel { width: 2fr; min-width: 20%; }

    DirectoryTree { height: 100%; background: #1f2127; }
    DirectoryTree > .tree--cursor    { background: #3e4043; color: #5ac1fe; }
    DirectoryTree > .tree--highlight { background: #3e4043; }
    DirectoryTree > .tree--guides    { color: #3f4043; }

    TextArea { height: 100%; background: #0d1016; color: #bfbdb6; }
    TextArea .text-area--gutter        { background: #0d1016; color: #4b4c4e; }
    TextArea .text-area--gutter-active { color: #5ac1fe; }
    TextArea .text-area--cursor        { background: #5ac1fe; }
    TextArea .text-area--cursor-line   { background: #1a1e26; }
    TextArea .text-area--selection     { background: #1f4a6e; }

    TerminalWidget { height: 1fr; layout: vertical; }
    #term-output   { height: 1fr; background: #0d1016; color: #bfbdb6; }
    #term-output:focus { border: solid #5ac1fe; }
    #term-output .rich-log--highlight { background: #1f4a6e; }
    #term-input {
        height: 3;
        dock: bottom;
        background: #1f2127;
        color: #bfbdb6;
        border: solid #3f4043;
    }
    #term-input:focus { border: solid #5ac1fe; }

    Input { background: #1f2127; color: #bfbdb6; border: solid #3f4043; }
    Input:focus { border: solid #5ac1fe; }

    #statusbar {
        height: 1;
        background: #161a1f;
        layout: horizontal;
        padding: 0 1;
    }
    #st-brand  { width: auto; color: #5ac1fe; text-style: bold; }
    #st-file   { width: auto; color: #bfbdb6; padding: 0 2; }
    #st-cursor { width: 1fr;  color: #8a8986; text-align: center; content-align: center middle; }
    #st-git    { width: auto; color: #8a8986; padding: 0 2; }
    #st-lang   { width: auto; color: #bfbdb6; padding: 0 1; }
    #st-help   { width: auto; color: #4b4c4e; }
    """

    BINDINGS = [
        ("ctrl+q",           "quit_app",        "Quit"),
        ("ctrl+s",           "save",            "Save"),
        ("ctrl+n",           "new_file",        "New File"),
        ("ctrl+w",           "close_file",      "Close File"),
        ("ctrl+o",           "open_folder",     "Open Folder"),
        ("ctrl+r",           "reload_tree",     "Reload Tree"),
        ("ctrl+t",           "cycle_theme",     "Cycle Theme"),
        ("ctrl+shift+c",     "copy_selection",  "Copy"),
        ("ctrl+b",           "toggle_filetree", "Toggle File Tree"),
        ("ctrl+backslash",   "zen_mode",        "Zen Mode"),
        ("f2",               "rename_file",     "Rename"),
        ("f1",               "show_help",       "Help"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False
        self._theme_index = 0
        self._filetree_visible = True
        self._zen_mode = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static("T R I X", id="hdr-title")
            yield Static("", id="hdr-folder")
            yield Static(THEMES[0]["name"], id="hdr-theme")
        with Horizontal(id="main-area"):
            with Container(id="files-panel"):
                yield DirectoryTree(".", id="file-tree")
            yield Divider("files-panel", "editor-panel", id="divider-1")
            with Container(id="editor-panel"):
                yield TextArea(id="editor", show_line_numbers=True)
            yield Divider("editor-panel", "terminal-panel", id="divider-2")
            with Container(id="terminal-panel"):
                yield TerminalWidget(id="terminal")
        with Horizontal(id="statusbar"):
            yield Static("TRIX", id="st-brand")
            yield Static("", id="st-file")
            yield Static("Ln 1, Col 1", id="st-cursor")
            yield Static(_git_branch(), id="st-git")
            yield Static("", id="st-lang")
            yield Static("F1 Help", id="st-help")

    async def on_mount(self) -> None:
        for t in THEMES:
            if t["theme"] is not None:
                self.register_theme(t["theme"])
        self.query_one("#files-panel").border_title = " Files"
        self.query_one("#editor-panel").border_title = " Editor"
        self.query_one("#terminal-panel").border_title = " Terminal"
        folder = Path(".").resolve().name
        self.query_one("#hdr-folder", Static).update(folder)
        # Focus the terminal input so all three panels are immediately usable
        self.query_one("#term-input", Input).focus()

    # ── Mouse click handling ─────────────────────────────────────────────────

    def on_click(self, event: Click) -> None:
        """
        Handle mouse clicks to focus the appropriate widget in each panel.
        This enables mouse interaction across all panels.
        """
        x, y = event.screen_x, event.screen_y
        files_panel = self.query_one("#files-panel")
        editor_panel = self.query_one("#editor-panel")
        terminal_panel = self.query_one("#terminal-panel")

        if files_panel.display and files_panel.region.contains(x, y):
            self.query_one(DirectoryTree).focus()
        elif editor_panel.display and editor_panel.region.contains(x, y):
            self.query_one("#editor", TextArea).focus()
        elif terminal_panel.display and terminal_panel.region.contains(x, y):
            # For terminal, check if click is on output or input area
            term_output = self.query_one("#term-output", RichLog)
            term_input = self.query_one("#term-input", Input)
            if term_output.region.contains(x, y):
                term_output.focus()
            else:
                term_input.focus()

    # ── Key routing ─────────────────────────────────────────────────────────

    def on_key(self, event: Key) -> None:
        """Handle keys that must be scoped to a specific focused widget."""
        focused = self.focused
        key = event.key

        # Ctrl+] cycles panels
        if key == "ctrl+right_square_bracket":
            self._cycle_panels()
            event.prevent_default()
            return

        # Delete only when file tree is focused
        if key == "delete" and isinstance(focused, DirectoryTree):
            self.call_later(self.action_delete_file)
            event.prevent_default()
            return

        # Editor-only shortcuts
        if isinstance(focused, TextArea):
            if key == "ctrl+z":
                focused.action_undo()
                event.prevent_default()
            elif key == "ctrl+y":
                focused.action_redo()
                event.prevent_default()
            elif key == "ctrl+a":
                focused.action_select_all()
                event.prevent_default()
            elif key == "ctrl+underscore":
                self._editor_comment()
                event.prevent_default()
            elif key == "ctrl+d":
                self._editor_duplicate()
                event.prevent_default()

    # ── Event handlers ─────────────────────────────────────────────────────

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return
        ta = self.query_one("#editor", TextArea)
        ta.load_text(content)
        try:
            ta.language = self._detect_language(path)
        except Exception:
            ta.language = None
        self._current_file = path
        self._has_changes = False
        ta.focus()
        self._refresh_ui()

    def on_text_area_changed(self) -> None:
        if self._current_file and not self._has_changes:
            self._has_changes = True
            self._refresh_ui()

    def on_text_area_selection_changed(self) -> None:
        try:
            ta = self.query_one("#editor", TextArea)
            row, col = ta.cursor_location
            self.query_one("#st-cursor", Static).update(f"Ln {row+1}, Col {col+1}")
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_zen_mode(self) -> None:
        self._zen_mode = not self._zen_mode
        show = not self._zen_mode
        self.query_one("#files-panel").display = show and self._filetree_visible
        self.query_one("#divider-1").display = show and self._filetree_visible
        self.query_one("#terminal-panel").display = show
        self.query_one("#divider-2").display = show
        self.query_one("#statusbar").display = show
        self.query_one("#header").display = show
        self.query_one("#editor-panel").styles.width = "1fr" if show else "100%"

    def action_toggle_filetree(self) -> None:
        self._filetree_visible = not self._filetree_visible
        self.query_one("#files-panel").display = self._filetree_visible
        self.query_one("#divider-1").display = self._filetree_visible

    def action_save(self) -> None:
        if self._current_file is None:
            self.notify("No file open", severity="warning")
            return
        self._current_file.write_text(
            self.query_one("#editor", TextArea).text, encoding="utf-8"
        )
        self._has_changes = False
        self._refresh_ui()

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(THEMES)
        t = THEMES[self._theme_index]
        self.theme = t["slug"]
        self.query_one("#hdr-theme", Static).update(t["name"])

    def action_copy_selection(self) -> None:
        focused = self.focused
        text = ""
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

    @work
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
        self.query_one("#editor", TextArea).load_text("")
        self.query_one("#hdr-folder", Static).update(path.name)
        self.query_one("#files-panel").border_title = f" Files - {path.name}"
        self._refresh_ui()

    def action_reload_tree(self) -> None:
        self.query_one(DirectoryTree).reload()

    @work
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
        self._refresh_ui()

    def action_close_file(self) -> None:
        self.query_one("#editor", TextArea).load_text("")
        self._current_file = None
        self._has_changes = False
        self._refresh_ui()

    @work
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
        self._refresh_ui()
        await self.query_one(DirectoryTree).reload()

    @work
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
        self._refresh_ui()
        await self.query_one(DirectoryTree).reload()

    @work
    async def action_quit_app(self) -> None:
        if self._has_changes:
            confirmed = await self.push_screen_wait(
                ConfirmScreen("Unsaved changes. Quit anyway?")
            )
            if not confirmed:
                return
        self.exit()

    # ── Private helpers ─────────────────────────────────────────────────────

    def _cycle_panels(self) -> None:
        """Ctrl+] cycles: Files → Editor → Terminal → Files"""
        focused = self.focused
        editor = self.query_one("#editor", TextArea)
        term_input = self.query_one("#term-input", Input)
        file_tree = self.query_one(DirectoryTree)

        if focused is file_tree:
            editor.focus()
        elif focused is editor:
            term_input.focus()
        else:
            file_tree.focus()

    def _editor_comment(self) -> None:
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

    def _editor_duplicate(self) -> None:
        ta = self.query_one("#editor", TextArea)
        row, _ = ta.cursor_location
        line = ta.document.get_line(row)
        ta.replace(line + "\n" + line, (row, 0), (row, len(line)))

    def _refresh_ui(self) -> None:
        if self._current_file is None:
            self.query_one("#editor-panel").border_title = " Editor"
            self.query_one("#st-file", Static).update("")
            self.query_one("#st-lang", Static).update("")
        else:
            suffix = " *" if self._has_changes else ""
            name = self._current_file.name
            self.query_one("#editor-panel").border_title = f" Editor - {name}{suffix}"
            self.query_one("#st-file", Static).update(f"{name}{suffix}")
            self.query_one("#st-lang", Static).update(self._lang_label(self._current_file))

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