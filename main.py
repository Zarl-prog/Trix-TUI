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
        
        # Harlequin style: Folders #bfbdb6, Files #8a8986
        # Selected background #5ac1fe, dark text
        if self.cursor_node == node:
            style = style.update(bgcolor="#5ac1fe", color="#0d1016", bold=True)
        else:
            if node.data and node.data.path.is_dir():
                style = style.update(color="#bfbdb6")
            else:
                style = style.update(color="#8a8986")
        
        node_label.stylize(style)
        if not node.data:
            return node_label
        path = node.data.path
        
        # Harlequin connectors: ▶ (collapsed), ▼ (expanded)
        # Files indented with ─ prefix
        if path.is_dir():
            icon = "▼ " if node.expanded else "▶ "
        else:
            icon = "─ "
            
        return Text(icon, style=style) + node_label


class PanelHeader(Static):
    """Harlequin-style panel header: ── Title ──────────────────"""
    
    def __init__(self, title: str, id: str = None, classes: str = None):
        super().__init__("", id=id, classes=classes)
        self._title = title
        self._is_active = False

    def set_active(self, active: bool) -> None:
        self._is_active = active
        self._update_display()

    def set_title(self, title: str) -> None:
        self._title = title
        self._update_display()

    def on_mount(self) -> None:
        self._update_display()

    def on_resize(self) -> None:
        self._update_display()

    def _update_display(self) -> None:
        width = self.size.width
        if width < 5:
            self.update("─" * width)
            return
            
        label = f" {self._title} "
        dash_color = "#3f4043"
        text_color = "#5ac1fe" if self._is_active else "#bfbdb6"
        
        # Construct the string: ── Label ──────────────────
        left_dashes = 2
        right_dashes = max(0, width - left_dashes - len(label))
        
        from rich.text import Text
        res = Text()
        res.append("─" * left_dashes, style=dash_color)
        res.append(label, style=text_color)
        res.append("─" * right_dashes, style=dash_color)
        self.update(res)


class MainScreen(Screen):
    """Main application screen that routes its click events to the app click handler."""

    def compose(self) -> ComposeResult:
        with LayoutHorizontal(id="header"):
            yield Static("TRIX", id="hdr-brand")
            yield Static("", id="hdr-folder")
            yield Static(self.app._current_theme_dict["name"], id="hdr-theme")
            
        with LayoutHorizontal(id="main-area"):
            with LayoutContainer(id="files-panel"):
                yield PanelHeader("Files", id="header-files")
                yield ClickableDirectoryTree(".", id="file-tree")
            yield Divider("files-panel", "editor-panel", id="divider-1")
            with LayoutContainer(id="editor-panel"):
                yield PanelHeader("Editor", id="header-editor")
                yield ClickableTextArea(id="editor", show_line_numbers=True)
                yield Static(
                    "Welcome to TRIX\n\nOpen a file from the Files panel\nor press Ctrl+O to open a folder",
                    id="editor-welcome"
                )
            yield Divider("editor-panel", "terminal-panel", id="divider-2")
            with LayoutContainer(id="terminal-panel"):
                yield PanelHeader("Terminal", id="header-terminal")
                yield TerminalWidget(id="terminal")
                
        with Horizontal(id="bottom-bar"):
            # ^q Quit   f1 Help   ^g Git   ^t Theme   ^b Files   ^o Open
            yield Static(" ^q ", classes="kb-key")
            yield Static("Quit  ", classes="kb-desc")
            yield Static(" f1 ", classes="kb-key")
            yield Static("Help  ", classes="kb-desc")
            yield Static(" ^g ", classes="kb-key")
            yield Static("Git  ", classes="kb-desc")
            yield Static(" ^t ", classes="kb-key")
            yield Static("Theme  ", classes="kb-desc")
            yield Static(" ^b ", classes="kb-key")
            yield Static("Files  ", classes="kb-desc")
            yield Static(" ^o ", classes="kb-key")
            yield Static("Open  ", classes="kb-desc")

    def on_click(self, event: Click) -> None:
        self.app.on_click(event)

    def on_mouse_down(self, event: MouseDown) -> None:
        self.app.on_click(event)

    def on_mount(self) -> None:
        self.app._refresh_ui()
        # Focus the terminal input so all three panels are immediately usable
        self.query_one("#term-input", Input).focus()


class TrixApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #0d1016;
    }

    /* ── Header ── */
    #header {
        height: 1;
        background: #0d1016;
        layout: horizontal;
        padding: 0 1;
    }
    #hdr-brand  { width: auto; color: #5ac1fe; text-style: bold; }
    #hdr-folder { width: 1fr; color: #4b4c4e; text-align: center; }
    #hdr-theme  { width: auto; color: #4b4c4e; }

    #main-area {
        height: 1fr;
        layout: horizontal;
    }

    LayoutContainer, Container, #files-panel, #editor-panel, #terminal-panel {
        border: none;
        background: #0d1016;
        padding: 0;
    }

    #files-panel    { width: 20%; min-width: 10%; }
    #editor-panel   { width: 2fr; min-width: 20%; }
    #terminal-panel { width: 2fr; min-width: 20%; }

    PanelHeader {
        height: 1;
        width: 100%;
        background: transparent;
    }

    /* ── File Tree ── */
    DirectoryTree { 
        height: 1fr; 
        background: #0d1016; 
        scrollbar-size: 1 1;
        scrollbar-color: #5ac1fe;
        scrollbar-background: #0d1016;
    }
    DirectoryTree > .tree--cursor    { background: #5ac1fe; color: #0d1016; text-style: bold; }
    DirectoryTree > .tree--highlight { background: #5ac1fe; color: #0d1016; }
    DirectoryTree > .tree--guides    { color: #3f4043; }
    DirectoryTree:hover > .tree--cursor { background: #5ac1fe; color: #0d1016; }

    /* ── Editor ── */
    TextArea { 
        height: 1fr; 
        background: #0d1016; 
        color: #bfbdb6; 
        scrollbar-size: 1 1;
        scrollbar-color: #5ac1fe;
        scrollbar-background: #0d1016;
    }
    TextArea .text-area--gutter        { background: #0d1016; color: #3f4043; }
    TextArea .text-area--gutter-active { background: #0d1016; color: #5ac1fe; text-style: bold; }
    TextArea .text-area--cursor        { background: #5ac1fe; }
    TextArea .text-area--cursor-line   { background: #131721; }
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

    /* ── Terminal ── */
    TerminalWidget { height: 1fr; layout: vertical; }
    #term-output   { 
        height: 1fr; 
        background: #0d1016; 
        color: #8a8986; 
        scrollbar-size: 1 1;
        scrollbar-color: #5ac1fe;
        scrollbar-background: #0d1016;
    }
    #term-output:focus { border: none; }
    #term-output .rich-log--highlight { background: #1f4a6e; }
    #term-input {
        height: 1;
        dock: bottom;
        background: #131721;
        color: #bfbdb6;
        border: none;
        padding: 0 1;
    }
    #term-input:focus {
        background: #131721;
    }

    Input { background: #131721; color: #bfbdb6; border: none; }
    Input:focus { border: none; }

    /* ── Bottom Bar ── */
    #bottom-bar {
        height: 1;
        background: #131721;
        layout: horizontal;
        padding: 0 1;
    }
    .kb-key  { width: auto; color: #5ac1fe; text-style: bold; }
    .kb-desc { width: auto; color: #8a8986; margin-right: 1; }

    /* ── Divider ── */
    Divider {
        background: #1a1d23;
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
            # Harlequin style: cursor location removed from status bar, moved to future line?
            # For now, keep it hidden or invisible
        except Exception:
            pass

    def on_descendant_focus(self, event) -> None:
        self._update_headers()

    def on_descendant_blur(self, event) -> None:
        self._update_headers()

    def _update_headers(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        focused = self.focused
        
        tree = self.screen.query_one(DirectoryTree)
        editor = self.screen.query_one("#editor", TextArea)
        term_output = self.screen.query_one("#term-output", RichLog)
        term_input = self.screen.query_one("#term-input", Input)

        self.screen.query_one("#header-files", PanelHeader).set_active(focused is tree)
        self.screen.query_one("#header-editor", PanelHeader).set_active(focused is editor)
        self.screen.query_one("#header-terminal", PanelHeader).set_active(
            focused is term_output or focused is term_input
        )

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
        self.screen.query_one("#bottom-bar").display = show
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
            tree = self.screen.query_one(DirectoryTree)
            self.screen.query_one("#hdr-folder", Static).update(str(tree.path))
        except Exception:
            pass
            
        if self._current_file is None:
            self.screen.query_one("#header-editor", PanelHeader).set_title("Editor")
            self.screen.query_one("#editor").display = False
            self.screen.query_one("#editor-welcome").display = True
        else:
            unsaved = " ●" if self._has_changes else ""
            name = self._current_file.name
            title = f"Editor — {name}{unsaved}"
            self.screen.query_one("#header-editor", PanelHeader).set_title(title)
            self.screen.query_one("#editor").display = True
            self.screen.query_one("#editor-welcome").display = False

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

if __name__ == "__main__":
    run()
