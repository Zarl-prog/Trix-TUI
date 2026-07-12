from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Any

from textual.app import ComposeResult
from textual.events import Click, Key, MouseDown
from textual.widget import Widget
from textual.widgets import Input, RichLog


_ANSI_ESCAPE = re.compile(
    r"\x1b\[[\d;]*[A-Za-z]"
    r"|\x1b\[\?[\d;]*[hl]"
    r"|\x1b\][^\x07]*(?:\x07|\x1b\\)"
    r"|\x1b[PX^_].*?\x1b\\"
    r"|\x1b[@-Z\-_]"
    r"|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
)


def strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


_IS_WINDOWS = sys.platform == "win32"

_STARTUP_FILTERS: tuple[str, ...] = ()
_PROMPT_RE: re.Pattern | None = None
_DEFAULT_SHELL = "powershell.exe"

if _IS_WINDOWS:
    _STARTUP_FILTERS = (
        "Windows PowerShell",
        "Copyright (C) Microsoft Corporation",
        "Install the latest PowerShell",
        "https://aka.ms/PSWindows",
    )
    _PROMPT_RE = re.compile(r"^PS [A-Za-z]:\\.*> ?")
    _DEFAULT_SHELL = "powershell.exe"
else:
    _DEFAULT_SHELL = os.environ.get("SHELL", "bash")


def _is_startup_noise(line: str) -> bool:
    if not _STARTUP_FILTERS:
        return False
    stripped = line.strip()
    if not stripped:
        return True
    for pattern in _STARTUP_FILTERS:
        if pattern in stripped:
            return True
    return False


def _clean_prompt(line: str) -> str:
    if _PROMPT_RE and _PROMPT_RE.match(line):
        return "\u276f"
    return line


class _SpacingTracker:
    def __init__(self) -> None:
        self._prev_blank = False

    def process(self, line: str) -> str | None:
        if not line.strip():
            if self._prev_blank:
                return None
            self._prev_blank = True
            return ""
        self._prev_blank = False
        return line


class TerminalOutputLog(RichLog):
    def on_click(self, event: Click) -> None:
        parent = self.parent
        if parent and hasattr(parent, "input_bar"):
            parent.input_bar.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        parent = self.parent
        if parent and hasattr(parent, "input_bar"):
            parent.input_bar.focus()


class TerminalWidget(Widget, can_focus=True):
    """Embedded terminal using the system shell."""

    COLS = 200
    ROWS = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._process: Any = None
        self._read_task: asyncio.Task | None = None
        self._history: list[str] = []
        self._hist_idx: int = -1
        self._startup_phase = True
        self._spacing = _SpacingTracker()
        self._winpty_impl = None
        if _IS_WINDOWS:
            import winpty
            self._winpty_impl = winpty

    async def _read_loop(self) -> None:
        log = self.query_one("#term-output", RichLog)
        loop = asyncio.get_event_loop()
        buf = ""

        while True:
            if _IS_WINDOWS:
                alive = self._process and self._process.isalive()
            else:
                p = self._process
                alive = p is not None and isinstance(p, asyncio.subprocess.Process) and p.returncode is None

            if not alive:
                break

            try:
                if _IS_WINDOWS:
                    data = await loop.run_in_executor(None, self._process.read, 4096)
                else:
                    data = await self._process.stdout.read(4096)

                if not data:
                    await asyncio.sleep(0.01)
                    continue

                raw = data if isinstance(data, str) else data.decode("utf-8", errors="replace")
                buf += raw

                if "\x1b[2J" in buf or "\x1b[3J" in buf:
                    log.clear()
                    buf = ""
                    self._spacing = _SpacingTracker()
                    continue

                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self._write_line(line)

            except Exception as e:
                log.write(f"[READ ERROR] {e}")
                await asyncio.sleep(0.1)

    def _write_line(self, raw_line: str) -> None:
        line = strip_ansi(raw_line)
        line = line.rstrip("\r")

        if self._startup_phase:
            if _PROMPT_RE and _PROMPT_RE.match(line):
                self._startup_phase = False
                self._spacing = _SpacingTracker()
                return
            if _is_startup_noise(line):
                return

        line = _clean_prompt(line)
        out = self._spacing.process(line)
        if out is None:
            return
        log = self.query_one("#term-output", RichLog)
        log.write(out)

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
            self._write_pty("\x03")
        elif key == "ctrl+z":
            event.prevent_default()
            self._write_pty("\x1a")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value
        self.query_one("#term-input", Input).clear()
        if cmd:
            self._history.append(cmd)
            self._query_one_write(f"\u276f {cmd}")
        self._hist_idx = -1
        self._write_pty(cmd + "\n")

    def _write_pty(self, data: str) -> None:
        if self._process is None:
            return
        try:
            if _IS_WINDOWS:
                self._process.write(data)
            else:
                p = self._process
                if isinstance(p, asyncio.subprocess.Process) and p.returncode is None:
                    p.stdin.write(data)
                    asyncio.ensure_future(p.stdin.drain())
        except Exception as e:
            self._query_one_write(f"[WRITE ERROR] {e}")

    def write(self, text: str) -> None:
        self._query_one_write(text)

    def _query_one_write(self, text: str) -> None:
        log = self.query_one("#term-output", RichLog)
        log.write(strip_ansi(text))

    async def on_unmount(self) -> None:
        if self._read_task:
            self._read_task.cancel()
        if _IS_WINDOWS:
            if self._process and self._process.isalive():
                self._process.terminate()
        else:
            p = self._process
            if isinstance(p, asyncio.subprocess.Process) and p.returncode is None:
                p.terminate()
                try:
                    await asyncio.wait_for(p.wait(), timeout=2)
                except asyncio.TimeoutError:
                    p.kill()

        self._hist_idx = -1
        self._startup_phase = True
        self._spacing = _SpacingTracker()

    @property
    def input_bar(self) -> Input:
        return self.query_one("#term-input", Input)

    def on_click(self, event: Click) -> None:
        self.input_bar.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        self.input_bar.focus()

    def compose(self) -> ComposeResult:
        yield TerminalOutputLog(id="term-output", auto_scroll=True, markup=False, highlight=False)
        yield Input(id="term-input", placeholder="\u276f")

    def on_mount(self) -> None:
        asyncio.get_event_loop().create_task(self._start_pty())

    async def _start_pty(self) -> None:
        log = self.query_one("#term-output", RichLog)
        try:
            if _IS_WINDOWS:
                self._process = self._winpty_impl.PtyProcess.spawn(
                    _DEFAULT_SHELL,
                    dimensions=(self.ROWS, self.COLS),
                )
                self._read_task = asyncio.get_event_loop().create_task(self._read_loop())
            else:
                self._process = await asyncio.create_subprocess_exec(
                    _DEFAULT_SHELL,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                self._read_task = asyncio.get_event_loop().create_task(self._read_loop())
            log.write(f"Terminal ready ({_DEFAULT_SHELL}).")
        except Exception as e:
            log.write(f"[ERROR] Failed to start terminal: {e}")
