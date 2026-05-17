from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal


class TrixApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }

    Container {
        border: solid $primary;
        border-title-align: center;
        padding: 1;
    }

    #files-panel {
        width: 25;
    }

    #editor-panel {
        width: 1fr;
    }

    #terminal-panel {
        width: 30;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            files = Container(id="files-panel")
            files.border_title = " Files "
            yield files

            editor = Container(id="editor-panel")
            editor.border_title = " Editor "
            yield editor

            terminal = Container(id="terminal-panel")
            terminal.border_title = " Terminal "
            yield terminal


if __name__ == "__main__":
    app = TrixApp()
    app.run()
