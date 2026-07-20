"""Screens module - all modal/dialog screens for the application."""

from __future__ import annotations  # noqa: F401 - needed for forward refs

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, Static, OptionList

_HELP = """\
  [bold #5ac1fe]── File ─────────────────────────[/bold #5ac1fe]
    [#5ac1fe]Ctrl+N[/#5ac1fe]          New File
    [#5ac1fe]Ctrl+S[/#5ac1fe]          Save File
    [#5ac1fe]Ctrl+W[/#5ac1fe]          Close Tab
    [#5ac1fe]Ctrl+O[/#5ac1fe]          Open Folder
    [#5ac1fe]F2[/#5ac1fe]              Rename File
    [#5ac1fe]Delete[/#5ac1fe]          Delete File

  [bold #5ac1fe]── Navigation ───────────────────[/bold #5ac1fe]
    [#5ac1fe]Ctrl+][/#5ac1fe]          Cycle Panels
    [#5ac1fe]Ctrl+Tab[/#5ac1fe]        Next Tab
    [#5ac1fe]Ctrl+Shift+Tab[/#5ac1fe]  Prev Tab
    [#5ac1fe]Ctrl+B[/#5ac1fe]          Toggle File Tree
    [#5ac1fe]Ctrl+\\[/#5ac1fe]          Zen Mode

  [bold #5ac1fe]── Editor ───────────────────────[/bold #5ac1fe]
    [#5ac1fe]Ctrl+Z[/#5ac1fe]          Undo
    [#5ac1fe]Ctrl+Y[/#5ac1fe]          Redo
    [#5ac1fe]Ctrl+A[/#5ac1fe]          Select All
    [#5ac1fe]Ctrl+_[/#5ac1fe]          Toggle Comment
    [#5ac1fe]Ctrl+D[/#5ac1fe]          Duplicate Line
    [#5ac1fe]Ctrl+Shift+C[/#5ac1fe]    Copy Selection

  [bold #5ac1fe]── Search ───────────────────────[/bold #5ac1fe]
    [#5ac1fe]Ctrl+F[/#5ac1fe]          Search in File
    [#5ac1fe]Ctrl+Shift+F[/#5ac1fe]    Search All Files
    [#5ac1fe]Ctrl+P[/#5ac1fe]          Command Palette

  [bold #5ac1fe]── Git & Theme ──────────────────[/bold #5ac1fe]
    [#5ac1fe]Ctrl+G[/#5ac1fe]          Git Menu
    [#5ac1fe]Ctrl+T[/#5ac1fe]          Cycle Theme
    [#5ac1fe]Ctrl+Shift+T[/#5ac1fe]    Theme Picker
    [#5ac1fe]Ctrl+R[/#5ac1fe]          Reload File Tree
    [#5ac1fe]Ctrl+Q[/#5ac1fe]          Quit\
"""

from themes import register_css_template


def _get_main_screen_class():
    """Lazy import to avoid circular dependency at module load time."""
    from main import MainScreen
    return MainScreen

HELP_SCREEN_CSS = """
HelpScreen {
    align: center middle;
    background: #030508;
}
#help-dialog {
    width: 58;
    height: auto;
    max-height: 90%;
    padding: 0;
    background: #131721;
    border: tall #5ac1fe;
}
#help-titlebar {
    width: 100%;
    height: 3;
    background: #0d1016;
    border-bottom: solid #2e3038;
    padding: 0 2;
    align: left middle;
}
#help-title {
    width: 1fr;
    color: #5ac1fe;
    text-style: bold;
}
#help-title-hint {
    width: auto;
    color: #686868;
}
#help-body {
    width: 100%;
    color: #bfbdb6;
    padding: 1 2;
}
#help-close {
    width: 100%;
    text-align: center;
    color: #686868;
    margin-top: 1;
    padding: 0 2;
}
"""
register_css_template("help_screen", HELP_SCREEN_CSS)


class HelpScreen(Screen):
    BINDINGS = [("escape", "dismiss", "Close"), ("f1", "dismiss", "Close")]
    CSS = HELP_SCREEN_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            with Horizontal(id="help-titlebar"):
                yield Label("⌨  Keyboard Shortcuts", id="help-title")
                yield Label("Esc to close", id="help-title-hint")
            yield Static(_HELP, id="help-body", markup=True)
            yield Label(
                "Press [bold #5ac1fe]Escape[/bold #5ac1fe] or [bold #5ac1fe]F1[/bold #5ac1fe] to close",
                id="help-close",
                markup=True,
            )

    def action_dismiss(self) -> None:
        self.dismiss()


CONFIRM_SCREEN_CSS = """
ConfirmScreen {
    align: center middle;
    background: #030508;
}
#cf-dialog {
    width: 50;
    height: auto;
    padding: 0;
    background: #131721;
    border: tall #ef7177;
}
#cf-titlebar {
    width: 100%;
    height: 3;
    background: #0d1016;
    border-bottom: solid #2e3038;
    padding: 0 2;
    align: left middle;
}
#cf-title { color: #ef7177; text-style: bold; }
#cf-msg { width: 100%; color: #bfbdb6; margin: 1 2; }
#cf-buttons { height: auto; layout: horizontal; margin: 1 2; align-horizontal: center; }
#cf-buttons Button { margin: 0 1; min-height: 3; min-width: 10; }
#cf-yes { background: #ef7177; color: #0d1016; text-style: bold; border: none; }
#cf-no { background: #2e3038; color: #bfbdb6; text-style: bold; border: none; }
"""
register_css_template("confirm_screen", CONFIRM_SCREEN_CSS)


class ConfirmScreen(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = CONFIRM_SCREEN_CSS

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        from textual.widgets import Button
        with Vertical(id="cf-dialog"):
            with Horizontal(id="cf-titlebar"):
                yield Label("⚠  Confirm", id="cf-title")
            yield Label(self._message, id="cf-msg")
            with Horizontal(id="cf-buttons"):
                yield Button("Yes", id="cf-yes", variant="error")
                yield Button("No", id="cf-no", variant="default")

    def on_button_pressed(self, event) -> None:
        self.dismiss(event.button.id == "cf-yes")

    def action_cancel(self) -> None:
        self.dismiss(False)


NEW_FILE_SCREEN_CSS = """
NewFileScreen {
    align: center middle;
    background: #030508;
}
#nf-dialog {
    width: 54;
    height: auto;
    padding: 0;
    background: #131721;
    border: tall #5ac1fe;
}
#nf-titlebar {
    width: 100%;
    height: 3;
    background: #0d1016;
    border-bottom: solid #2e3038;
    padding: 0 2;
    align: left middle;
}
#nf-title { color: #5ac1fe; text-style: bold; }
#nf-hint  { width: 100%; color: #686868; padding: 1 2 0 2; }
#nf-input { width: 100%; margin: 1 2; border: solid #2e3038; background: #0d1016; color: #bfbdb6; padding: 0 1; }
#nf-input:focus { border: solid #5ac1fe; }
"""
register_css_template("new_file_screen", NEW_FILE_SCREEN_CSS)


class NewFileScreen(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = NEW_FILE_SCREEN_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="nf-dialog"):
            with Horizontal(id="nf-titlebar"):
                yield Label("✦  New File", id="nf-title")
            yield Label("Enter a filename (use / for subdirectory):", id="nf-hint")
            yield Input(id="nf-input", placeholder="filename.txt")

    def on_mount(self) -> None:
        self.query_one("#nf-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


RENAME_SCREEN_CSS = """
RenameScreen {
    align: center middle;
    background: #030508;
}
#rn-dialog {
    width: 54;
    height: auto;
    padding: 0;
    background: #131721;
    border: tall #5ac1fe;
}
#rn-titlebar {
    width: 100%;
    height: 3;
    background: #0d1016;
    border-bottom: solid #2e3038;
    padding: 0 2;
    align: left middle;
}
#rn-title { color: #5ac1fe; text-style: bold; }
#rn-hint  { width: 100%; color: #686868; padding: 1 2 0 2; }
#rn-input { width: 100%; margin: 1 2; border: solid #2e3038; background: #0d1016; color: #bfbdb6; padding: 0 1; }
#rn-input:focus { border: solid #5ac1fe; }
"""
register_css_template("rename_screen", RENAME_SCREEN_CSS)


class RenameScreen(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = RENAME_SCREEN_CSS

    def __init__(self, current_name: str, **kwargs):
        super().__init__(**kwargs)
        self._current_name = current_name

    def compose(self) -> ComposeResult:
        with Vertical(id="rn-dialog"):
            with Horizontal(id="rn-titlebar"):
                yield Label(f"✏  Rename: {self._current_name}", id="rn-title")
            yield Label("Enter new name:", id="rn-hint")
            yield Input(id="rn-input", value=self._current_name)

    def on_mount(self) -> None:
        inp = self.query_one("#rn-input", Input)
        inp.focus()
        inp.cursor_position = len(inp.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


FOLDER_PICKER_CSS = """
FolderPicker {
    align: center middle;
    background: #030508;
}
#dialog {
    width: 60;
    height: auto;
    padding: 0;
    background: #131721;
    border: tall #5ac1fe;
}
#fp-titlebar {
    width: 100%;
    height: 3;
    background: #0d1016;
    border-bottom: solid #2e3038;
    padding: 0 2;
    align: left middle;
}
#fp-title { color: #5ac1fe; text-style: bold; }
#fp-hint  { width: 100%; color: #686868; padding: 1 2 0 2; }
#folder-path { width: 100%; margin: 1 2; border: solid #2e3038; background: #0d1016; color: #bfbdb6; padding: 0 1; }
#folder-path:focus { border: solid #5ac1fe; }
"""
register_css_template("folder_picker", FOLDER_PICKER_CSS)


class FolderPicker(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = FOLDER_PICKER_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            with Horizontal(id="fp-titlebar"):
                yield Label("📂  Open Folder", id="fp-title")
            yield Label("Enter folder path (~ supported):", id="fp-hint")
            yield Input(id="folder-path", placeholder="/path/to/folder")

    def on_mount(self) -> None:
        self.query_one("#folder-path", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


PERFECT_SPLASH_CSS = """
SplashScreen {
    align: center middle;
    background: #0d1016;
}
#splash-frame {
    width: 50;
    height: auto;
    border: solid #2e3038;
    background: #131721;
    padding: 1 2;
}
#splash-logo {
    text-align: center;
    text-style: bold;
    margin-bottom: 0;
}
#splash-tagline {
    text-align: center;
    color: #686868;
    text-style: italic;
    margin-bottom: 0;
}
#splash-version {
    text-align: center;
    color: #3f4043;
    margin-bottom: 1;
}
#splash-status {
    text-align: center;
    color: #686868;
}
"""
register_css_template("splash_screen", PERFECT_SPLASH_CSS)


class SplashScreen(Screen):
    """Splash screen with logo that fills as loading progresses."""

    CSS = PERFECT_SPLASH_CSS

    _LOGO = (
        "  ████████╗██████╗ ██╗██╗  ██╗\n"
        "  ╚══██╔══╝██╔══██╗██║╚██╗██╔╝\n"
        "     ██║   ██████╔╝██║ ╚███╔╝ \n"
        "     ██║   ██╔══██╗██║ ██╔██╗ \n"
        "     ██║   ██║  ██║██║██╔╝ ██╗\n"
        "     ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝"
    )
    _LOGO_ROWS = _LOGO.split("\n")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress = 0.0
        self.duration = 2.2
        self.steps = 44
        self.step_time = self.duration / self.steps
        self.timer = None
        self.version = self._get_version()

    def _get_version(self) -> str:
        try:
            import os
            toml_path = os.path.join(os.path.dirname(__file__), "pyproject.toml")
            if not os.path.exists(toml_path):
                toml_path = "pyproject.toml"
            if os.path.exists(toml_path):
                with open(toml_path, "r") as f:
                    for line in f:
                        if line.strip().startswith("version"):
                            return "v" + line.split("=")[1].strip().strip('"').strip("'")
        except Exception:
            pass
        return "v0.2.0"

    def _color_logo(self, progress: float) -> str:
        rows = self._LOGO_ROWS
        ncols = max(len(r) for r in rows)

        all_chars: list[tuple[int, int, str]] = []
        for col in range(ncols):
            for r_idx, row in enumerate(rows):
                if col < len(row) and row[col] not in (" ", "\r"):
                    all_chars.append((r_idx, col, row[col]))

        total = len(all_chars)
        filled = int(progress * total)

        result_rows = [list(row) for row in rows]
        for i, (r_idx, col, ch) in enumerate(all_chars):
            result_rows[r_idx][col] = (
                f"[#5ac1fe]{ch}[/]" if i < filled else f"[#3f4043]{ch}[/]"
            )

        return "\n".join("".join(r) for r in result_rows)

    def compose(self) -> ComposeResult:
        with Vertical(id="splash-frame"):
            yield Static(self._color_logo(0.0), id="splash-logo")
            yield Static("Your Terminal. Reimagined.", id="splash-tagline")
            yield Static(self.version, id="splash-version")
            yield Static("Initializing…", id="splash-status")

    def on_mount(self) -> None:
        self.timer = self.set_interval(self.step_time, self.tick)

    def tick(self) -> None:
        self.progress += 1.0 / self.steps
        if self.progress >= 1.0:
            self.progress = 1.0
            if self.timer:
                self.timer.stop()
            self.query_one("#splash-logo", Static).update(
                self._color_logo(1.0)
            )
            from main import MainScreen
            self.app.push_screen(MainScreen())
            return

        statuses = [
            "Boot sequence initiated…",
            "Loading configuration…",
            "Registering themes…",
            "Mapping file icons…",
            "Preparing editor…",
            "Warming up cache…",
            "Ready.",
        ]
        status_idx = min(int(self.progress * len(statuses)), len(statuses) - 1)

        try:
            self.query_one("#splash-logo", Static).update(
                self._color_logo(self.progress)
            )
            self.query_one("#splash-status", Static).update(
                f"[#686868]{statuses[status_idx]}[/#686868]"
            )
        except Exception:
            pass


THEME_PICKER_SCREEN_CSS = """
ThemePickerScreen {
    align: center middle;
    background: #030508;
}
#tp-dialog {
    width: 48;
    height: 24;
    padding: 0;
    background: #131721;
    border: tall #5ac1fe;
}
#tp-titlebar {
    width: 100%;
    height: 3;
    background: #0d1016;
    border-bottom: solid #2e3038;
    padding: 0 2;
    align: left middle;
}
#tp-title {
    width: 1fr;
    color: #5ac1fe;
    text-style: bold;
}
#tp-count {
    width: auto;
    color: #686868;
}
#tp-list {
    background: #0d1016;
    border: none;
    height: 1fr;
    margin: 0;
}
#tp-hint {
    width: 100%;
    text-align: center;
    color: #686868;
    height: 1;
    padding: 0 2;
    border-top: solid #2e3038;
}
"""
register_css_template("theme_picker_screen", THEME_PICKER_SCREEN_CSS)


class ThemePickerScreen(Screen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Confirm"),
    ]
    CSS = THEME_PICKER_SCREEN_CSS

    def __init__(self, themes: list[dict], initial_theme: dict, **kwargs):
        super().__init__(**kwargs)
        self._themes = themes
        self._initial_theme = initial_theme

    def compose(self) -> ComposeResult:
        with Vertical(id="tp-dialog"):
            with Horizontal(id="tp-titlebar"):
                yield Label("🎨  Theme Picker", id="tp-title")
                yield Label(f"{len(self._themes)} themes", id="tp-count")
            yield OptionList(id="tp-list")
            yield Label("↑↓ Navigate  Enter Select  Esc Cancel", id="tp-hint")

    def on_mount(self) -> None:
        opt_list = self.query_one("#tp-list", OptionList)
        active_idx = 0
        for i, theme in enumerate(self._themes):
            # Build a colored swatch using accent color indicator
            acc = theme.get("accent", "#888888")
            is_active = theme["name"] == self._initial_theme["name"]
            check = "✓ " if is_active else "  "
            opt_list.add_option(f"{check}{theme['name']}")
            if is_active:
                active_idx = i
        opt_list.highlighted = active_idx
        opt_list.focus()

    @on(OptionList.OptionHighlighted)
    def on_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_index is not None and event.option_index < len(self._themes):
            theme = self._themes[event.option_index]
            self.app.apply_theme(theme)

    @on(OptionList.OptionSelected)
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_index is not None and event.option_index < len(self._themes):
            theme = self._themes[event.option_index]
            self.dismiss(theme)

    def action_confirm(self) -> None:
        opt_list = self.query_one("#tp-list", OptionList)
        idx = opt_list.highlighted
        if idx is not None and idx < len(self._themes):
            self.dismiss(self._themes[idx])
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.app.apply_theme(self._initial_theme)
        self.dismiss(None)
