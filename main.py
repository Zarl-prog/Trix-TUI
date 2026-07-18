import sys
import subprocess
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
from textual.events import Click, Key, MouseDown
from textual.widget import Widget
from textual.widgets import DirectoryTree, ListView, ListItem, Static, TextArea
from textual.widgets.text_area import Selection
from textual import work

import json
from themes import THEMES, build_theme_css
from divider_widget import Divider
from search_widget import EditorSearch, GlobalSearch
from screens import ConfirmScreen, FolderPicker, HelpScreen, NewFileScreen, RenameScreen, SplashScreen, ThemePickerScreen
from git_history_screen import GitHistoryScreen


import time as _time

_GIT_BRANCH_CACHE: str = ""
_GIT_BRANCH_CACHE_TIME: float = 0
_GIT_BRANCH_TTL: float = 2.0


def _git_branch() -> str:
    global _GIT_BRANCH_CACHE, _GIT_BRANCH_CACHE_TIME
    now = _time.time()
    if _GIT_BRANCH_CACHE and (now - _GIT_BRANCH_CACHE_TIME) < _GIT_BRANCH_TTL:
        return _GIT_BRANCH_CACHE
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1,
        )
        b = r.stdout.strip()
        _GIT_BRANCH_CACHE = f" 🌿 {b}" if b else ""
        _GIT_BRANCH_CACHE_TIME = now
        return _GIT_BRANCH_CACHE
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
    recent = [r for r in recent if r != path_str]
    recent.insert(0, path_str)
    config["recent_files"] = recent[:15]
    _save_config(config)


from textual.command import Provider, Hit, Hits, DiscoveryHit
from textual.types import IgnoreReturnCallbackType


class TrixCommandProvider(Provider):
    """Provides Trix-specific commands to the command palette."""

    COMMANDS = [
        ("Save File",           "Ctrl+S",       "action_save"),
        ("New File",            "Ctrl+N",       "action_new_file"),
        ("Open Folder",         "Ctrl+O",       "action_open_folder"),
        ("Close File",          "Ctrl+W",       "action_close_file"),
        ("Rename File",         "F2",           "action_rename_file"),
        ("Delete File",         "Del",          "action_delete_file"),
        ("Toggle File Tree",    "Ctrl+B",       "action_toggle_filetree"),
        ("Zen Mode",            "Ctrl+\\",      "action_zen_mode"),
        ("Search in File",      "Ctrl+F",       "action_search"),
        ("Search Across Files", "Ctrl+Shift+F", "action_global_search"),
        ("Git History",         "Ctrl+G",       "action_show_git_history"),
        ("Cycle Theme",         "Ctrl+T",       "action_cycle_theme"),
        ("Theme Picker",        "Ctrl+Shift+T", "action_pick_theme"),
        ("Reload File Tree",    "Ctrl+R",       "action_reload_tree"),
        ("Show Help",           "F1",           "action_show_help"),
        ("Quit",                "Ctrl+Q",       "action_quit_app"),
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


class HorizontalContainer(Horizontal):
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

    _git_status_cache: dict[str, str] = {}
    _git_root: str | None = None

    def on_click(self, event: Click) -> None:
        self.focus()
        # Call the parent's click handler to enable file selection
        if hasattr(super(), 'on_click'):
            super().on_click(event)

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

    def watch_path(self, path: Path) -> None:
        """Reload tree and re-run git status when the tree path changes."""
        self._refresh_git_status()
        self.reload()

def render_label(self, node, base_style, style):
        from rich.text import Text
        from rich.style import Style

        if not node.data:
            return node._label.copy()

        node_label = node._label.copy()
        path = node.data.path

        git_code = self.__class__._git_status_cache.get(str(path), "")

        if self.cursor_node == node:
            # Use app's current accent color for cursor
            try:
                acc = self.app._current_theme_dict.get("accent", "#5ac1fe")
                bg  = self.app._current_theme_dict.get("background", "#0d1016")
                style = Style(bgcolor=acc, color=bg, bold=True)
            except Exception:
                style = Style(bgcolor="#5ac1fe", color="#0d1016", bold=True)
        else:
            if path.is_dir():
                try:
                    txt = self.app._current_theme_dict.get("text", "#bfbdb6")
                    style = Style(color=txt)
                except Exception:
                    style = Style(color="#bfbdb6")
            else:
                # Git status colors from theme
                try:
                    theme = self.app._current_theme_dict
                    if git_code in ("M", "MM", "AM"):
                        style = Style(color=theme.get("warning", "#e6b450"))
                    elif git_code in ("??",):
                        style = Style(color=theme.get("success", "#aad84c"))
                    elif git_code in ("D", "DD", " D"):
                        style = Style(color=theme.get("error", "#ef7177"))
                    elif git_code in ("A", "AM"):
                        style = Style(color=theme.get("success", "#aad84c"))
                    elif git_code in ("R", "C"):
                        style = Style(color=theme.get("accent", "#5ac1fe"))
                    else:
                        style = Style(color=theme.get("text_muted", "#8a8986"))
                except Exception:
                    if git_code in ("M", "MM", "AM"):
                        style = Style(color="#e6b450")
                    elif git_code in ("??",):
                        style = Style(color="#aad84c")
                    elif git_code in ("D", "DD", " D"):
                        style = Style(color="#ef7177")
                    elif git_code in ("A", "AM"):
                        style = Style(color="#aad84c")
                    elif git_code in ("R", "C"):
                        style = Style(color="#5ac1fe")
                    else:
                        style = Style(color="#8a8986")

        node_label.stylize(style)

        # Folder icons
        if path.is_dir():
            icon = "▼ 📂 " if node.is_expanded else "▶ 📁 "
            return Text(icon, style=style) + node_label

        _EXT_ICONS: dict[str, str] = {
            ".py": "🐍 ", ".pyw": "🐍 ", ".pyi": "🐍 ", ".pyx": "🐍 ", ".pxd": "🐍 ",
            ".js": "🟨 ", ".mjs": "🟨 ", ".cjs": "🟨 ",
            ".jsx": "⚛️ ", ".tsx": "⚛️ ",
            ".ts": "🔷 ", ".cts": "🔷 ", ".mts": "🔷 ",
            ".html": "🌐 ", ".htm": "🌐 ", ".xhtml": "🌐 ",
            ".css": "🎨 ", ".scss": "🎨 ", ".sass": "🎨 ", ".less": "🎨 ",
            ".vue": "💚 ", ".svelte": "🔥 ", ".astro": "🚀 ",
            ".json": "📋 ", ".jsonc": "📋 ", ".json5": "📋 ",
            ".yaml": "⚙️ ", ".yml": "⚙️ ",
            ".toml": "⚙️ ", ".ini": "⚙️ ", ".cfg": "⚙️ ", ".conf": "⚙️ ",
            ".env": "🔒 ",
            ".md": "📝 ", ".mdx": "📝 ", ".rst": "📝 ", ".txt": "📄 ",
            ".c": "🔵 ", ".h": "🔵 ",
            ".cpp": "🔵 ", ".cc": "🔵 ", ".cxx": "🔵 ", ".hpp": "🔵 ",
            ".rs": "🦀 ",
            ".go": "🐹 ",
            ".java": "☕ ", ".kt": "☕ ",
            ".cs": "🔵 ",
            ".swift": "🍎 ",
            ".rb": "💎 ",
            ".php": "🐘 ",
            ".scala": "🔴 ",
            ".hs": "🟣 ",
            ".ex": "💜 ", ".exs": "💜 ",
            ".dart": "🎯 ",
            ".zig": "⚡ ",
            ".sh": "🖥️ ", ".bash": "🖥️ ", ".zsh": "🖥️ ", ".fish": "🖥️ ",
            ".ps1": "💙 ",
            ".sql": "🗄️ ",
            ".csv": "📊 ",
            ".png": "🖼️ ", ".jpg": "🖼️ ", ".jpeg": "🖼️ ", ".gif": "🖼️ ",
            ".svg": "🖼️ ", ".ico": "🖼️ ", ".webp": "🖼️ ",
            ".mp4": "🎬 ", ".mov": "🎬 ", ".avi": "🎬 ", ".mkv": "🎬 ",
            ".mp3": "🎵 ", ".wav": "🎵 ", ".flac": "🎵 ",
            ".ttf": "🔤 ", ".otf": "🔤 ", ".woff": "🔤 ", ".woff2": "🔤 ",
            ".zip": "📦 ", ".tar": "📦 ", ".gz": "📦 ",
            ".gitignore": "🙈 ", ".gitattributes": "🙈 ",
            ".lock": "🔒 ",
            ".xml": "📰 ",
            ".lua": "🌙 ",
            ".vim": "📗 ",
            ".r": "📈 ",
            ".proto": "📋 ",
            ".graphql": "📊 ", ".gql": "📊 ",
            ".tf": "🏗️ ", ".tfvars": "🏗️ ",
        }

        _NAME_ICONS: dict[str, str] = {
            "dockerfile":          "🐳 ",
            "docker-compose.yml":  "🐳 ",
            "docker-compose.yaml": "🐳 ",
            "makefile":            "🔧 ",
            "cmakelists.txt":      "🔧 ",
            ".gitignore":          "🙈 ",
            ".gitattributes":      "🙈 ",
            ".env":                "🔒 ",
            ".env.local":          "🔒 ",
            ".env.production":     "🔒 ",
            ".env.development":    "🔒 ",
            ".env.example":        "🔒 ",
            "license":             "⚖️ ",
            "license.md":          "⚖️ ",
            "license.txt":         "⚖️ ",
            "readme.md":           "📖 ",
            "readme.txt":          "📖 ",
            "readme":              "📖 ",
            "changelog.md":        "📋 ",
            "changelog":           "📋 ",
            "contributing.md":     "🤝 ",
            "pyproject.toml":      "🐍 ",
            "setup.py":            "🐍 ",
            "requirements.txt":    "📦 ",
            "package.json":        "📦 ",
            "package-lock.json":   "🔒 ",
            "yarn.lock":           "🔒 ",
            "cargo.toml":          "🦀 ",
            "cargo.lock":          "🦀 ",
            "go.mod":              "🐹 ",
            "go.sum":              "🐹 ",
            "tsconfig.json":       "🔷 ",
            "vite.config.js":      "⚡ ",
            "vite.config.ts":      "⚡ ",
            ".github":             "🐙 ",
            ".vscode":             "💙 ",
        }

        name_lower = path.name.lower()
        ext = path.suffix.lower()

        icon = (
            _NAME_ICONS.get(name_lower)
            or _EXT_ICONS.get(ext)
            or "📄 "
        )

        git_badge = ""
        if git_code == "??":
            git_badge = " [dim]?[/dim]"
        elif git_code in ("M", "MM", "AM"):
            git_badge = " [dim]M[/dim]"
        elif git_code in ("A",):
            git_badge = " [dim]A[/dim]"
        elif git_code in ("D", "DD"):
            git_badge = " [dim]D[/dim]"

        result = Text(icon, style=style) + node_label
        if git_badge:
            try:
                muted = self.app._current_theme_dict.get("text_muted", "#4b4c4e")
                result.append(git_badge, style=Style(color=muted, dim=True))
            except Exception:
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
        try:
            theme = self.app._current_theme_dict
            dash_color  = theme.get("border",         "#3f4043")
            text_color  = theme.get("accent",         "#5ac1fe") if self._is_active else theme.get("text", "#bfbdb6")
        except Exception:
            dash_color = "#3f4043"
            text_color = "#5ac1fe" if self._is_active else "#bfbdb6"

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tabs: list[tuple[Path, bool]] = []
        self._active: int = -1

    def _get_theme_colors(self) -> dict:
        try:
            theme = self.app._current_theme_dict
            return {
                "bg": theme.get("background", "#0d1016"),
                "fg_muted": theme.get("text_muted", "#4b4c4e"),
                "fg": theme.get("text", "#bfbdb6"),
                "surface": theme.get("surface", "#131721"),
                "accent": theme.get("accent", "#5ac1fe"),
                "warning": theme.get("warning", "#e6b450"),
            }
        except Exception:
            return {
                "bg": "#0d1016", "fg_muted": "#4b4c4e", "fg": "#bfbdb6",
                "surface": "#131721", "accent": "#5ac1fe", "warning": "#e6b450",
            }

    def _rebuild(self) -> None:
        self.remove_children()
        theme_colors = self._get_theme_colors()
        # Apply dynamic styles via inline styles
        for i, (path, unsaved) in enumerate(self._tabs):
            dot = " ●" if unsaved else ""
            label = f" {path.name}{dot}  ✕ "
            classes = "tab-item"
            if i == self._active:
                classes += " --tab-active"
            if unsaved:
                classes += " --tab-unsaved"
            tab = Static(label, classes=classes, id=f"tab-{i}")
            self.mount(tab)

    def _update_tab_styles(self) -> None:
        """Update tab styles based on current theme."""
        theme_colors = self._get_theme_colors()
        # Set styles on the widget directly
        self.styles.background = theme_colors["bg"]
        for child in self.children:
            if isinstance(child, Static):
                if "--tab-active" in child.classes:
                    child.styles.color = theme_colors["fg"]
                    child.styles.background = theme_colors["surface"]
                    child.styles.text_style = "bold"
                elif "--tab-unsaved" in child.classes:
                    child.styles.color = theme_colors["warning"]
                    if "--tab-active" in child.classes:
                        child.styles.background = theme_colors["surface"]
                        child.styles.text_style = "bold"
                    else:
                        child.styles.background = theme_colors["bg"]
                else:
                    child.styles.color = theme_colors["fg_muted"]
                    child.styles.background = theme_colors["bg"]

    def set_tabs(self, tabs: list[tuple[Path, bool]], active: int) -> None:
        self._tabs = tabs
        self._active = active
        self._rebuild()
        self._update_tab_styles()


class WelcomePanel(Widget):
    """Welcome screen shown when no file is open, with recent files list."""

    class FileClicked(Message):
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    def _get_theme_colors(self) -> dict:
        try:
            theme = self.app._current_theme_dict
            return {
                "bg": theme.get("background", "#0d1016"),
                "accent": theme.get("accent", "#5ac1fe"),
                "fg": theme.get("text", "#bfbdb6"),
                "text_muted": theme.get("text_muted", "#8a8986"),
                "border": theme.get("border", "#3f4043"),
            }
        except Exception:
            return {
                "bg": "#0d1016", "accent": "#5ac1fe", "fg": "#bfbdb6",
                "text_muted": "#8a8986", "border": "#3f4043",
            }

    def compose(self) -> ComposeResult:
        yield Static("T R I X", id="welcome-header")
        yield Static("Your Terminal. Reimagined.", id="welcome-tagline")
        yield Static("── Recent Files ──", id="welcome-recent-label")
        yield ListView(id="welcome-recent-list")
        yield Static("No recent files", id="welcome-empty")
        yield Static(
            "^O Open Folder   ^N New File   ^P Command Palette   F1 Help",
            id="welcome-hint"
        )

    def on_mount(self) -> None:
        self._apply_styles()
        self._recent: list[str] = []
        self.refresh_content(_load_recent_files())

    def _apply_styles(self) -> None:
        theme_colors = self._get_theme_colors()
        self.styles.background = theme_colors["bg"]
        self.styles.align = ("center", "middle")
        self.styles.layout = "vertical"
        self.styles.padding = (2, 4)
        
        # Apply styles to children
        header = self.query_one("#welcome-header")
        header.styles.color = theme_colors["accent"]
        header.styles.text_style = "bold"
        header.styles.text_align = "center"
        header.styles.width = "100%"
        header.styles.margin_bottom = 1

        tagline = self.query_one("#welcome-tagline")
        tagline.styles.color = theme_colors["text_muted"]
        tagline.styles.text_align = "center"
        tagline.styles.width = "100%"
        tagline.styles.margin_bottom = 2

        recent_label = self.query_one("#welcome-recent-label")
        recent_label.styles.color = theme_colors["text_muted"]
        recent_label.styles.text_style = "bold"
        recent_label.styles.width = "100%"
        recent_label.styles.margin_bottom = 1
        recent_label.styles.padding = (0, 2)

        recent_list = self.query_one("#welcome-recent-list")
        recent_list.styles.width = "100%"
        recent_list.styles.height = "auto"
        recent_list.styles.max_height = 16
        recent_list.styles.background = theme_colors["bg"]
        # ListView border is not directly settable via styles

        empty = self.query_one("#welcome-empty")
        empty.styles.color = theme_colors["text_muted"]
        empty.styles.text_align = "center"
        empty.styles.width = "100%"
        empty.styles.margin_top = 1

        hint = self.query_one("#welcome-hint")
        hint.styles.color = theme_colors["text_muted"]
        hint.styles.text_align = "center"
        hint.styles.width = "100%"
        hint.styles.margin_top = 2

    def refresh_content(self, recent_files: list[str]) -> None:
        self._recent = recent_files
        lv = self.query_one("#welcome-recent-list", ListView)
        lv.clear()
        theme_colors = self._get_theme_colors()

        valid = [r for r in recent_files[:8] if Path(r).exists()]
        stale = [r for r in recent_files[:8] if not Path(r).exists()]

        if valid or stale:
            self.query_one("#welcome-empty").display = False
            self.query_one("#welcome-recent-label").display = True
            lv.display = True
            for path_str in valid:
                p = Path(path_str)
                static = Static(
                    f"📄 {p.name}  [dim]{p.parent}[/dim]", markup=True
                )
                static.styles.padding = (0, 2)
                static.styles.background = theme_colors["bg"]
                static.styles.color = theme_colors["fg"]
                lv.append(ListItem(static))
            for path_str in stale:
                p = Path(path_str)
                static = Static(
                    f"✗  [dim]{p.name}  {p.parent}[/dim]", markup=True
                )
                static.styles.padding = (0, 2)
                static.styles.background = theme_colors["bg"]
                static.styles.color = theme_colors["fg"]
                lv.append(ListItem(static))
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

    class FileClicked(Message):
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

class MainScreen(Screen):
    """Main application screen."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static("✦ TRIX", id="hdr-brand")
            yield Static("", id="hdr-folder")
            yield Static("", id="hdr-sep1", classes="hdr-sep")
            yield Static(self.app._current_theme_dict["name"], id="hdr-theme")

        with Horizontal(id="main-area"):
            with LayoutContainer(id="files-panel"):
                yield PanelHeader("Explorer", id="header-files")
                yield GlobalSearch(id="global-search")
                yield ClickableDirectoryTree(".", id="file-tree")
            yield Divider("files-panel", "editor-panel", id="divider-1")
            with Vertical(id="editor-panel"):
                yield PanelHeader("Editor", id="header-editor")
                yield TabStrip(id="tab-strip")
                yield EditorSearch(id="editor-search")
                yield ClickableTextArea(id="editor", show_line_numbers=True)
                yield WelcomePanel(id="editor-welcome-panel")

        with Horizontal(id="bottom-bar"):
            with Horizontal(id="bb-quit", classes="bb-item"):
                yield Static(" ^Q ", classes="kb-key")
                yield Static("Quit ", classes="kb-desc")
            with Horizontal(id="bb-help", classes="bb-item"):
                yield Static(" F1 ", classes="kb-key")
                yield Static("Help ", classes="kb-desc")
            with Horizontal(id="bb-git", classes="bb-item"):
                yield Static(" ^G ", classes="kb-key")
                yield Static("Git ", classes="kb-desc")
            with Horizontal(id="bb-theme", classes="bb-item"):
                yield Static(" ^T ", classes="kb-key")
                yield Static("Theme ", classes="kb-desc")
            with Horizontal(id="bb-files", classes="bb-item"):
                yield Static(" ^B ", classes="kb-key")
                yield Static("Files ", classes="kb-desc")
            with Horizontal(id="bb-open", classes="bb-item"):
                yield Static(" ^O ", classes="kb-key")
                yield Static("Open ", classes="kb-desc")
            with Horizontal(id="bb-save", classes="bb-item"):
                yield Static(" ^S ", classes="kb-key")
                yield Static("Save ", classes="kb-desc")
            with Horizontal(id="bb-search", classes="bb-item"):
                yield Static(" ^F ", classes="kb-key")
                yield Static("Search ", classes="kb-desc")
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
        self.query_one("#editor", TextArea).focus()


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
    #hdr-brand  { width: auto; color: #5ac1fe; text-style: bold; margin-right: 1; }
    #hdr-folder { width: 1fr; color: #4b4c4e; text-align: center; }
    #hdr-sep1   { width: auto; color: #3f4043; margin-right: 1; }
    #hdr-theme  { width: auto; color: #4b4c4e; }

    #main-area {
        height: 1fr;
        layout: horizontal;
    }

    LayoutContainer, Container, #files-panel, #editor-panel {
        border: none;
        background: #0d1016;
        padding: 0;
    }

    #files-panel.--panel-active    { border-left: tall #5ac1fe; }
    #editor-panel.--panel-active   { border-left: tall #5ac1fe; }

    #files-panel    { width: 20%; min-width: 10%; }
    #editor-panel   { width: 2fr; min-width: 20%; }

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

/* ── Editor Panel ── */
    #editor-panel {
        layout: vertical;
        height: 1fr;
    }
    #editor-panel > PanelHeader {
        height: 1;
    }
    #editor-panel > TabStrip {
        height: 1;
    }
    #editor-panel > EditorSearch {
        height: auto;
    }
    #editor-panel > ClickableTextArea {
        height: 1fr;
    }
    #editor-panel > WelcomePanel {
        display: none;
    }
    #editor-panel > WelcomePanel.-visible {
        display: block;
        height: 1fr;
    }

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

    /* ── Bottom Bar ── */
    #bottom-bar {
        height: 1;
        background: #131721;
        layout: horizontal;
        padding: 0 1;
    }
    .bb-item { width: auto; }
    .bb-item:hover { background: #1f4a6e; }
    .kb-key  { width: auto; color: #5ac1fe; text-style: bold; }
    .kb-desc { width: auto; color: #4b4c4e; margin-right: 1; }

    #sb-spacer  { width: 1fr; }
    #sb-unsaved { width: auto; color: #e6b450; margin-right: 1; }
    #sb-lang    { width: auto; color: #4b4c4e; margin-right: 2; }
    #sb-cursor  { width: auto; color: #4b4c4e; margin-right: 2; }
    #sb-branch  { width: auto; color: #aad84c; margin-right: 1; }

    /* ── Divider ── */
    Divider {
        background: #1a1d23;
    }

    /* ── Toast Notifications ── */
    Toast {
        background: #1f2430;
        border-left: tall #5ac1fe;
        color: #bfbdb6;
        padding: 0 1;
    }
    Toast.-information { border-left: tall #5ac1fe; }
    Toast.-warning     { border-left: tall #e6b450; background: #1f1e2a; }
    Toast.-error       { border-left: tall #ef7177; background: #2a1f20; }
    Toast .toast--title        { color: #5ac1fe; text-style: bold; }
    Toast.-warning .toast--title { color: #e6b450; }
    Toast.-error   .toast--title { color: #ef7177; }
    ToastRack { align: right bottom; padding: 1 2; }

    /* ── Tab Strip ── */
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
    .tab-item.--tab-unsaved  { color: #e6b450; }
    .tab-item.--tab-active.--tab-unsaved {
        color: #e6b450;
        background: #131721;
        text-style: bold;
    }

    /* ── Welcome Panel (hidden when editor has content) ── */
    #editor-welcome-panel {
        height: 1fr;
    }
    #editor-welcome-panel.-hidden {
        display: none;
    }
    """

    BINDINGS = [
        ("ctrl+q",          "quit_app",         "Quit"),
        ("ctrl+s",          "save",             "Save"),
        ("ctrl+n",          "new_file",         "New File"),
        ("ctrl+w",          "close_file",       "Close File"),
        ("ctrl+o",          "open_folder",      "Open Folder"),
        ("ctrl+r",          "reload_tree",      "Reload Tree"),
        ("ctrl+f",          "search",           "Search in File"),
        ("ctrl+shift+f",    "global_search",    "Global Search"),
        ("ctrl+t",          "cycle_theme",      "Cycle Theme"),
        ("ctrl+shift+t",    "pick_theme",       "Theme Picker"),
        ("ctrl+shift+c",    "copy_selection",   "Copy"),
        ("ctrl+b",          "toggle_filetree",  "Toggle File Tree"),
        ("ctrl+backslash",  "zen_mode",         "Zen Mode"),
        ("ctrl+g",          "show_git_history", "Git History"),
        ("f2",              "rename_file",      "Rename"),
        ("f1",              "show_help",        "Help"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False
        self._open_files: list[Path] = []
        self._open_files_dirty: dict[Path, bool] = {}
        self._open_files_content: dict[Path, str] = {}
        self._active_tab: int = -1
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
                    dark=True,
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
                dark=True,
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

        # Apply dynamic CSS overrides so widget colors reflect the new theme
        try:
            self.stylesheet.add_source(build_theme_css(theme))
            self.refresh_css(animate=False)
        except Exception:
            pass

        # Update header theme name
        if self.screen.__class__.__name__ == "MainScreen":
            try:
                self.screen.query_one("#hdr-theme", Static).update(theme["name"])
            except Exception:
                pass
            # Refresh panel headers to pick up new accent color
            try:
                cast(PanelHeader, self.screen.query_one("#header-files"))._update_display()
                cast(PanelHeader, self.screen.query_one("#header-editor"))._update_display()
            except Exception:
                pass
            # Refresh tree render to pick up git status colors
            try:
                self.screen.query_one(DirectoryTree).refresh()
            except Exception:
                pass
            # Refresh tab strip
            try:
                self._update_tab_strip()
            except Exception:
                pass

    # ── Tab management ───────────────────────────────────────────────────────

    def _open_in_tab(self, path: Path, content: str) -> None:
        _save_recent_file(path)
        if self._current_file and self._current_file in self._open_files:
            try:
                ta = self.screen.query_one("#editor", TextArea)
                self._open_files_content[self._current_file] = ta.text
            except Exception:
                pass
        if path in self._open_files:
            idx = self._open_files.index(path)
        else:
            self._open_files.append(path)
            self._open_files_dirty[path] = False
            self._open_files_content[path] = content
            idx = len(self._open_files) - 1
        self._switch_tab(idx)

    def _switch_tab(self, idx: int) -> None:
        if not self._open_files:
            return
        idx = max(0, min(idx, len(self._open_files) - 1))

        if self._current_file and self._current_file in self._open_files:
            try:
                ta = self.screen.query_one("#editor", TextArea)
                self._open_files_content[self._current_file] = ta.text
            except Exception:
                pass

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
            self.call_later(self._confirm_close_tab, closing)
        else:
            self._close_tab(event.index)

    @work
    async def _confirm_close_tab(self, path: Path) -> None:
        if path not in self._open_files:
            return
        idx = self._open_files.index(path)
        name = path.name
        confirmed = await self.push_screen_wait(ConfirmScreen(f"Close {name} with unsaved changes?"))
        if confirmed:
            self._close_tab(idx)

    # ── Mouse click handling ─────────────────────────────────────────────────

    def on_click(self, event: Click | MouseDown) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return

        widget = event.widget
        ancestors = list(widget.ancestors) if widget else []
        bb_actions = {
            "bb-quit":   "action_quit_app",
            "bb-help":   "action_show_help",
            "bb-git":    "action_show_git_history",
            "bb-theme":  "action_cycle_theme",
            "bb-files":  "action_toggle_filetree",
            "bb-open":   "action_open_folder",
            "bb-save":   "action_save",
            "bb-search": "action_search",
        }
        for w in [widget] + ancestors:
            if w and w.id and w.id in bb_actions:
                self.run_action(bb_actions[w.id])
                return

        if widget:
            if isinstance(widget, DirectoryTree) or any(isinstance(a, DirectoryTree) for a in ancestors):
                self.screen.query_one(DirectoryTree).focus()
                return
            if isinstance(widget, TextArea) or any(isinstance(a, TextArea) for a in ancestors):
                self.screen.query_one("#editor", TextArea).focus()
                return

        x, y = event.screen_x, event.screen_y
        files_panel = self.screen.query_one("#files-panel")
        editor_panel = self.screen.query_one("#editor-panel")

        if files_panel.display and files_panel.region.contains(x, y):
            self.screen.query_one(DirectoryTree).focus()
        elif editor_panel.display and editor_panel.region.contains(x, y):
            self.screen.query_one("#editor", TextArea).focus()

    # ── Key routing ─────────────────────────────────────────────────────────

    def on_key(self, event: Key) -> None:
        focused = self.focused
        key = event.key

        if key == "ctrl+right_square_bracket":
            self._cycle_panels()
            event.prevent_default()
            return

        # Tab navigation with Ctrl+Tab / Ctrl+Shift+Tab
        if key == "ctrl+tab":
            if self._open_files:
                new_idx = (self._active_tab + 1) % len(self._open_files)
                self._switch_tab(new_idx)
            event.prevent_default()
            return

        if key == "ctrl+shift+tab":
            if self._open_files:
                new_idx = (self._active_tab - 1) % len(self._open_files)
                self._switch_tab(new_idx)
            event.prevent_default()
            return

        if key == "delete" and isinstance(focused, DirectoryTree):
            self.call_later(self.action_delete_file)
            event.prevent_default()
            return

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
            self.notify(f"Cannot open {path.name}", severity="error")
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
            ta = self.screen.query_one("#editor", TextArea)
            row, col = ta.cursor_location
            self.screen.query_one("#sb-cursor", Static).update(f"Ln {row + 1}  Col {col + 1}")
            lang = self._lang_label(self._current_file) if self._current_file else ""
            self.screen.query_one("#sb-lang", Static).update(lang)
            unsaved = "● unsaved" if self._has_changes else ""
            self.screen.query_one("#sb-unsaved", Static).update(unsaved)
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

        files_active = focused is tree
        editor_active = focused is editor

        cast(PanelHeader, self.screen.query_one("#header-files")).set_active(files_active)
        cast(PanelHeader, self.screen.query_one("#header-editor")).set_active(editor_active)

        self.screen.query_one("#files-panel").set_class(files_active, "--panel-active")
        self.screen.query_one("#editor-panel").set_class(editor_active, "--panel-active")

    def _refresh_ui(self) -> None:
        self._update_tab_strip()
        self._refresh_status_bar()
        if self.screen.__class__.__name__ != "MainScreen":
            return

        # Phase 1: toggle display states (must always succeed independently)
        try:
            welcome = self.screen.query_one("#editor-welcome-panel", WelcomePanel)
            editor  = self.screen.query_one("#editor", TextArea)
            tab_strip = self.screen.query_one("#tab-strip", TabStrip)
            has_files = len(self._open_files) > 0
            welcome.set_class(has_files, "-visible")
            editor.display    = has_files
            tab_strip.display = has_files
        except Exception:
            pass

        # Phase 2: update header labels (may fail without breaking display)
        try:
            tree = self.screen.query_one(DirectoryTree)
            cast(PanelHeader, self.screen.query_one("#header-files")).set_title(f"Explorer — {tree.path.name}")
            self.screen.query_one("#hdr-folder", Static).update(str(tree.path))
        except Exception:
            pass

        # Phase 3: update editor header title
        try:
            if self._current_file is None:
                cast(PanelHeader, self.screen.query_one("#header-editor")).set_title("Editor")
                self.screen.query_one("#editor-welcome-panel", WelcomePanel).refresh_content(_load_recent_files())
            else:
                unsaved = " ●" if self._has_changes else ""
                name = self._current_file.name
                cast(PanelHeader, self.screen.query_one("#header-editor")).set_title(
                    f"Editor — {name}{unsaved}"
                )
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_search(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        if self._current_file is None:
            self.notify("Open a file first", severity="warning")
            return
        self.screen.query_one("#editor-search", EditorSearch).open()

    def action_global_search(self) -> None:
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
        self.screen.query_one("#bottom-bar").display = show
        self.screen.query_one("#header").display = show
        self.screen.query_one("#editor-panel").styles.width = "1fr" if show else "100%"
        if not show:
            self.notify("Zen Mode — Press Ctrl+\\ to exit", timeout=2)

    def action_toggle_filetree(self) -> None:
        self._filetree_visible = not self._filetree_visible
        if not self._zen_mode:
            self.screen.query_one("#files-panel").display = self._filetree_visible
            self.screen.query_one("#divider-1").display = self._filetree_visible

    def action_save(self) -> None:
        if self._current_file is None:
            self.notify("No file open", severity="warning")
            return
        try:
            self._current_file.write_text(
                self.screen.query_one("#editor", TextArea).text, encoding="utf-8"
            )
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")
            return
        self._has_changes = False
        if self._current_file in self._open_files_dirty:
            self._open_files_dirty[self._current_file] = False
        try:
            self.screen.query_one(DirectoryTree)._refresh_git_status()
            self.screen.query_one(DirectoryTree).refresh()
        except Exception:
            pass
        self._refresh_ui()
        self.notify(f"Saved {self._current_file.name}", timeout=1)

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        t = self._themes[self._theme_index]
        self.apply_theme(t)
        self.notify(f"Theme: {t['name']}", timeout=1)

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
        if text:
            self.copy_to_clipboard(text)
            self.notify("Copied to clipboard", timeout=1)

    @work
    async def action_open_folder(self) -> None:
        path_str = await self.push_screen_wait(FolderPicker())
        if not path_str:
            return
        cleaned = Path(path_str.strip()).expanduser().resolve()
        if not cleaned.is_dir():
            self.notify(f"Invalid path: {cleaned}", severity="error")
            return
        self._open_files.clear()
        self._open_files_dirty.clear()
        self._open_files_content.clear()
        self._active_tab = -1
        self._current_file = None
        self._has_changes = False
        tree = self.screen.query_one(DirectoryTree)
        tree.path = cleaned
        self.screen.query_one("#editor", TextArea).load_text("")
        self.screen.query_one("#hdr-folder", Static).update(cleaned.name)
        self._refresh_ui()
        self.notify(f"Opened: {cleaned.name}", timeout=2)

    async def action_reload_tree(self) -> None:
        await self.screen.query_one(DirectoryTree).reload()
        self.notify("File tree reloaded", timeout=1)

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
        self._open_in_tab(new_path, "")
        self.notify(f"Created: {new_path.name}", timeout=2)

    def action_close_file(self) -> None:
        if self._active_tab >= 0 and self._active_tab < len(self._open_files):
            closing = self._open_files[self._active_tab]
            if self._open_files_dirty.get(closing) or self._has_changes:
                self.call_later(self._confirm_close_tab, closing)
            else:
                self._close_tab(self._active_tab)
        else:
            self.screen.query_one("#editor", TextArea).load_text("")
            self._current_file = None
            self._has_changes = False
            self._refresh_ui()

    def _get_target_path(self) -> "Path | None":
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
        if target in self._open_files:
            idx = self._open_files.index(target)
            self._open_files[idx] = new_path
            if target in self._open_files_dirty:
                self._open_files_dirty[new_path] = self._open_files_dirty.pop(target)
            if target in self._open_files_content:
                self._open_files_content[new_path] = self._open_files_content.pop(target)
        if self._current_file == target:
            self._current_file = new_path
        self._has_changes = False
        await self.screen.query_one(DirectoryTree).reload()
        self._refresh_ui()
        self.notify(f"Renamed to {new_path.name}", timeout=2)

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
        if target in self._open_files:
            idx = self._open_files.index(target)
            self._close_tab(idx)
        elif self._current_file == target:
            self.screen.query_one("#editor", TextArea).load_text("")
            self._current_file = None
            self._has_changes = False
            self._refresh_ui()
        await self.screen.query_one(DirectoryTree).reload()
        self.notify(f"Deleted {target.name}", timeout=2)

    @work
    async def action_quit_app(self) -> None:
        dirty_files = [p for p, dirty in self._open_files_dirty.items() if dirty]
        if self._has_changes and self._current_file and self._current_file not in dirty_files:
            dirty_files.append(self._current_file)
        if dirty_files:
            confirmed = await self.push_screen_wait(
                ConfirmScreen(f"Unsaved changes in {len(dirty_files)} file(s). Quit anyway?")
            )
            if not confirmed:
                return
        self.exit()

    # ── Private helpers ─────────────────────────────────────────────────────

    def _cycle_panels(self) -> None:
        if self.screen.__class__.__name__ != "MainScreen":
            return
        focused = self.focused
        editor = self.screen.query_one("#editor", TextArea)
        file_tree = self.screen.query_one(DirectoryTree)

        if focused is file_tree:
            editor.focus()
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

    _LANG_MAP: dict[str, str] = {
        ".py": "python",     ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript", ".json": "json",
        ".html": "html",     ".htm": "html",       ".css": "css",
        ".md": "markdown",   ".yaml": "yaml",      ".yml": "yaml",
        ".toml": "toml",     ".sql": "sql",        ".rs": "rust",
        ".go": "go",         ".c": "c",            ".cpp": "cpp",
        ".h": "c",           ".hpp": "cpp",        ".java": "java",
        ".sh": "bash",       ".bash": "bash",      ".rb": "ruby",
        ".php": "php",       ".xml": "xml",        ".svg": "xml",
        ".lua": "lua",
    }

    _LABEL_MAP: dict[str, str] = {
        ".py": "Python",   ".js": "JavaScript", ".jsx": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript", ".json": "JSON",
        ".html": "HTML",   ".htm": "HTML",      ".css": "CSS",
        ".md": "Markdown", ".yaml": "YAML",     ".yml": "YAML",
        ".toml": "TOML",   ".sql": "SQL",       ".rs": "Rust",
        ".go": "Go",       ".c": "C",           ".cpp": "C++",
        ".h": "C",         ".hpp": "C++",       ".java": "Java",
        ".sh": "Bash",     ".bash": "Bash",     ".rb": "Ruby",
        ".php": "PHP",     ".xml": "XML",       ".lua": "Lua",
    }

    def _lang_label(self, path: Path) -> str:
        return self._LABEL_MAP.get(path.suffix.lower(), path.suffix.upper().lstrip(".") or "Text")

    def _detect_language(self, path: Path) -> str | None:
        return self._LANG_MAP.get(path.suffix.lower())


def run():
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_stdin = kernel32.GetStdHandle(-10)
            if h_stdin != -1:
                mode = ctypes.c_uint()
                if kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode)):
                    new_mode = (mode.value & ~0x0040) | 0x0080
                    kernel32.SetConsoleMode(h_stdin, new_mode)
        except Exception:
            pass
    TrixApp().run()


if __name__ == "__main__":
    run()
