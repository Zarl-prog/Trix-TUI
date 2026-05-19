from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, Static, OptionList

_HELP = """\
 [bold #5ac1fe]File[/bold #5ac1fe]
   [#bfbdb6]Ctrl+N[/#bfbdb6]           New File
   [#bfbdb6]Ctrl+S[/#bfbdb6]           Save File
   [#bfbdb6]Ctrl+W[/#bfbdb6]           Close File
   [#bfbdb6]Ctrl+O[/#bfbdb6]           Open Folder
   [#bfbdb6]F2[/#bfbdb6]               Rename File
   [#bfbdb6]Delete[/#bfbdb6]           Delete File (focus file tree first)

 [bold #5ac1fe]Layout[/bold #5ac1fe]
   [#bfbdb6]Ctrl+][/#bfbdb6]           Cycle Panels (Files→Editor→Terminal)
   [#bfbdb6]Click[/#bfbdb6]            Focus any panel by clicking it
   [#bfbdb6]Ctrl+B[/#bfbdb6]           Toggle File Tree
   [#bfbdb6]Ctrl+\[/#bfbdb6]           Zen Mode (Editor only)

 [bold #5ac1fe]Editor[/bold #5ac1fe]
   [#bfbdb6]Ctrl+Z[/#bfbdb6]           Undo
   [#bfbdb6]Ctrl+Y[/#bfbdb6]           Redo
   [#bfbdb6]Ctrl+A[/#bfbdb6]           Select All
   [#bfbdb6]Ctrl+_[/#bfbdb6]           Toggle Comment
   [#bfbdb6]Ctrl+D[/#bfbdb6]           Duplicate Line
   [#bfbdb6]Ctrl+T[/#bfbdb6]           Cycle Theme
   [#bfbdb6]Ctrl+R[/#bfbdb6]           Reload File Tree

 [bold #5ac1fe]Terminal[/bold #5ac1fe]
   [#bfbdb6]Ctrl+C[/#bfbdb6]           Copy selection / Interrupt
   [#bfbdb6]Ctrl+Shift+C[/#bfbdb6]     Copy Selected Text
   [#bfbdb6]↑ ↓[/#bfbdb6]              Command History
   [#bfbdb6]cls[/#bfbdb6]              Clear Terminal

 [bold #5ac1fe]General[/bold #5ac1fe]
   [#bfbdb6]Ctrl+G[/#bfbdb6]           Git History
   [#bfbdb6]Ctrl+Q[/#bfbdb6]           Quit (confirms if unsaved)
   [#bfbdb6]F1[/#bfbdb6]               Show This Help\
"""


from themes import register_css_template

HELP_SCREEN_CSS = """
HelpScreen {
    align: center middle;
    background: rgba(0,0,0,0.75);
}
#help-dialog {
    width: 52;
    height: auto;
    padding: 1 2;
    background: var(--panel);
    border: solid var(--border-focused);
}
#help-title {
    width: 100%;
    text-align: center;
    color: var(--accent);
    text-style: bold;
    margin-bottom: 1;
}
#help-body {
    width: 100%;
    color: var(--text);
}
#help-close {
    width: 100%;
    text-align: center;
    color: var(--text-muted);
    margin-top: 1;
}
"""
register_css_template("help_screen", HELP_SCREEN_CSS)


class HelpScreen(Screen):
    BINDINGS = [("escape", "dismiss", "Close"), ("f1", "dismiss", "Close")]
    CSS = HELP_SCREEN_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("⌨  Keyboard Shortcuts", id="help-title")
            yield Static(_HELP, id="help-body", markup=True)
            yield Label("Press [bold]Escape[/bold] or [bold]F1[/bold] to close", id="help-close", markup=True)

    def action_dismiss(self) -> None:
        self.dismiss()


CONFIRM_SCREEN_CSS = """
ConfirmScreen {
    align: center middle;
    background: rgba(0,0,0,0.7);
}
#cf-dialog {
    width: 44;
    height: auto;
    padding: 2;
    background: var(--panel);
    border: solid var(--error);
}
#cf-msg { width: 100%; color: var(--text); margin-bottom: 1; }
#cf-buttons { height: auto; layout: horizontal; }
ConfirmScreen Button { margin: 0 1; }
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
            yield Label(self._message, id="cf-msg")
            with Horizontal(id="cf-buttons"):
                yield Button("Yes", id="cf-yes", variant="error")
                yield Button("No", id="cf-no")

    def on_button_pressed(self, event) -> None:
        self.dismiss(event.button.id == "cf-yes")

    def action_cancel(self) -> None:
        self.dismiss(False)


NEW_FILE_SCREEN_CSS = """
NewFileScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}
#nf-dialog {
    width: 50;
    height: auto;
    padding: 2;
    background: var(--panel);
    border: solid var(--border-focused);
}
NewFileScreen Label { width: 100%; margin-bottom: 1; color: var(--text); }
#nf-input { width: 100%; }
"""
register_css_template("new_file_screen", NEW_FILE_SCREEN_CSS)


class NewFileScreen(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = NEW_FILE_SCREEN_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="nf-dialog"):
            yield Label("New file name:")
            yield Input(id="nf-input", placeholder="filename.txt")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


RENAME_SCREEN_CSS = """
RenameScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}
#rn-dialog {
    width: 50;
    height: auto;
    padding: 2;
    background: var(--panel);
    border: solid var(--border-focused);
}
RenameScreen Label { width: 100%; margin-bottom: 1; color: var(--text); }
#rn-input { width: 100%; }
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
            yield Label(f"Rename: {self._current_name}")
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
    background: rgba(0, 0, 0, 0.7);
}
#dialog {
    width: 50;
    height: auto;
    padding: 2;
    background: var(--panel);
    border: solid var(--border-focused);
}
FolderPicker Label {
    width: 100%;
    margin-bottom: 1;
    color: var(--text);
}
#folder-path { width: 100%; }
"""
register_css_template("folder_picker", FOLDER_PICKER_CSS)


class FolderPicker(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = FOLDER_PICKER_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Enter folder path:")
            yield Input(id="folder-path", placeholder="/path/to/folder")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


SPLASH_SCREEN_CSS = """
SplashScreen {
    align: center middle;
    background: #0d1016;
}
#splash-container {
    align: center middle;
    width: 100%;
    height: 100%;
}
#splash-logo {
    text-align: center;
    color: #5ac1fe;
    text-style: bold;
    margin-bottom: 1;
}
#splash-tagline {
    text-align: center;
    color: #8a8986;
    text-style: bold;
    margin-bottom: 0;
}
#splash-version {
    text-align: center;
    color: #3f4043;
    margin-bottom: 2;
}
#splash-bar {
    text-align: center;
    color: #5ac1fe;
    width: 32;
    margin-bottom: 0;
}
#splash-status {
    text-align: center;
    color: #8a8986;
    width: 32;
}
"""
register_css_template("splash_screen", SPLASH_SCREEN_CSS)


class SplashScreen(Screen):
    """Splash screen shown for 2 seconds upon app startup."""

    CSS = SPLASH_SCREEN_CSS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress = 0.0
        self.duration = 2.0
        self.steps = 40
        self.step_time = self.duration / self.steps
        self.timer = None
        self.version = self._get_version()

    def _get_version(self) -> str:
        try:
            import os
            if os.path.exists("pyproject.toml"):
                with open("pyproject.toml", "r") as f:
                    for line in f:
                        if line.strip().startswith("version"):
                            return "v" + line.split("=")[1].strip().strip('"').strip("'")
        except Exception:
            pass
        return "v0.1.0"

    def compose(self) -> ComposeResult:
        logo = (
            "████████╗██████╗ ██╗██╗  ██╗\n"
            "╚══██╔══╝██╔══██╗██║╚██╗██╔╝\n"
            "   ██║   ██████╔╝██║ ╚███╔╝ \n"
            "   ██║   ██╔══██╗██║ ██╔██╗ \n"
            "   ██║   ██║  ██║██║██╔╝ ██╗\n"
            "   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝"
        )
        with Vertical(id="splash-container"):
            yield Static(logo, id="splash-logo")
            yield Label("Your Terminal. Reimagined.", id="splash-tagline")
            yield Label(self.version, id="splash-version")
            yield Static("░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░", id="splash-bar")
            yield Static("Initializing...", id="splash-status")

    def on_mount(self) -> None:
        self.timer = self.set_interval(self.step_time, self.tick)

    def tick(self) -> None:
        self.progress += 1.0 / self.steps
        if self.progress >= 1.0:
            self.progress = 1.0
            if self.timer:
                self.timer.stop()
            from main import MainScreen
            self.app.push_screen(MainScreen())
            return

        # Update bar
        bar_width = 30
        filled = int(self.progress * bar_width)
        bar_str = "█" * filled + "░" * (bar_width - filled)
        self.query_one("#splash-bar", Static).update(bar_str)

        # Update status text
        statuses = [
            "Initializing...",
            "Loading themes...",
            "Starting terminal...",
            "Ready."
        ]
        status_idx = min(int(self.progress * len(statuses)), len(statuses) - 1)
        self.query_one("#splash-status", Static).update(statuses[status_idx])


THEME_PICKER_SCREEN_CSS = """
ThemePickerScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.75);
}
#tp-dialog {
    width: 36;
    height: 18;
    padding: 1 2;
    background: var(--panel);
    border: solid var(--border-focused);
}
#tp-title {
    width: 100%;
    text-align: center;
    color: var(--accent);
    text-style: bold;
    margin-bottom: 1;
}
#tp-list {
    background: var(--background);
    border: none;
    height: 1fr;
}
#tp-hint {
    width: 100%;
    text-align: center;
    color: var(--text-muted);
    margin-top: 1;
}
"""
register_css_template("theme_picker_screen", THEME_PICKER_SCREEN_CSS)


class ThemePickerScreen(Screen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Confirm")
    ]
    CSS = THEME_PICKER_SCREEN_CSS

    def __init__(self, themes: list[dict], initial_theme: dict, **kwargs):
        super().__init__(**kwargs)
        self._themes = themes
        self._initial_theme = initial_theme

    def compose(self) -> ComposeResult:
        with Vertical(id="tp-dialog"):
            yield Label("🎨 Choose Theme", id="tp-title")
            yield OptionList(id="tp-list")
            yield Label("Enter Select • Esc Cancel", id="tp-hint")

    def on_mount(self) -> None:
        opt_list = self.query_one("#tp-list", OptionList)
        active_idx = 0
        for i, theme in enumerate(self._themes):
            prefix = "✓ " if theme["name"] == self._initial_theme["name"] else "  "
            opt_list.add_option(f"{prefix}{theme['name']}")
            if theme["name"] == self._initial_theme["name"]:
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
