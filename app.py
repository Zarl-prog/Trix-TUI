from pathlib import Path
import asyncio
import json
import sys

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Button, DirectoryTree, Input, Label, RichLog, TextArea


def _load_themes() -> list[dict]:
    """Load themes from ayu.json, mapping Zed style keys to CSS variables."""
    try:
        data = json.loads((Path(__file__).parent / "ayu.json").read_text())
    except Exception:
        return []
    result = []
    for t in data["themes"]:
        s = t["style"]
        result.append({
            "name": t["name"],
            "bg": s.get("background", "#313337")[:7],
            "surface": s.get("surface.background", "#1f2127")[:7],
            "editor_bg": s.get("toolbar.background", "#0d1016")[:7],
            "text": s.get("text", "#bfbdb6")[:7],
            "text_muted": s.get("text.muted", "#8a8986")[:7],
            "accent": s.get("text.accent", "#5ac1fe")[:7],
            "border": s.get("border", "#3f4043")[:7],
            "border_focused": s.get("text.accent", "#5ac1fe")[:7],
            "selection": s.get("element.active", "#3e4043")[:7],
        })
    return result


THEMES = _load_themes() or [
    {
        "name": "Ayu Dark",
        "bg": "#313337", "surface": "#1f2127", "editor_bg": "#0d1016",
        "text": "#bfbdb6", "text_muted": "#8a8986", "accent": "#5ac1fe",
        "border": "#3f4043", "border_focused": "#5ac1fe", "selection": "#3e4043",
    }
]


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

    #folder-path {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Enter folder path:")
            yield Input(id="folder-path", placeholder="/path/to/folder")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


class TrixApp(App):
    CSS = """
    Screen {
        layout: horizontal;
        background: #313337;
    }

    Container {
        border: solid #3f4043;
        border-title-align: center;
        background: #1f2127;
    }

    Container:focus-within {
        border: solid #5ac1fe;
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
        background: #1f2127;
    }

    DirectoryTree > .tree--cursor {
        background: #3e4043;
    }

    DirectoryTree > .tree--highlight {
        background: #3e4043;
    }

    TextArea {
        height: 100%;
        background: #0d1016;
        color: #bfbdb6;
    }

    TextArea .text-area--gutter {
        background: #0d1016;
        color: #4b4c4e;
    }

    TextArea .text-area--cursor {
        background: #5ac1fe;
    }

    TextArea .text-area--selection {
        background: #1f2127;
    }

    #terminal-output {
        height: 1fr;
        background: #0d1016;
        color: #bfbdb6;
    }

    #terminal-buttons {
        height: auto;
        dock: bottom;
        padding: 0 1;
    }

    #terminal-buttons Button {
        min-width: 12;
        margin: 0 1;
        background: #1f2127;
        color: #bfbdb6;
        border: solid #3f4043;
    }

    Button:hover {
        background: #2d2f34;
    }

    Button:focus {
        border: solid #5ac1fe;
    }

    #terminal-input {
        height: 3;
        dock: bottom;
    }

    Input {
        background: #0d1016;
        color: #bfbdb6;
        border: solid #3f4043;
    }

    Input:focus {
        border: solid #5ac1fe;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
        ("ctrl+o", "open_folder", "Open Folder"),
        ("ctrl+t", "cycle_theme", "Cycle Theme"),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: Path | None = None
        self._has_changes = False
        self._shell_process: asyncio.subprocess.Process | None = None
        self._shell_output_task: asyncio.Task | None = None
        self._theme_index = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Container(id="files-panel"):
                yield DirectoryTree(".")
            with Container(id="editor-panel"):
                yield TextArea(id="editor", show_line_numbers=True)
            with Container(id="terminal-panel"):
                yield RichLog(
                    id="terminal-output",
                    auto_scroll=True,
                    highlight=True,
                    markup=True,
                )
                with Horizontal(id="terminal-buttons"):
                    yield Button("Clear", id="btn-clear")
                    yield Button("Run File", id="btn-run-file")
                    yield Button("Git Status", id="btn-git-status")
                    yield Button("List Files", id="btn-list-files")
                yield Input(id="terminal-input", placeholder="> ")

    async def on_mount(self) -> None:
        self.query_one("#files-panel").border_title = " Files "
        self.query_one("#editor-panel").border_title = " Editor "
        self.query_one("#terminal-panel").border_title = " Terminal "
        await self._start_shell()

    async def _start_shell(self) -> None:
        shells = ["bash", "zsh", "sh"]
        if sys.platform == "win32":
            shells = ["bash", "cmd", "powershell"]

        output = self.query_one("#terminal-output", RichLog)

        for shell in shells:
            try:
                self._shell_process = await asyncio.create_subprocess_exec(
                    shell,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                output.write(f"[#aad84c]Shell started: {shell}[/#aad84c]")
                self._shell_output_task = asyncio.create_task(self._read_shell_output())
                return
            except FileNotFoundError:
                continue

        output.write("[#ef7177]No shell found (tried bash, zsh, sh)[/#ef7177]")

    async def _read_shell_output(self) -> None:
        output = self.query_one("#terminal-output", RichLog)
        while True:
            try:
                line = await self._shell_process.stdout.readline()
                if not line:
                    break
                text = line.decode(errors="replace").rstrip()
                output.write(text)
            except Exception:
                break

    async def _send_to_shell(self, command: str) -> None:
        if self._shell_process is None or self._shell_process.returncode is not None:
            return
        output = self.query_one("#terminal-output", RichLog)
        output.write(f"[bold]$ {command}[/bold]")
        self._shell_process.stdin.write((command + "\n").encode())
        await self._shell_process.stdin.drain()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value
        self.query_one("#terminal-input", Input).clear()
        if not command:
            return
        await self._send_to_shell(command)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        output = self.query_one("#terminal-output", RichLog)

        if button_id == "btn-clear":
            output.clear()
        elif button_id == "btn-run-file":
            if self._current_file is None:
                output.write("[#ef7177]No file open[/#ef7177]")
            else:
                cmd = f"python {self._current_file}"
                await self._send_to_shell(cmd)
        elif button_id == "btn-git-status":
            await self._send_to_shell("git status")
        elif button_id == "btn-list-files":
            await self._send_to_shell("dir" if sys.platform == "win32" else "ls")

    def on_click(self, event: Click) -> None:
        terminal = self.query_one("#terminal-panel")
        inp = self.query_one("#terminal-input", Input)
        if terminal.region.contains(event.screen_x, event.screen_y):
            if self.focused is not inp:
                inp.focus()

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

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(THEMES)
        t = THEMES[self._theme_index]
        self.theme = t["name"].lower().replace(" ", "-")
        self.query_one("#terminal-output", RichLog).write(
            f"Theme: [bold]{t['name']}[/bold]"
        )

    async def action_open_folder(self) -> None:
        path_str = await self.push_screen_wait(FolderPicker())
        if path_str is None:
            return
        path = Path(path_str.strip())
        if not path.is_dir():
            self.query_one("#terminal-output", RichLog).write(
                f"[#ef7177]Invalid path: {path_str}[/#ef7177]"
            )
            return
        # Reload directory tree
        tree = self.query_one(DirectoryTree)
        tree.path = path
        # Clear editor
        self._current_file = None
        self._has_changes = False
        self.query_one("#editor", TextArea).load_text("")
        self._update_editor_title()
        # Update files panel title
        self.query_one("#files-panel").border_title = f" Files — {path.name} "

    def action_save(self) -> None:
        if self._current_file is None:
            self.query_one("#terminal-output", RichLog).write(
                "[#ef7177]No file open[/#ef7177]"
            )
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
