from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import DirectoryTree, Static, TextArea


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

    #terminal-output {
        height: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Container(id="files-panel"):
                yield DirectoryTree(".")
            with Container(id="editor-panel"):
                yield TextArea(id="editor", show_line_numbers=True)
            with Container(id="terminal-panel"):
                yield Static(id="terminal-output")

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
        self._current_file = path
        self._has_changes = False
        self._update_editor_title()

    def on_text_area_changed(self) -> None:
        if self._current_file is None:
            return
        if not self._has_changes:
            self._has_changes = True
            self._update_editor_title()

    def action_save(self) -> None:
        if self._current_file is None:
            self.query_one("#terminal-output", Static).update("No file open")
            return
        text_area = self.query_one("#editor", TextArea)
        self._current_file.write_text(text_area.text, encoding="utf-8")
        self._has_changes = False
        self._update_editor_title()

    def _update_editor_title(self) -> None:
        panel = self.query_one("#editor-panel")
        if self._current_file is None:
            panel.border_title = " Editor "
        else:
            name = self._current_file.name
            suffix = " *" if self._has_changes else ""
            panel.border_title = f" Editor — {name}{suffix} "

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
