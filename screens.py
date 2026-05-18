from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, Static

_HELP = """\
 [bold #5ac1fe]Layout[/bold #5ac1fe]
   [#bfbdb6]Ctrl+B[/#bfbdb6]           Toggle File Tree
   [#bfbdb6]Ctrl+O[/#bfbdb6]           Open Folder

 [bold #5ac1fe]Editor[/bold #5ac1fe]
   [#bfbdb6]Ctrl+S[/#bfbdb6]           Save File
   [#bfbdb6]Ctrl+T[/#bfbdb6]           Cycle Theme

 [bold #5ac1fe]Terminal[/bold #5ac1fe]
   [#bfbdb6]Ctrl+C[/#bfbdb6]           Copy selection / Interrupt
   [#bfbdb6]Ctrl+Shift+C[/#bfbdb6]     Copy Selected Text
   [#bfbdb6]↑ ↓[/#bfbdb6]              Command History
   [#bfbdb6]cls[/#bfbdb6]              Clear Terminal

 [bold #5ac1fe]General[/bold #5ac1fe]
   [#bfbdb6]?[/#bfbdb6]                Show This Help
   [#bfbdb6]Q[/#bfbdb6]                Quit App\
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
