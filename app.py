from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import DirectoryTree
import os


class TrixApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }

    Container {
        border: solid $primary;
        border-title-align: center;
    }

    #files-panel {
        width: 20%;
    }

    #editor-panel {
        width: 2fr;
    }

    #terminal-panel {
        width: 2fr;
    }

    DirectoryTree {
        height: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Container(id="files-panel"):
                yield DirectoryTree(os.getcwd())
            yield Container(id="editor-panel")
            yield Container(id="terminal-panel")

    def on_mount(self) -> None:
        self.query_one("#files-panel").border_title = " Files "
        self.query_one("#editor-panel").border_title = " Editor "
        self.query_one("#terminal-panel").border_title = " Terminal "


if __name__ == "__main__":
    app = TrixApp()
    app.run()
