from __future__ import annotations

import asyncio
import fcntl
import os
import pty
import re
import signal
import struct
import sys
import termios
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


import re as _re

# ── Terminal line colorizer ────────────────────────────────────────────────

_COLOR_RULES: list[tuple[_re.Pattern, str]] = [
    # Errors
    (_re.compile(r"(?i)(error|traceback|exception|fatal|failed|failure|critical|abort)", _re.IGNORECASE), "#ef7177"),
    # Warnings
    (_re.compile(r"(?i)(warning|warn|deprecated)", _re.IGNORECASE), "#e6b450"),
    # Success / OK
    (_re.compile(r"(?i)(success|succeeded|done|ok\b|passed|installed|complete|built)", _re.IGNORECASE), "#aad84c"),
    # Prompts (lines ending with $ or ❯ or lines that look like shell prompts)
    (_re.compile(r"(^|\s)(\$|❯|>>|#)\s*$"), "#5ac1fe"),
    # Git output
    (_re.compile(r"^(On branch|HEAD|commit [0-9a-f]{7}|Author:|Date:|    )"), "#bfbdb6"),
    # File paths
    (_re.compile(r"(/[\w./\-_]+|[A-Za-z]:\\[\w\\./\-_]+)"), "#39bae6"),
    # Numbers / exit codes
    (_re.compile(r"\b(exit code|returned|status):?\s*\d+"), "#feb454"),
]


def _colorize_line(line: str) -> str:
    """Return a Rich markup-colored version of a terminal output line."""
    if not line.strip():
        return line

    # Prompt lines (PS1-style: ends with $ or > or ❯)
    if _re.search(r"[$❯#>]\s*$", line):
        return f"[bold #5ac1fe]{line}[/bold #5ac1fe]"

    # Error lines
    if _re.search(r"(?i)\b(error|traceback|exception|fatal|failed|failure|critical|abort)\b", line):
        return f"[#ef7177]{line}[/#ef7177]"

    # Warning lines
    if _re.search(r"(?i)\b(warning|warn|deprecated)\b", line):
        return f"[#e6b450]{line}[/#e6b450]"

    # Success lines
    if _re.search(r"(?i)\b(success|succeeded|done|passed|installed|complete|built)\b", line):
        return f"[#aad84c]{line}[/#aad84c]"

    # Git branch / status lines
    if _re.match(r"^(On branch|HEAD detached|Your branch|nothing to commit|Changes|Untracked)", line):
        return f"[#bfbdb6]{line}[/#bfbdb6]"

    # Git commit hash lines
    if _re.match(r"^[0-9a-f]{7,40}\s", line):
        return f"[#feb454]{line}[/#feb454]"

    # Info / note lines
    if _re.search(r"(?i)\b(info|note|hint|tip)\b", line):
        return f"[#4b4c4e]{line}[/#4b4c4e]"

    return line


_DEFAULT_SHELL = os.environ.get("SHELL", "/bin/bash")


class _SpacingTracker:
    """Collapses consecutive blank lines into a single blank line."""

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
    """
    Embedded terminal using a real PTY (pty.fork) on Linux/macOS.
    Spawns $SHELL (default: /bin/bash) in a pseudo-terminal so interactive
    programs (python REPL, vim, top, etc.) work correctly.
    """

    COLS = 200
    ROWS = 50

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._master_fd: int | None = None
        self._child_pid: int | None = None
        self._read_task: asyncio.Task | None = None
        self._history: list[str] = []
        self._hist_idx: int = -1
        self._spacing = _SpacingTracker()

    # ── Compose / mount ────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield TerminalOutputLog(
            id="term-output", auto_scroll=True, markup=False, highlight=False
        )
        yield Input(id="term-input", placeholder="❯")

    def on_mount(self) -> None:
        asyncio.get_event_loop().create_task(self._start_pty())

    # ── PTY lifecycle ──────────────────────────────────────────────────────

    async def _start_pty(self) -> None:
        log = self.query_one("#term-output", RichLog)
        try:
            pid, master_fd = pty.fork()
        except Exception as e:
            log.write(f"[ERROR] pty.fork() failed: {e}")
            return

        if pid == 0:
            # ── child process ──
            # Set terminal size
            try:
                s = struct.pack("HHHH", self.ROWS, self.COLS, 0, 0)
                fcntl.ioctl(pty.STDOUT_FILENO, termios.TIOCSWINSZ, s)
            except Exception:
                pass
            # Clean environment
            env = os.environ.copy()
            env.setdefault("TERM", "xterm-256color")
            env.setdefault("COLORTERM", "truecolor")
            try:
                os.execvpe(_DEFAULT_SHELL, [_DEFAULT_SHELL], env)
            except Exception:
                os._exit(1)
        else:
            # ── parent process ──
            self._child_pid = pid
            self._master_fd = master_fd
            # Set initial PTY window size
            try:
                s = struct.pack("HHHH", self.ROWS, self.COLS, 0, 0)
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, s)
            except Exception:
                pass
            # Make master_fd non-blocking for async reading
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            self._read_task = asyncio.get_event_loop().create_task(self._read_loop())
            log.write(f"[#aad84c]Terminal ready ({_DEFAULT_SHELL})[/#aad84c]", markup=True)

    async def _read_loop(self) -> None:
        log = self.query_one("#term-output", RichLog)
        buf = ""
        loop = asyncio.get_event_loop()

        while self._master_fd is not None:
            try:
                data = await loop.run_in_executor(None, self._blocking_read)
            except Exception:
                await asyncio.sleep(0.02)
                continue

            if not data:
                await asyncio.sleep(0.02)
                continue

            raw = data.decode("utf-8", errors="replace")
            buf += raw

            # Handle clear-screen escape sequences
            if "\x1b[2J" in buf or "\x1b[3J" in buf:
                log.clear()
                buf = ""
                self._spacing = _SpacingTracker()
                continue

            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                self._write_line(line)

    def _blocking_read(self) -> bytes:
        """Read from master fd, return empty bytes if nothing available."""
        if self._master_fd is None:
            return b""
        try:
            return os.read(self._master_fd, 4096)
        except BlockingIOError:
            import time
            time.sleep(0.02)
            return b""
        except OSError:
            return b""

    def _write_line(self, raw_line: str) -> None:
        line = strip_ansi(raw_line).rstrip("\r")
        out = self._spacing.process(line)
        if out is None:
            return
        log = self.query_one("#term-output", RichLog)
        colored = _colorize_line(out)
        log.write(colored, markup=True)

    def _write_pty(self, data: str) -> None:
        if self._master_fd is None:
            return
        try:
            os.write(self._master_fd, data.encode("utf-8"))
        except OSError as e:
            self._safe_write(f"[WRITE ERROR] {e}")

    def _safe_write(self, text: str) -> None:
        try:
            self.query_one("#term-output", RichLog).write(strip_ansi(text))
        except Exception:
            pass

    # ── Input handling ─────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value
        self.query_one("#term-input", Input).clear()
        if cmd:
            self._history.append(cmd)
        self._hist_idx = -1
        self._write_pty(cmd + "\n")

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
            # Copy selected terminal text if any
            log = self.query_one("#term-output", RichLog)
            sel = log.text_selection
            if sel:
                result = log.get_selection(sel)
                text = result[0] + result[1] if result else ""
                if text:
                    self.app.copy_to_clipboard(text)
                    self.app.notify("Copied to clipboard")
                    return
            # Otherwise send SIGINT to child
            self._write_pty("\x03")

        elif key == "ctrl+z":
            event.prevent_default()
            self._write_pty("\x1a")

    # ── Click / focus ──────────────────────────────────────────────────────

    @property
    def input_bar(self) -> Input:
        return self.query_one("#term-input", Input)

    def on_click(self, event: Click) -> None:
        self.input_bar.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        self.input_bar.focus()

    # ── Cleanup ────────────────────────────────────────────────────────────

    async def on_unmount(self) -> None:
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        if self._child_pid is not None:
            try:
                os.kill(self._child_pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                os.waitpid(self._child_pid, os.WNOHANG)
            except OSError:
                pass
            self._child_pid = None

        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

        self._hist_idx = -1
        self._spacing = _SpacingTracker()

    # ── Public helper ──────────────────────────────────────────────────────

    def write(self, text: str) -> None:
        self._safe_write(text)
