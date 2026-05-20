import sys
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal
from textual.events import Click, Key, MouseDown
from textual.widgets import DirectoryTree, Input, RichLog, Static, TextArea
from textual._work_decorator import work

import json
from themes import THEMES
from terminal_widget import TerminalWidget
from divider_widget import Divider
from screens import ConfirmScreen, FolderPicker, HelpScreen, NewFileScreen, RenameScreen, SplashScreen, ThemePickerScreen
from git_history_screen import GitHistoryScreen


def _git_branch() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1,
        )
        b = r.stdout.strip()
        return f" 🌿 {b}" if b else ""
    except Exception:
        return ""


def _init_config_dir() -> Path:
    p = Path.home() / ".trix"
    p.mkdir(parents=True, exist_ok=True)
    return p / "config.json"


def _load_theme_persistence() -> str:
    path = _init_config_dir()
    if path.exists():
        try:
            config = json.loads(path.read_text())
            return config.get("theme", "Ayu Dark")
        except Exception:
            pass
    return "Ayu Dark"


def _save_theme_persistence(theme_name: str) -> None:
    path = _init_config_dir()
    try:
        path.write_text(json.dumps({"theme": theme_name}, indent=4))
    except Exception:
        pass


class LayoutHorizontal(Horizontal):
    """Horizontal container that doesn't steal focus and bubbles mouse events."""
    can_focus = False
    COMPONENT_CLASSES = set()

    def on_mouse_down(self, event: MouseDown) -> None:
        event.bubble = True


class LayoutContainer(Container):
    """Container layout wrapper that doesn't steal focus and bubbles mouse events."""
    can_focus = False
    COMPONENT_CLASSES = set()

    def on_mouse_down(self, event: MouseDown) -> None:
        event.bubble = True


class ClickableTextArea(TextArea):
    """TextArea subclass that explicitly focuses itself when clicked."""

    def on_click(self, event: Click) -> None:
        self.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        self.focus()


class ClickableDirectoryTree(DirectoryTree):
    """DirectoryTree subclass that explicitly focuses itself when clicked."""

    def on_click(self, event: Click) -> None:
        self.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        self.focus()

    def render_label(self, node, base_style, style):
        from rich.text import Text
        node_label = node._label.copy()
        node_label.stylize(style)
        if not node.data:
            return node_label
        path = node.data.path
        if path.is_dir():
            if path.name == ".git":
                icon = "🌿 "
            else:
                icon = "📁 "
        else:
            suffix = path.suffix.lower()
            if suffix == ".py":
                icon = "🐍 "
            elif suffix in (".js", ".jsx"):
                icon = "🟨 "
            elif suffix == ".json":
                icon = "📦 "
            elif suffix == ".md":
                icon = "📝 "
            elif suffix in (".toml", ".yaml", ".yml"):
                icon = "⚙️ "
            elif suffix in (".txt", ".log"):
                icon = "📄 "
            else:
                icon = "📄 "
        return Text(icon) + node_label


class MainScreen(Screen):
    """Main application screen that routes its click events to the app click handler."""

    def compose(self) -> ComposeResult:
        with LayoutHorizontal(id="header"):
            yield Static("T  R  I  X", id="hdr-title")
            yield Static("Trix TUI", id="hdr-title-center")
            yield Static(self.app._current_theme_dict["name"], id="hdr-theme")
        with LayoutHorizontal(id="main-area"):
            with LayoutContainer(id="files-panel"):
                yield ClickableDirectoryTree(".", id="file-tree")
            yield Divider("files-panel", "editor-panel", id="divider-1")
            with LayoutContainer(id="editor-panel"):
                yield ClickableTextArea(id="editor", show_line_numbers=True)
                yield Static(
                    "Welcome to TRIX\n\nOpen a file from the Files panel\nor press Ctrl+O to open a folder",
                    id="editor-welcome"
                )
            yield Divider("editor-panel", "terminal-panel", id="divider-2")
            with LayoutContainer(id="terminal-panel"):
                yield TerminalWidget(id="terminal")
        with LayoutHorizontal(id="statusbar"):
            yield Static("TRIX", id="st-brand")
            yield Static("", id="st-file")
            yield Static("Ln 1, Col 1", id="st-cursor")
            yield Static(_git_branch(), id="st-git")
            yield Static(self.app._current_theme_dict["name"], id="st-theme")
            yield Static("", id="st-lang")
            yield Static("F1 Help", id="st-help")

    def on_click(self, event: Click) -> None:
        self.app.on_click(event)

    def on_mouse_down(self, event: MouseDown) -> None:
        self.app.on_click(event)

    def on_mount(self) -> None:
        self.query_one("#files-panel").border_title = " 📁 Files"
        self.query_one("#editor-panel").border_title = " 📝 Editor"
        self.query_one("#terminal-panel").border_title = " 💻 Terminal"
        self.app._refresh_ui()
        # Focus the terminal input so all three panels are immediately usable
        self.query_one("#term-input", Input).focus()


class TrixApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #0d1016;
    }

    #header {
        height: 2;
        background: #1a1e26;
        layout: horizontal;
        padding: 0 1;
        border-bottom: solid #3f4043;
    }
    #hdr-title  { width: auto; color: #5ac1fe; text-style: bold; }
    #hdr-title-center { width: 1fr; color: #4b4c4e; text-style: bold; text-align: center; }
    #hdr-theme  { width: auto; color: #feb454; text-style: bold; }

    #main-area {
        height: 1fr;
        layout: horizontal;
    }

    LayoutContainer, Container, #files-panel, #editor-panel, #terminal-panel {
        border: none;
        background: #0d1016;
        padding: 0;
    }
    #files-panel {
        background: #1a1d23;
    }
    #editor-panel, #terminal-panel {
        background: #0d1016;
    }

    /* Focus indicator: subtle top accent line */
    LayoutContainer:focus-within, Container:focus-within, #files-panel:focus-within, #editor-panel:focus-within, #terminal-panel:focus-within {
        border-top: solid #5ac1fe;
    }

    #files-panel    { width: 20%; min-width: 10%; }
    #editor-panel   { width: 2fr; min-width: 20%; }
    #terminal-panel { width: 2fr; min-width: 20%; }

    .panel-label {
        height: 1;
        padding: 0 1;
        color: #4b4c4e;
        text-style: bold;
        background: transparent;
    }

    DirectoryTree { height: 1fr; background: #1a1d23; }
    DirectoryTree > .tree--cursor    { background: #1f232c; color: #5ac1fe; text-style: bold; }
    DirectoryTree > .tree--highlight { background: #1f232c; }
    DirectoryTree > .tree--guides    { color: #3f4043; }
    DirectoryTree:hover > .tree--cursor { background: #252830; }

    TextArea { height: 1fr; background: #0d1016; color: #bfbdb6; }

    TextArea .text-area--gutter        { background: #0d1016; color: #4b4c4e; }
    TextArea .text-area--gutter-active { background: #0d1016; color: #5ac1fe; text-style: bold; }
    TextArea .text-area--cursor        { background: #5ac1fe; }
    TextArea .text-area--cursor-line   { background: #1f2127; }
    TextArea .text-area--selection     { background: #1f4a6e; }

    #editor-welcome {
        width: 100%;
        height: 100%;
        content-align: center middle;
        text-align: center;
        color: #4b4c4e;
        background: #0d1016;
        text-style: bold;
    }

    TerminalWidget { height: 1fr; layout: vertical; }
    #term-output   { height: 1fr; background: #0d1016; color: #bfbdb6; }
    #term-output:focus { border: none; }
    #term-output .rich-log--highlight { background: #1f4a6e; }
    #term-input {
        height: 3;
        dock: bottom;
        background: #1f2127;
        color: #bfbdb6;
        border-left: solid #5ac1fe;
        border-top: none;
        border-right: none;
        border-bottom: none;
    }
    #term-input:focus {
        border-left: solid #5ac1fe;
        border-top: none;
        border-right: none;
        border-bottom: none;
    }

    Input { background: #1f2127; color: #bfbdb6; border: none; }
    Input:focus { border: none; }

    #statusbar {
        height: 2;
        background: #161a1f;
        layout: horizontal;
        padding: 0 1;
        border-top: solid #3f4043;
    }
    #st-brand  { width: auto; color: #5ac1fe; text-style: bold; }
    #st-file   { width: auto; color: #bfbdb6; padding: 0 2; }
    #st-cursor { width: 1fr;  color: #4b4c4e; text-align: center; content-align: center middle; }
    #st-git    { width: auto; color: #aad84c; padding: 0 2; }
    #st-theme  { width: auto; color: #feb454; padding: 0 1; }
    #st-lang   { width: auto; color: #5ac1fe; padding: 0 1; }
    #st-help   { width: auto; color: #4b4c4e; }

    DirectoryTree, TextArea, RichLog {
        scrollbar-size: 1 1;
        scrollbar-color: #5ac1fe;
        scrollbar-background: #3f4043;
    }
    """

    BINDINGS = [
        ("ctrl+q",           "quit_app",        "Quit"),
        ("ctrl+s",           "save",            "Save"),
        ("ctrl+n",           "new_file",        "New File"),
        ("ctrl+w",           "close_file",      "Close File"),
        ("ctrl+o",           "open_folder",     "Open Folder"),
        ("ctrl+r",           "reload_tree",     "Reload Tree"),
        ("ctrl+t",           "cycle_theme",     "Cycle Theme"),
        ("ctrl+shift+t",     "pick_theme",      "Theme Picker"),
        ("ctrl+shift+c",     "copy_selection",  "Copy"),
        ("ctrl+b",           "toggle_filetree", "Toggle File Tree"),
        ("ctrl+backslash",   "zen_mode",        "Zen Mode"),
        ("ctrl+g",           "show_git_history","Git History"),
        ("f2",               "rename_file",     "Rename"),
        ("f1",               "show_help",       "Help"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False
        self._themes = THEMES
        persisted_theme_name = _load_theme_persistence()
        self._theme_index = 0
        for i, t in enumerate(self._themes):
            if t["name"] == persisted_theme_name:
                self._theme_index = i
                break
        self._current_theme_dict = self._themes[self._theme_index]
        self._filetree_visible = True
        self._zen_mode = False

    async def on_mount(self) -> None:
        await self.push_screen(SplashScreen())
        self._register_all_themes()
        self.apply_theme(self._current_theme_dict)

    def _register_all_themes(self) -> None:
        from textual.theme import Theme
        for theme in self._themes:
            slug = theme["name"].lower().replace(" ", "-")
            try:
                t = Theme(
                    name=slug,
                    primary=theme["accent"],
                    secondary=theme["border"],
                    accent=theme["accent_alt"],
                    background=theme["background"],
                    surface=theme["surface"],
                    panel=theme["panel"],
                    foreground=theme["text"],
                    error=theme["error"],
                    success=theme["success"],
                    warning=theme["warning"],
                    dark=True
                )
                self.register_theme(t)
            except Exception:
                pass

    def apply_theme(self, theme: dict) -> None:
        self._current_theme_dict = theme
        slug = theme["name"].lower().replace(" ", "-")
        from textual.theme import Theme
        try:
            t = Theme(
                name=slug,
                primary=theme["accent"],
                secondary=theme["border"],
                accent=theme["accent_alt"],
                background=theme["background"],
                surface=theme["surface"],
                panel=theme["panel"],
                foreground=theme["text"],
                error=theme["error"],
                success=theme["success"],
                warning=theme["warning"],
                dark=True
            )
            self.register_theme(t)
        except Exception:
            pass

        self.theme = slug
        _save_theme_persistence(theme["name"])
        
        for i, tm in enumerate(self._themes):
            if tm["name"] == theme["name"]:
                self._theme_index = i
                break
                
        if self.screen.__class__.__name__ == "MainScreen":
            try:
                self.screen.query_one("#hdr-theme", Static).update(theme["name"])
            except Exception:
                pass
            try:
                self.screen.query_one("#st-theme", Static).update(theme["name"])
            except Exception:
                pass

    # ── Mouse click handling ─────────────────────────────────────────────────

    def on_click(self, event: Click | MouseDown) -> None:
        """
        Handle mouse clicks to focus the appropriate widget in each panel.
        This enables mouse interaction across all panels.
        """
        if self.screen.__class__.__name__ != "MainScreen":
            return
        widget = event.widget
        if widget:
            # 1. Widget hierarchy/ancestor check (100% reliable for direct clicks)
            ancestors = list(widget.ancestors)
            
            # Check Files Panel
            if isinstance(widget, DirectoryTree) or any(isinstance(a, DirectoryTree) for a in ancestors):
                self.screen.query_one(DirectoryTree).focus()
                return
                
            # Check Editor Panel
            if isinstance(widget, TextArea) or any(isinstance(a, TextArea) for a in ancestors):
                self.screen.query_one("#editor", TextArea).focus()
                return
                
            # Check Terminal Panel
            if (
                isinstance(widget, TerminalWidget) 
                or any(isinstance(a, TerminalWidget) for a in ancestors)
                or (widget.id and widget.id in ("term-output", "term-input"))
                or any(a.id and a.id in ("term-output", "term-input") for a in ancestors)
            ):
                term_output = self.screen.query_one("#term-output", RichLog)
                term_input = self.screen.query_one("#term-input", Input)
                if widget == term_output or any(a == term_output for a in ancestors):
                    term_output.focus()
                else:
                    term_input.focus()
                return

        # 2. Coordinate boundary check fallback (for clicks on empty padding, borders, headers)
        x, y = event.screen_x, event.screen_y
        files_panel = self.screen.query_one("#files-panel")
        editor_panel = self.screen.query_one("#editor-panel")
        terminal_panel = self.screen.query_one("#terminal-panel")

        if files_panel.display and files_panel.region.contains(x, y):
            self.screen.query_one(DirectoryTree).focus()
        elif editor_panel.display and editor_panel.region.contains(x, y):
            self.screen.query_one("#editor", TextArea).focus()
        elif terminal_panel.display and terminal_panel.region.contains(x, y):
            # For terminal, check if click is on output or input area
            term_output = self.screen.query_one("#term-output", RichLog)
            term_input = self.screen.query_one("#term-input", Input)
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
        ta = self.screen.query_one("#editor", TextArea)
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
            ta = self.screen.query_one("#editor", TextArea)
            row, col = ta.cursor_location
            self.screen.query_one("#st-cursor", Static).update(f"Ln {row+1}, Col {col+1}")
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_show_git_history(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        tree = self.screen.query_one(DirectoryTree)
        repo_path = str(tree.path)
        self.push_screen(GitHistoryScreen(repo_path))

    def action_zen_mode(self) -> None:
        self._zen_mode = not self._zen_mode
        show = not self._zen_mode
        self.screen.query_one("#files-panel").display = show and self._filetree_visible
        self.screen.query_one("#divider-1").display = show and self._filetree_visible
        self.screen.query_one("#terminal-panel").display = show
        self.screen.query_one("#divider-2").display = show
        self.screen.query_one("#statusbar").display = show
        self.screen.query_one("#header").display = show
        self.screen.query_one("#editor-panel").styles.width = "1fr" if show else "100%"

    def action_toggle_filetree(self) -> None:
        self._filetree_visible = not self._filetree_visible
        self.screen.query_one("#files-panel").display = self._filetree_visible
        self.screen.query_one("#divider-1").display = self._filetree_visible

    def action_save(self) -> None:
        if self._current_file is None:
            self.notify("No file open", severity="warning")
            return
        self._current_file.write_text(
            self.screen.query_one("#editor", TextArea).text, encoding="utf-8"
        )
        self._has_changes = False
        self._refresh_ui()

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        t = self._themes[self._theme_index]
        self.apply_theme(t)

    @work
    async def action_pick_theme(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        theme_picker = ThemePickerScreen(self._themes, self._current_theme_dict)
        chosen_theme = await self.push_screen_wait(theme_picker)
        if chosen_theme:
            self.apply_theme(chosen_theme)

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
        tree = self.screen.query_one(DirectoryTree)
        tree.path = path
        self._current_file = None
        self._has_changes = False
        self.screen.query_one("#editor", TextArea).load_text("")
        self.screen.query_one("#hdr-folder", Static).update(path.name)
        self.screen.query_one("#files-panel").border_title = f" Files - {path.name}"
        self._refresh_ui()

    def action_reload_tree(self) -> None:
        self.screen.query_one(DirectoryTree).reload()

    @work
    async def action_new_file(self) -> None:
        name = await self.push_screen_wait(NewFileScreen())
        if not name:
            return
        tree = self.screen.query_one(DirectoryTree)
        new_path = Path(tree.path) / name.strip()
        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.touch()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            return
        await tree.reload()
        self.screen.query_one("#editor", TextArea).load_text("")
        self._current_file = new_path
        self._has_changes = False
        self._refresh_ui()

    def action_close_file(self) -> None:
        self.screen.query_one("#editor", TextArea).load_text("")
        self._current_file = None
        self._has_changes = False
        self._refresh_ui()

    def _get_target_path(self) -> "Path | None":
        """Return the file to operate on: open file first, then tree selection."""
        if self._current_file is not None:
            return self._current_file
        try:
            tree = self.screen.query_one(DirectoryTree)
            node = tree.cursor_node
            if node and node.data and node.data.path.is_file():
                return node.data.path
        except Exception:
            pass
        return None

    @work
    async def action_rename_file(self) -> None:
        target = self._get_target_path()
        if target is None:
            self.notify("Select a file to rename", severity="warning")
            return
        new_name = await self.push_screen_wait(RenameScreen(target.name))
        if not new_name or new_name.strip() == target.name:
            return
        new_path = target.parent / new_name.strip()
        try:
            target.rename(new_path)
        except Exception as e:
            self.notify(f"Rename failed: {e}", severity="error")
            return
        if self._current_file == target:
            self._current_file = new_path
        self._has_changes = False
        self._refresh_ui()
        await self.screen.query_one(DirectoryTree).reload()

    @work
    async def action_delete_file(self) -> None:
        target = self._get_target_path()
        if target is None:
            self.notify("Select a file to delete", severity="warning")
            return
        confirmed = await self.push_screen_wait(
            ConfirmScreen(f"Delete {target.name}?")
        )
        if not confirmed:
            return
        try:
            target.unlink()
        except Exception as e:
            self.notify(f"Delete failed: {e}", severity="error")
            return
        if self._current_file == target:
            self.screen.query_one("#editor", TextArea).load_text("")
            self._current_file = None
            self._has_changes = False
            self._refresh_ui()
        await self.screen.query_one(DirectoryTree).reload()

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
        if self.screen.__class__.__name__ != "MainScreen":
            return
        focused = self.focused
        editor = self.screen.query_one("#editor", TextArea)
        term_input = self.screen.query_one("#term-input", Input)
        file_tree = self.screen.query_one(DirectoryTree)

        if focused is file_tree:
            editor.focus()
        elif focused is editor:
            term_input.focus()
        else:
            file_tree.focus()

    def _editor_comment(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        ta = self.screen.query_one("#editor", TextArea)
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
        if self.screen.__class__.__name__ != "MainScreen":
            return
        ta = self.screen.query_one("#editor", TextArea)
        row, _ = ta.cursor_location
        line = ta.document.get_line(row)
        ta.replace(line + "\n" + line, (row, 0), (row, len(line)))

    def _refresh_ui(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        try:
            self.screen.query_one("#st-theme", Static).update(self._current_theme_dict["name"])
        except Exception:
            pass
        if self._current_file is None:
            self.screen.query_one("#editor-panel").border_title = " 📝 Editor"
            self.screen.query_one("#editor").display = False
            self.screen.query_one("#editor-welcome").display = True
            self.screen.query_one("#st-file", Static).update("")
            self.screen.query_one("#st-lang", Static).update("")
        else:
            suffix = " *" if self._has_changes else ""
            name = self._current_file.name
            ext = self._current_file.suffix.lower()
            icon = "📄"
            if ext == ".py":
                icon = "🐍"
            elif ext in (".js", ".jsx"):
                icon = "🟨"
            elif ext == ".json":
                icon = "📦"
            elif ext == ".md":
                icon = "📝"
            elif ext in (".toml", ".yaml", ".yml"):
                icon = "⚙️"
            elif ext in (".txt", ".log"):
                icon = "📄"
            self.screen.query_one("#editor-panel").border_title = f" {icon} {name}{suffix}"
            self.screen.query_one("#editor").display = True
            self.screen.query_one("#editor-welcome").display = False
            self.screen.query_one("#st-file", Static).update(f"{name}{suffix}")
            self.screen.query_one("#st-lang", Static).update(self._lang_label(self._current_file))

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
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_stdin = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
            if h_stdin != -1:
                mode = ctypes.c_uint()
                if kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode)):
                    # Clear ENABLE_QUICK_EDIT_MODE (0x0040) and set ENABLE_EXTENDED_FLAGS (0x0080)
                    new_mode = (mode.value & ~0x0040) | 0x0080
                    kernel32.SetConsoleMode(h_stdin, new_mode)
        except Exception:
            pass
    TrixApp().run()