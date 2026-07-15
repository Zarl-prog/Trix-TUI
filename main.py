import sys
import subprocess
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import cast

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from textual.app import App, ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.events import Click, Key, MouseDown, MouseMove, MouseUp
from textual.widget import Widget
from textual.widgets import DirectoryTree, Input, ListView, ListItem, RichLog, Static, TextArea
from textual.widgets.text_area import Selection
from textual import work

import json
from themes import THEMES
from terminal_widget import TerminalWidget
from divider_widget import Divider
from search_widget import EditorSearch, GlobalSearch
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


def _load_config() -> dict:
    path = _init_config_dir()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def _save_config(data: dict) -> None:
    path = _init_config_dir()
    try:
        path.write_text(json.dumps(data, indent=4))
    except Exception:
        pass


def _load_theme_persistence() -> str:
    return _load_config().get("theme", "Ayu Dark")


def _save_theme_persistence(theme_name: str) -> None:
    config = _load_config()
    config["theme"] = theme_name
    _save_config(config)


def _load_recent_files() -> list[str]:
    return _load_config().get("recent_files", [])


def _save_recent_file(path: Path) -> None:
    config = _load_config()
    recent = config.get("recent_files", [])
    path_str = str(path)
    # Remove if already present, then prepend
    recent = [r for r in recent if r != path_str]
    recent.insert(0, path_str)
    config["recent_files"] = recent[:15]  # keep last 15
    _save_config(config)


from textual.command import Provider, Hit, Hits, DiscoveryHit
from textual.types import IgnoreReturnCallbackType

class TrixCommandProvider(Provider):
    """Provides Trix-specific commands to the command palette."""

    COMMANDS = [
        ("Save File",           "Ctrl+S",  "action_save"),
        ("New File",            "Ctrl+N",  "action_new_file"),
        ("Open Folder",         "Ctrl+O",  "action_open_folder"),
        ("Close File",          "Ctrl+W",  "action_close_file"),
        ("Rename File",         "F2",      "action_rename_file"),
        ("Delete File",         "Del",     "action_delete_file"),
        ("Toggle File Tree",    "Ctrl+B",  "action_toggle_filetree"),
        ("Zen Mode",            "Ctrl+\\", "action_zen_mode"),
        ("Search in File",      "Ctrl+F",  "action_search"),
        ("Search Across Files", "Ctrl+Shift+F", "action_global_search"),
        ("Git History",         "Ctrl+G",  "action_show_git_history"),
        ("Cycle Theme",         "Ctrl+T",  "action_cycle_theme"),
        ("Theme Picker",        "Ctrl+Shift+T", "action_pick_theme"),
        ("Reload File Tree",    "Ctrl+R",  "action_reload_tree"),
        ("Show Help",           "F1",      "action_show_help"),
        ("Quit",                "Ctrl+Q",  "action_quit_app"),
    ]

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        for name, shortcut, action in self.COMMANDS:
            score = matcher.match(name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(name),
                    partial(self.app.run_action, action),
                    help=shortcut,
                )

    async def discover(self) -> Hits:
        for name, shortcut, action in self.COMMANDS:
            yield DiscoveryHit(
                name,
                partial(self.app.run_action, action),
                help=shortcut,
            )



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

    # Git status cache: maps absolute path string → git status code ('M', '?', 'D', 'A', etc.)
    _git_status_cache: dict[str, str] = {}
    _git_root: str | None = None

    def on_click(self, event: Click) -> None:
        self.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        self.focus()

    def on_mount(self) -> None:
        self._refresh_git_status()

    def _refresh_git_status(self) -> None:
        """Run git status --porcelain and cache results."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "-u"],
                cwd=str(self.path),
                capture_output=True, text=True, timeout=3
            )
            root_result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(self.path),
                capture_output=True, text=True, timeout=2
            )
            self.__class__._git_root = root_result.stdout.strip()
            cache: dict[str, str] = {}
            for line in result.stdout.splitlines():
                if len(line) >= 3:
                    code = line[:2].strip()
                    fpath = line[3:].strip()
                    if self.__class__._git_root:
                        abs_path = str(Path(self.__class__._git_root) / fpath)
                        cache[abs_path] = code
            self.__class__._git_status_cache = cache
        except Exception:
            self.__class__._git_status_cache = {}

    def watch_path(self, path) -> None:
        """Re-run git status when the tree path changes."""
        self._refresh_git_status()

    def render_label(self, node, base_style, style):
        from rich.text import Text
        from rich.style import Style
        
        if not node.data:
            return node._label.copy()
            
        node_label = node._label.copy()
        path = node.data.path

        # Git status color for files
        git_code = self.__class__._git_status_cache.get(str(path), "")

        if self.cursor_node == node:
            style = Style(bgcolor="#5ac1fe", color="#0d1016", bold=True)
        else:
            if path.is_dir():
                style = Style(color="#bfbdb6")
            else:
                # Color by git status
                if git_code in ("M", "MM", "AM"):
                    style = Style(color="#e6b450")   # modified → orange
                elif git_code in ("??",):
                    style = Style(color="#aad84c")   # untracked → green
                elif git_code in ("D", "DD", " D"):
                    style = Style(color="#ef7177")   # deleted → red
                elif git_code in ("A", "AM"):
                    style = Style(color="#aad84c")   # added → green
                elif git_code in ("R", "C"):
                    style = Style(color="#5ac1fe")   # renamed/copied → accent
                else:
                    style = Style(color="#8a8986")   # default

        node_label.stylize(style)

        # Folder icons
        if path.is_dir():
            icon = "▼ 📂 " if node.is_expanded else "▶ 📁 "
            return Text(icon, style=style) + node_label

        # File type icon map
        _EXT_ICONS: dict[str, str] = {
            # Python
            ".py": "🐍 ", ".pyw": "🐍 ", ".pyi": "🐍 ",
            # JavaScript / TypeScript
            ".js": "🟨 ", ".mjs": "🟨 ", ".cjs": "🟨 ",
            ".jsx": "⚛️ ", ".tsx": "⚛️ ",
            ".ts": "🔷 ",
            # Web
            ".html": "🌐 ", ".htm": "🌐 ",
            ".css": "🎨 ", ".scss": "🎨 ", ".sass": "🎨 ", ".less": "🎨 ",
            # Data / Config
            ".json": "📋 ", ".jsonc": "📋 ",
            ".yaml": "⚙️ ", ".yml": "⚙️ ",
            ".toml": "⚙️ ", ".ini": "⚙️ ", ".cfg": "⚙️ ", ".conf": "⚙️ ",
            ".env": "🔒 ",
            # Docs
            ".md": "📝 ", ".mdx": "📝 ", ".rst": "📝 ", ".txt": "📄 ",
            # Systems
            ".c": "⚡ ", ".h": "⚡ ",
            ".cpp": "⚡ ", ".cc": "⚡ ", ".cxx": "⚡ ", ".hpp": "⚡ ",
            ".rs": "🦀 ",
            ".go": "🐹 ",
            ".java": "☕ ", ".kt": "☕ ", ".kts": "☕ ",
            ".cs": "🔵 ",
            ".swift": "🍎 ",
            ".rb": "💎 ",
            ".php": "🐘 ",
            # Shell
            ".sh": "🖥️ ", ".bash": "🖥️ ", ".zsh": "🖥️ ", ".fish": "🖥️ ",
            ".ps1": "🖥️ ",
            # Data
            ".sql": "🗄️ ", ".db": "🗄️ ", ".sqlite": "🗄️ ",
            ".csv": "📊 ", ".tsv": "📊 ",
            # Media
            ".png": "🖼️ ", ".jpg": "🖼️ ", ".jpeg": "🖼️ ", ".gif": "🖼️ ",
            ".svg": "🖼️ ", ".ico": "🖼️ ", ".webp": "🖼️ ",
            ".mp4": "🎬 ", ".mov": "🎬 ", ".avi": "🎬 ",
            ".mp3": "🎵 ", ".wav": "🎵 ", ".ogg": "🎵 ",
            # Archives
            ".zip": "📦 ", ".tar": "📦 ", ".gz": "📦 ", ".bz2": "📦 ",
            ".7z": "📦 ", ".rar": "📦 ",
            # Special files
            ".git": "🌿 ", ".gitignore": "🙈 ", ".gitattributes": "🙈 ",
            ".dockerfile": "🐳 ", ".lock": "🔒 ",
            ".xml": "📰 ",
            ".lua": "🌙 ", ".vim": "📗 ", ".nvim": "📗 ",
            ".r": "📈 ", ".rmd": "📈 ",
        }
        # Special full-name matches
        _NAME_ICONS: dict[str, str] = {
            "dockerfile":         "🐳 ",
            "docker-compose.yml": "🐳 ",
            "docker-compose.yaml":"🐳 ",
            "makefile":           "🔧 ",
            "cmake":              "🔧 ",
            "justfile":           "🔧 ",
            ".gitignore":         "🙈 ",
            ".gitattributes":     "🙈 ",
            ".env":               "🔒 ",
            ".env.local":         "🔒 ",
            "license":            "⚖️ ",
            "licence":            "⚖️ ",
            "readme.md":          "📖 ",
            "readme":             "📖 ",
            "changelog.md":       "📋 ",
            "changelog":          "📋 ",
            "pyproject.toml":     "🐍 ",
            "setup.py":           "🐍 ",
            "setup.cfg":          "🐍 ",
            "requirements.txt":   "📦 ",
            "package.json":       "📦 ",
            "package-lock.json":  "🔒 ",
            "yarn.lock":          "🔒 ",
            "cargo.toml":         "🦀 ",
            "cargo.lock":         "🦀 ",
            "go.mod":             "🐹 ",
            "go.sum":             "🐹 ",
        }

        name_lower = path.name.lower()
        ext = path.suffix.lower()

        icon = (
            _NAME_ICONS.get(name_lower)
            or _EXT_ICONS.get(ext)
            or "📄 "
        )

        # Append git badge
        git_badge = ""
        if git_code == "??" :
            git_badge = " [dim]?[/dim]"
        elif git_code in ("M", "MM", "AM"):
            git_badge = " [dim]M[/dim]"
        elif git_code in ("A",):
            git_badge = " [dim]A[/dim]"
        elif git_code in ("D", "DD"):
            git_badge = " [dim]D[/dim]"

        result = Text(icon, style=style) + node_label
        if git_badge:
            result.append(git_badge, style=Style(color="#4b4c4e", dim=True))
        return result


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


class TabStrip(Widget):
    """Horizontal tab bar showing open files above the editor."""

    DEFAULT_CSS = """
    TabStrip {
        height: 1;
        layout: horizontal;
        background: #0d1016;
        overflow-x: auto;
        scrollbar-size: 0 0;
    }
    .tab-item {
        width: auto;
        height: 1;
        padding: 0 1;
        color: #4b4c4e;
        background: #0d1016;
    }
    .tab-item.--tab-active {
        color: #bfbdb6;
        background: #131721;
        text-style: bold;
    }
    .tab-item.--tab-unsaved {
        color: #e6b450;
    }
    .tab-item.--tab-active.--tab-unsaved {
        color: #e6b450;
        background: #131721;
        text-style: bold;
    }
    """

    class TabClicked(Message):
        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class TabClosed(Message):
        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tabs: list[tuple[Path, bool]] = []  # (path, has_unsaved_changes)
        self._active: int = -1

    def set_tabs(self, tabs: list[tuple[Path, bool]], active: int) -> None:
        self._tabs = tabs
        self._active = active
        self._rebuild()

    def _rebuild(self) -> None:
        self.remove_children()
        for i, (path, unsaved) in enumerate(self._tabs):
            dot = " ●" if unsaved else "  "
            label = f" {path.name}{dot} ✕ "
            classes = "tab-item"
            if i == self._active:
                classes += " --tab-active"
            if unsaved:
                classes += " --tab-unsaved"
            tab = Static(label, classes=classes, id=f"tab-{i}")
            self.mount(tab)

    def on_click(self, event: Click) -> None:
        # Determine which tab was clicked
        x = event.x
        offset = 0
        for i, child in enumerate(self.children):
            w = child.size.width
            if offset <= x < offset + w:
                label = child.renderable if hasattr(child, "renderable") else ""
                raw = str(label)
                # If click is near the ✕ (last 3 chars of label region)
                if x >= offset + w - 3:
                    self.post_message(self.TabClosed(i))
                else:
                    self.post_message(self.TabClicked(i))
                return
            offset += w


class WelcomePanel(Widget):
    """Welcome screen shown when no file is open, with recent files list."""

    class FileClicked(Message):
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    DEFAULT_CSS = """
    WelcomePanel {
        width: 100%;
        height: 100%;
        background: #0d1016;
        align: center middle;
        layout: vertical;
        padding: 2 4;
    }
    #welcome-header {
        width: 100%;
        text-align: center;
        color: #5ac1fe;
        text-style: bold;
        margin-bottom: 1;
    }
    #welcome-tagline {
        width: 100%;
        text-align: center;
        color: #4b4c4e;
        margin-bottom: 2;
    }
    #welcome-recent-label {
        width: 100%;
        color: #8a8986;
        text-style: bold;
        margin-bottom: 1;
        padding: 0 2;
    }
    #welcome-recent-list {
        width: 100%;
        height: auto;
        max-height: 16;
        background: #0d1016;
        border: none;
    }
    #welcome-recent-list > ListItem {
        padding: 0 2;
        background: #0d1016;
        color: #bfbdb6;
    }
    #welcome-recent-list > ListItem:hover {
        background: #1f2430;
        color: #5ac1fe;
    }
    #welcome-recent-list > ListItem.--highlight {
        background: #1f2430;
    }
    #welcome-hint {
        width: 100%;
        text-align: center;
        color: #3f4043;
        margin-top: 2;
    }
    #welcome-empty {
        width: 100%;
        text-align: center;
        color: #4b4c4e;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("T R I X", id="welcome-header")
        yield Static("Your Terminal. Reimagined.", id="welcome-tagline")
        yield Static("Recent Files", id="welcome-recent-label")
        yield ListView(id="welcome-recent-list")
        yield Static("Open a file to get started", id="welcome-empty")
        yield Static("^O Open Folder   ^N New File   F1 Help", id="welcome-hint")

    def on_mount(self) -> None:
        self._recent: list[str] = []
        self.refresh_content(_load_recent_files())

    def refresh_content(self, recent_files: list[str]) -> None:
        self._recent = recent_files
        lv = self.query_one("#welcome-recent-list", ListView)
        lv.clear()

        valid = [r for r in recent_files[:8] if Path(r).exists()]
        stale = [r for r in recent_files[:8] if not Path(r).exists()]

        if valid or stale:
            self.query_one("#welcome-empty").display = False
            self.query_one("#welcome-recent-label").display = True
            lv.display = True
            for path_str in valid:
                p = Path(path_str)
                lv.append(ListItem(Static(f"📄 {p.name}  [dim]{p.parent}[/dim]", markup=True)))
            for path_str in stale:
                p = Path(path_str)
                lv.append(ListItem(Static(f"✗  [dim]{p.name}  {p.parent}[/dim]", markup=True)))
        else:
            self.query_one("#welcome-empty").display = True
            self.query_one("#welcome-recent-label").display = False
            lv.display = False

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is None:
            return
        valid = [r for r in self._recent[:8] if Path(r).exists()]
        if idx < len(valid):
            self.post_message(self.FileClicked(Path(valid[idx])))


class MainScreen(Screen):
    """Main application screen that routes its click events to the app click handler."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static("TRIX", id="hdr-brand")
            yield Static("", id="hdr-folder")
            yield Static(self.app._current_theme_dict["name"], id="hdr-theme")
            
        with Horizontal(id="main-area"):
            with LayoutContainer(id="files-panel"):
                yield PanelHeader("Files", id="header-files")
                yield GlobalSearch(id="global-search")
                yield ClickableDirectoryTree(".", id="file-tree")
            yield Divider("files-panel", "editor-panel", id="divider-1")
            with LayoutContainer(id="editor-panel"):
                yield PanelHeader("Editor", id="header-editor")
                yield TabStrip(id="tab-strip")
                yield EditorSearch(id="editor-search")
                yield ClickableTextArea(id="editor", show_line_numbers=True)
                yield WelcomePanel(id="editor-welcome-panel")
            yield Divider("editor-panel", "terminal-panel", id="divider-2")
            with LayoutContainer(id="terminal-panel"):
                yield PanelHeader("Terminal", id="header-terminal")
                yield TerminalWidget(id="terminal")
                
        with Horizontal(id="bottom-bar"):
            # Left: keybinding hints
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
            yield Static(" ` ", classes="kb-key")
            yield Static("Terminal  ", classes="kb-desc")
            yield Static(" ^o ", classes="kb-key")
            yield Static("Open  ", classes="kb-desc")
            # Right: status info (spacer + status segments)
            yield Static("", id="sb-spacer")
            yield Static("", id="sb-unsaved")
            yield Static("", id="sb-lang")
            yield Static("", id="sb-cursor")
            yield Static("", id="sb-branch")

    def on_click(self, event: Click) -> None:
        self.app.on_click(event)

    def on_mouse_down(self, event: MouseDown) -> None:
        self.app.on_click(event)

    def on_mount(self) -> None:
        self.app._refresh_ui()
        # Hide panels by default — only editor is shown at startup
        self.query_one("#files-panel").display = False
        self.query_one("#divider-1").display = False
        self.query_one("#terminal-panel").display = False
        self.query_one("#divider-2").display = False
        self.query_one("#editor-panel").styles.width = "1fr"
        # Focus the terminal input so all three panels are immediately usable
        self.query_one("#term-input", Input).focus()


class TrixApp(App):
    ENABLE_COMMAND_PALETTE = True
    COMMANDS = App.COMMANDS | {TrixCommandProvider}
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

    #files-panel.--panel-active    { border-left: tall #5ac1fe; }
    #editor-panel.--panel-active   { border-left: tall #5ac1fe; }
    #terminal-panel.--panel-active { border-left: tall #5ac1fe; }

    #files-panel    { width: 20%; min-width: 10%; transition: width 200ms, display 200ms; }
    #editor-panel   { width: 2fr; min-width: 20%; transition: width 200ms; }
    #terminal-panel { width: 2fr; min-width: 20%; transition: width 200ms, display 200ms; }

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
    }
    .welcome-title {
        text-align: center;
        color: #5ac1fe;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }
    .welcome-subtitle {
        text-align: center;
        color: #4b4c4e;
        width: 100%;
        margin-bottom: 2;
    }
    .welcome-section {
        text-align: left;
        color: #8a8986;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    .recent-file-item {
        width: 100%;
        color: #bfbdb6;
        padding: 0 2;
    }
    .recent-file-item:hover {
        background: #1f2430;
        color: #5ac1fe;
    }
    .welcome-hint {
        text-align: center;
        color: #3f4043;
        width: 100%;
        margin-top: 2;
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

    /* Status bar right-side segments */
    #sb-spacer  { width: 1fr; }
    #sb-unsaved { width: auto; color: #e6b450; margin-right: 1; }
    #sb-lang    { width: auto; color: #8a8986; margin-right: 2; }
    #sb-cursor  { width: auto; color: #4b4c4e; margin-right: 2; }
    #sb-branch  { width: auto; color: #aad84c; margin-right: 1; }

    /* ── Divider ── */
    Divider {
        background: #1a1d23;
        transition: display 200ms;
    }

    /* ── Notification Toasts ── */
    Toast {
        background: #1f2430;
        border-left: tall #5ac1fe;
        color: #bfbdb6;
        padding: 0 1;
    }
    Toast.-information {
        border-left: tall #5ac1fe;
    }
    Toast.-warning {
        border-left: tall #e6b450;
        background: #1f1e2a;
    }
    Toast.-error {
        border-left: tall #ef7177;
        background: #2a1f20;
    }
    Toast .toast--title {
        color: #5ac1fe;
        text-style: bold;
    }
    Toast.-warning .toast--title {
        color: #e6b450;
    }
    Toast.-error .toast--title {
        color: #ef7177;
    }
    ToastRack {
        align: right bottom;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("ctrl+q",           "quit_app",        "Quit"),
        ("ctrl+s",           "save",            "Save"),
        ("ctrl+n",           "new_file",        "New File"),
        ("ctrl+w",           "close_file",      "Close File"),
        ("ctrl+o",           "open_folder",     "Open Folder"),
        ("ctrl+r",           "reload_tree",     "Reload Tree"),
        ("ctrl+f",           "search",          "Search in File"),
        ("ctrl+shift+f",     "global_search",   "Global Search"),
        ("ctrl+t",           "cycle_theme",     "Cycle Theme"),
        ("ctrl+shift+t",     "pick_theme",      "Theme Picker"),
        ("ctrl+shift+c",     "copy_selection",  "Copy"),
        ("ctrl+b",           "toggle_filetree", "Toggle File Tree"),
        ("ctrl+backslash",   "zen_mode",        "Zen Mode"),
        ("ctrl+`",           "toggle_terminal", "Toggle Terminal"),
        ("ctrl+g",           "show_git_history","Git History"),
        ("f2",               "rename_file",     "Rename"),
        ("f1",               "show_help",       "Help"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False
        self._open_files: list[Path] = []          # all open tabs
        self._open_files_dirty: dict[Path, bool] = {}  # unsaved state per file
        self._open_files_content: dict[Path, str] = {} # cached content per file
        self._active_tab: int = -1
        self._themes = THEMES
        persisted_theme_name = _load_theme_persistence()
        self._theme_index = 0
        for i, t in enumerate(self._themes):
            if t["name"] == persisted_theme_name:
                self._theme_index = i
                break
        self._current_theme_dict = self._themes[self._theme_index]
        self._filetree_visible = False
        self._terminal_visible = False
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

    # ── Tab management ───────────────────────────────────────────────────────

    def _open_in_tab(self, path: Path, content: str) -> None:
        """Open a file in a tab, switching to it if already open."""
        _save_recent_file(path)
        if path in self._open_files:
            idx = self._open_files.index(path)
        else:
            # Save current editor content before switching
            if self._current_file and self._current_file in self._open_files:
                try:
                    ta = self.screen.query_one("#editor", TextArea)
                    self._open_files_content[self._current_file] = ta.text
                except Exception:
                    pass
            self._open_files.append(path)
            self._open_files_dirty[path] = False
            self._open_files_content[path] = content
            idx = len(self._open_files) - 1
        self._switch_tab(idx)

    def _switch_tab(self, idx: int) -> None:
        """Switch to tab at index, saving current state first."""
        if not self._open_files:
            return
        idx = max(0, min(idx, len(self._open_files) - 1))

        # Save current editor content
        if self._current_file and self._current_file in self._open_files:
            try:
                ta = self.screen.query_one("#editor", TextArea)
                self._open_files_content[self._current_file] = ta.text
            except Exception:
                pass

        # Switch
        self._active_tab = idx
        self._current_file = self._open_files[idx]
        self._has_changes = self._open_files_dirty.get(self._current_file, False)

        ta = self.screen.query_one("#editor", TextArea)
        content = self._open_files_content.get(self._current_file, "")
        ta.load_text(content)
        try:
            ta.language = self._detect_language(self._current_file)
        except Exception:
            ta.language = None
        ta.focus()
        self._refresh_ui()

    def _close_tab(self, idx: int) -> None:
        """Close tab at index, switching to adjacent tab."""
        if not self._open_files or idx >= len(self._open_files):
            return
        closing = self._open_files[idx]
        self._open_files.pop(idx)
        self._open_files_dirty.pop(closing, None)
        self._open_files_content.pop(closing, None)

        if not self._open_files:
            self._active_tab = -1
            self._current_file = None
            self._has_changes = False
            ta = self.screen.query_one("#editor", TextArea)
            ta.load_text("")
            self._refresh_ui()
        else:
            new_idx = min(idx, len(self._open_files) - 1)
            self._active_tab = -1  # force switch
            self._switch_tab(new_idx)

    def _update_tab_strip(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        try:
            strip = self.screen.query_one("#tab-strip", TabStrip)
            tabs = [(p, self._open_files_dirty.get(p, False)) for p in self._open_files]
            strip.set_tabs(tabs, self._active_tab)
            strip.display = len(self._open_files) > 0
        except Exception:
            pass

    def on_tab_strip_tab_clicked(self, event: TabStrip.TabClicked) -> None:
        self._switch_tab(event.index)

    def on_tab_strip_tab_closed(self, event: TabStrip.TabClosed) -> None:
        closing = self._open_files[event.index] if event.index < len(self._open_files) else None
        if closing and self._open_files_dirty.get(closing):
            self.call_later(self._confirm_close_tab, event.index)
        else:
            self._close_tab(event.index)

    @work
    async def _confirm_close_tab(self, idx: int) -> None:
        if idx >= len(self._open_files):
            return
        name = self._open_files[idx].name
        confirmed = await self.push_screen_wait(ConfirmScreen(f"Close {name} with unsaved changes?"))
        if confirmed:
            self._close_tab(idx)

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

    def on_welcome_panel_file_clicked(self, event: WelcomePanel.FileClicked) -> None:
        path = event.path
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            self.notify(f"Cannot open {path.name}", severity="error")
            return
        self._open_in_tab(path, content)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return
        self._open_in_tab(path, content)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if self._current_file and not self._has_changes:
            self._has_changes = True
            if self._current_file in self._open_files_dirty:
                self._open_files_dirty[self._current_file] = True
            self._refresh_ui()
        self._refresh_status_bar()

    def on_text_area_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        self._refresh_status_bar()

    def _refresh_status_bar(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        try:
            # Cursor position
            ta = self.screen.query_one("#editor", TextArea)
            row, col = ta.cursor_location
            self.screen.query_one("#sb-cursor", Static).update(f"Ln {row + 1}, Col {col + 1}")
        except Exception:
            pass
        try:
            # Language
            lang = self._lang_label(self._current_file) if self._current_file else ""
            self.screen.query_one("#sb-lang", Static).update(lang)
        except Exception:
            pass
        try:
            # Unsaved indicator
            unsaved = "● unsaved" if self._has_changes else ""
            self.screen.query_one("#sb-unsaved", Static).update(unsaved)
        except Exception:
            pass
        try:
            # Git branch (cached — only refresh when file changes)
            branch = _git_branch()
            self.screen.query_one("#sb-branch", Static).update(branch)
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

        files_active = focused is tree
        editor_active = focused is editor
        terminal_active = focused is term_output or focused is term_input

        cast(PanelHeader, self.screen.query_one("#header-files")).set_active(files_active)
        cast(PanelHeader, self.screen.query_one("#header-editor")).set_active(editor_active)
        cast(PanelHeader, self.screen.query_one("#header-terminal")).set_active(terminal_active)

        # Panel glow: toggle --panel-active class
        self.screen.query_one("#files-panel").set_class(files_active, "--panel-active")
        self.screen.query_one("#editor-panel").set_class(editor_active, "--panel-active")
        self.screen.query_one("#terminal-panel").set_class(terminal_active, "--panel-active")

    # ── Actions ───────────────────────────────────────────────────────────

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_search(self) -> None:
        """Ctrl+F — inline search inside the editor."""
        if self.screen.__class__.__name__ != "MainScreen":
            return
        if self._current_file is None:
            self.notify("Open a file first", severity="warning")
            return
        self.screen.query_one("#editor-search", EditorSearch).open()

    def action_global_search(self) -> None:
        """Ctrl+Shift+F — search across all files."""
        if self.screen.__class__.__name__ != "MainScreen":
            return
        self.screen.query_one("#global-search", GlobalSearch).open()

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
        self.screen.query_one("#terminal-panel").display = show and self._terminal_visible
        self.screen.query_one("#divider-2").display = show and (self._terminal_visible or self._filetree_visible)
        self.screen.query_one("#bottom-bar").display = show
        self.screen.query_one("#header").display = show
        self.screen.query_one("#editor-panel").styles.width = "1fr" if show else "100%"

    def action_toggle_filetree(self) -> None:
        self._filetree_visible = not self._filetree_visible
        self.screen.query_one("#files-panel").display = self._filetree_visible
        self.screen.query_one("#divider-1").display = self._filetree_visible

    def action_toggle_terminal(self) -> None:
        """Toggle terminal panel visibility."""
        self._terminal_visible = not self._terminal_visible
        self.screen.query_one("#terminal-panel").display = self._terminal_visible
        self.screen.query_one("#divider-2").display = (
            self._terminal_visible or self._filetree_visible
        )

    def action_save(self) -> None:
        if self._current_file is None:
            self.notify("No file open", severity="warning")
            return
        self._current_file.write_text(
            self.screen.query_one("#editor", TextArea).text, encoding="utf-8"
        )
        self._has_changes = False
        if self._current_file in self._open_files_dirty:
            self._open_files_dirty[self._current_file] = False
        # Refresh git status to reflect the save
        try:
            self.screen.query_one(DirectoryTree)._refresh_git_status()
            self.screen.query_one(DirectoryTree).refresh()
        except Exception:
            pass
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

    async def action_reload_tree(self) -> None:
        await self.screen.query_one(DirectoryTree).reload()

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
        if self._active_tab >= 0:
            self.on_tab_strip_tab_closed(TabStrip.TabClosed(self._active_tab))
        else:
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
            cast(PanelHeader, self.screen.query_one("#header-editor")).set_title("Editor")
            self.screen.query_one("#editor").display = False
            try:
                wp = self.screen.query_one("#editor-welcome-panel", WelcomePanel)
                wp.display = True
                wp.refresh_content(_load_recent_files())
            except Exception:
                pass
        else:
            unsaved = " ●" if self._has_changes else ""
            name = self._current_file.name
            title = f"Editor — {name}{unsaved}"
            cast(PanelHeader, self.screen.query_one("#header-editor")).set_title(title)
            self.screen.query_one("#editor").display = True
            try:
                self.screen.query_one("#editor-welcome-panel", WelcomePanel).display = False
            except Exception:
                pass
        self._update_tab_strip()
        self._refresh_status_bar()

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
