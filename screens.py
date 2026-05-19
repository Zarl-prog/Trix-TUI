from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, Static

_HELP = """\
 [bold #5ac1fe]File[/bold #5ac1fe]
   [#bfbdb6]Ctrl+N[/#bfbdb6]           New File
   [#bfbdb6]Ctrl+S[/#bfbdb6]           Save File
   [#bfbdb6]Ctrl+W[/#bfbdb6]           Close File
   [#bfbdb6]Ctrl+O[/#bfbdb6]           Open Folder
   [#bfbdb6]F2[/#bfbdb6]               Rename File
   [#bfbdb6]Delete[/#bfbdb6]           Delete File

 [bold #5ac1fe]Layout[/bold #5ac1fe]
   [#bfbdb6]Ctrl+B[/#bfbdb6]           Toggle File Tree
   [#bfbdb6]Ctrl+\[/#bfbdb6]           Zen Mode (Editor only)
   [#bfbdb6]Ctrl+1[/#bfbdb6]           Focus File Tree
   [#bfbdb6]Ctrl+2[/#bfbdb6]           Focus Editor
   [#bfbdb6]Ctrl+3[/#bfbdb6]           Focus Terminal
   [#bfbdb6]Ctrl+][/#bfbdb6]           Cycle Panels

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
   [#bfbdb6]Ctrl+Q[/#bfbdb6]           Quit (confirms if unsaved)
   [#bfbdb6]?[/#bfbdb6]                Show This Help\
"""


class HelpScreen(Screen):
    BINDINGS = [("escape", "dismiss", "Close"), ("question_mark", "dismiss", "Close")]

    CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(0,0,0,0.75);
    }
    #help-dialog {
        width: 52;
        height: auto;
        padding: 1 2;
        background: #1f2127;
        border: solid #5ac1fe;
    }
    #help-title {
        width: 100%;
        text-align: center;
        color: #5ac1fe;
        text-style: bold;
        margin-bottom: 1;
    }
    #help-body {
        width: 100%;
        color: #bfbdb6;
    }
    #help-close {
        width: 100%;
        text-align: center;
        color: #8a8986;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("⌨  Keyboard Shortcuts", id="help-title")
            yield Static(_HELP, id="help-body", markup=True)
            yield Label("Press [bold]Escape[/bold] or [bold]?[/bold] to close", id="help-close", markup=True)

    def action_dismiss(self) -> None:
        self.dismiss()


class ConfirmScreen(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    ConfirmScreen {
        align: center middle;
        background: rgba(0,0,0,0.7);
    }
    #cf-dialog {
        width: 44;
        height: auto;
        padding: 2;
        background: #1f2127;
        border: solid #ef7177;
    }
    #cf-msg { width: 100%; color: #bfbdb6; margin-bottom: 1; }
    #cf-buttons { height: auto; layout: horizontal; }
    Button { margin: 0 1; }
    """

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


class NewFileScreen(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    NewFileScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #nf-dialog {
        width: 50;
        height: auto;
        padding: 2;
        background: #1f2127;
        border: solid #5ac1fe;
    }
    Label { width: 100%; margin-bottom: 1; color: #bfbdb6; }
    #nf-input { width: 100%; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="nf-dialog"):
            yield Label("New file name:")
            yield Input(id="nf-input", placeholder="filename.txt")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


class RenameScreen(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    RenameScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #rn-dialog {
        width: 50;
        height: auto;
        padding: 2;
        background: #1f2127;
        border: solid #5ac1fe;
    }
    Label { width: 100%; margin-bottom: 1; color: #bfbdb6; }
    #rn-input { width: 100%; }
    """

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


class FolderPicker(Screen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    FolderPicker {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #dialog {
        width: 50;
        height: auto;
        padding: 2;
        background: #1f2127;
        border: solid #5ac1fe;
    }
    Label {
        width: 100%;
        margin-bottom: 1;
        color: #bfbdb6;
    }
    #folder-path { width: 100%; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Enter folder path:")
            yield Input(id="folder-path", placeholder="/path/to/folder")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)
