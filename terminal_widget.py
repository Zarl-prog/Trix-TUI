import asyncio
import re

import winpty

from textual.app import ComposeResult
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Input, RichLog

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b.")
_CLEAR = re.compile(r"\x1b\[(?:2J|3J|\d*J)")


class TerminalWidget(Widget, can_focus=True):
    """Embedded PowerShell terminal using winpty PTY."""

    COLS = 200
    ROWS = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pty: winpty.PtyProcess | None = None
        self._read_task: asyncio.Task | None = None
        self._history: list[str] = []
        self._hist_idx: int = -1

    def compose(self) -> ComposeResult:
        yield RichLog(id="term-output", auto_scroll=True, markup=False, highlight=False)
        yield Input(id="term-input", placeholder="PowerShell>")

    def on_mount(self) -> None:
        self._start_pty()
        self.query_one("#term-input", Input).focus()

    def _start_pty(self) -> None:
        try:
            self._pty = winpty.PtyProcess.spawn(
                "powershell.exe",
                dimensions=(self.ROWS, self.COLS),
            )
            self._read_task = asyncio.get_event_loop().create_task(self._read_loop())
        except Exception as e:
            self.query_one("#term-output", RichLog).write(f"Failed to start PowerShell: {e}")

    async def _read_loop(self) -> None:
        log = self.query_one("#term-output", RichLog)
        loop = asyncio.get_event_loop()
        buf = ""
        while self._pty and self._pty.isalive():
            try:
                data = await loop.run_in_executor(None, self._pty.read, 4096)
                if not data:
                    await asyncio.sleep(0.01)
                    continue
                buf += data if isinstance(data, str) else data.decode("utf-8", errors="replace")
                if _CLEAR.search(buf):
                    log.clear()
                    buf = _CLEAR.sub("", buf)
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = _ANSI.sub("", line).rstrip("\r")
                    if line.strip():
                        log.write(line)
            except Exception:
                await asyncio.sleep(0.05)

    def on_key(self, event: Key) -> None:
        key = event.key
        inp = self.query_one("#term-input", Input)

        if key == "up" and self._history:
            self._hist_idx = min(self._hist_idx + 1, len(self._history) - 1)
            inp.value = self._history[-(self._hist_idx + 1)]
            inp.cursor_position = len(inp.value)
            event.prevent_default()
            return
        if key == "down":
            if self._hist_idx > 0:
                self._hist_idx -= 1
                inp.value = self._history[-(self._hist_idx + 1)]
            else:
                self._hist_idx = -1
                inp.value = ""
            inp.cursor_position = len(inp.value)
            event.prevent_default()
            return

        if key == "ctrl+c":
            event.prevent_default()
            log = self.query_one("#term-output", RichLog)
            sel = log.text_selection
            if sel:
                result = log.get_selection(sel)
                text = result[0] + result[1] if result else ""
                if text:
                    self.app.copy_to_clipboard(text)
                    self.app.notify("Copied to clipboard")
                    return
            self._write_pty(b"\x03")
        elif key == "ctrl+z":
            event.prevent_default()
            self._write_pty(b"\x1a")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value
        self.query_one("#term-input", Input).clear()
        if cmd:
            self._history.append(cmd)
            self.query_one("#term-output", RichLog).write(f"> {cmd}")
        self._hist_idx = -1
        self._write_pty((cmd + "\r").encode())

    def _write_pty(self, data: bytes) -> None:
        if self._pty and self._pty.isalive():
            try:
                self._pty.write(data.decode("utf-8", errors="replace"))
            except Exception:
                pass

    def write(self, text: str) -> None:
        self.query_one("#term-output", RichLog).write(text)

    async def on_unmount(self) -> None:
        if self._read_task:
            self._read_task.cancel()
        if self._pty and self._pty.isalive():
            self._pty.terminate()
