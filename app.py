from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import DirectoryTree, TextArea
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

    TextArea {
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
            with Container(id="editor-panel"):
                yield TextArea(id="editor", show_line_numbers=True)
            yield Container(id="terminal-panel")

    def on_mount(self) -> None:
        self.query_one("#files-panel").border_title = " Files "
        self.query_one("#editor-panel").border_title = " Editor "
        self.query_one("#terminal-panel").border_title = " Terminal "

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        path = event.path
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return
        text_area = self.query_one("#editor", TextArea)
        text_area.load_text(content)
        text_area.language = self._detect_language(path)

    def _detect_language(self, path) -> str | None:
        ext = path.suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".json": "json",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".md": "markdown",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".sql": "sql",
            ".rs": "rust",
            ".go": "go",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".java": "java",
            ".sh": "bash",
            ".bash": "bash",
            ".rb": "ruby",
            ".php": "php",
            ".xml": "xml",
            ".svg": "xml",
        }
        return mapping.get(ext)


if __name__ == "__main__":
    app = TrixApp()
    app.run()
