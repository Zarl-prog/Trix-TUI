"""terminal_widget.py - Embedded PowerShell terminal using winpty PTY.

Features:
  - Comprehensive ANSI/VT100 escape sequence stripping
  - Startup banner filtering (copyright, upgrade notice)
  - Clean prompt display (CC instead of PS ...>)
  - Proper spacing between command output blocks
"""

from __future__ import annotations

import asyncio
import re
import winpty

from textual.app import ComposeResult
from textual.events import Click, Key, MouseDown
from textual.widget import Widget
from textual.widgets import Input, RichLog


# ==============================================================================
# ANSI / escape sequence stripping
# ==============================================================================

# Comprehensive regex that strips EVERY known ANSI/VT100 escape pattern.
# Covers CSI, OSC, DCS, SOS, PM, APC, Fe, and all control chars except \t \n \r.
_ANSI_ESCAPE = re.compile(
    # CSI sequences: ESC[ + optional params + final byte
    r"\x1b\[[\d;]*[A-Za-z]"
    # CSI private mode: ESC[? + digits + hl
    r"|\x1b\[\?[\d;]*[hl]"
    # OSC sequences: ESC] ... terminated by BEL (\x07) or ST (\x1b\\)
    r"|\x1b\][^\x07]*(?:\x07|\x1b\\)"
    # DCS/SOS/PM/APC: ESC P/X/^/_ ... terminated by ST
    r"|\x1b[PX^_].*?\x1b\\"
    # 2-byte escapes: ESC + one char from [@-Z\-_]
    r"|\x1b[@-Z\-_]"
    # All control characters EXCEPT \t (0x09), \n (0x0a), \r (0x0d)
    r"|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
)


def strip_ansi(text: str) -> str:
    """Remove ALL ANSI/VT100 escape codes and control characters from text.

    Preserves only printable characters plus \t, \n, \r.
    """
    return _ANSI_ESCAPE.sub("", text)


# ==============================================================================
# PowerShell startup banner filters
# ==============================================================================

_STARTUP_FILTERS = (
    "Windows PowerShell",
    "Copyright (C) Microsoft Corporation",
    "Install the latest PowerShell",
    "https://aka.ms/PSWindows",
)


def _is_startup_noise(line: str) -> bool:
    """Return True if line is part of the PowerShell startup banner."""
    stripped = line.strip()
    if not stripped:
        return True  # suppress all empty lines during startup
    for pattern in _STARTUP_FILTERS:
        if pattern in stripped:
            return True
    return False


# ==============================================================================
# Prompt detection / transformation
# ==============================================================================

# Matches PowerShell prompt like "PS C:\Users\...> "
_PROMPT_RE = re.compile(r"^PS [A-Za-z]:\\.*> ?")


def _clean_prompt(line: str) -> str:
    """Transform a PowerShell prompt line into a clean CC display."""
    if _PROMPT_RE.match(line):
        return "\u276f"
    return line


# ==============================================================================
# Spacing tracker - ensures exactly one blank line between output blocks
# ==============================================================================


class _SpacingTracker:
    """Tracks consecutive blank lines to collapse them to at most one."""

    def __init__(self) -> None:
        self._prev_blank = False

    def process(self, line: str) -> str | None:
        """Return the line to write, or None to skip."""
        if not line.strip():
            if self._prev_blank:
                return None  # suppress second consecutive blank
            self._prev_blank = True
            return ""  # write a blank line
        self._prev_blank = False
        return line


# ==============================================================================
# RichLog subclass that redirects focus
# ==============================================================================


class TerminalOutputLog(RichLog):
    """RichLog that redirects click/mouse focus to the parent's input bar."""

    def on_click(self, event: Click) -> None:
        parent = self.parent
        if parent and hasattr(parent, "input_bar"):
            parent.input_bar.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        parent = self.parent
        if parent and hasattr(parent, "input_bar"):
            parent.input_bar.focus()


# ==============================================================================
# TerminalWidget - main widget
# ==============================================================================


class TerminalWidget(Widget, can_focus=True):
    """Embedded PowerShell terminal using winpty PTY with clean output."""

    COLS = 200
    ROWS = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pty: winpty.PtyProcess | None = None
        self._read_task: asyncio.Task | None = None
        self._history: list[str] = []
        self._hist_idx: int = -1
        self._startup_phase = True
        self._spacing = _SpacingTracker()

    async def _read_loop(self) -> None:
        """Async loop reading PTY output, stripping escapes and filtering."""
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

                # Handle clear-screen sequences
                if "\x1b[2J" in buf or "\x1b[3J" in buf:
                    log.clear()
                    buf = ""
                    self._spacing = _SpacingTracker()
                    continue

                # Process complete lines from buffer
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self._write_line(line)

            except Exception as e:
                log.write(f"[READ ERROR] {e}")
                await asyncio.sleep(0.1)

    def _write_line(self, raw_line: str) -> None:
        """Strip, filter, and write one line of PTY output."""
        # 1. Strip ALL ANSI escape codes
        line = strip_ansi(raw_line)
        # 2. Strip trailing carriage returns
        line = line.rstrip("\r")
        # 3. During startup, suppress copyright/upgrade banner
        if self._startup_phase:
            if _PROMPT_RE.match(line):
                self._startup_phase = False
                self._spacing = _SpacingTracker()
                return
            if _is_startup_noise(line):
                return
        # 4. Clean PowerShell prompts to just CC
        line = _clean_prompt(line)
        # 5. Apply spacing rules (collapse consecutive blank lines)
        out = self._spacing.process(line)
        if out is None:
            return
        # 6. Write to the RichLog
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
            self._query_one_write(f"❯ {cmd}")
        self._hist_idx = -1
        self._write_pty(cmd + "\r\n")

    def _write_pty(self, data: str) -> None:
        if self._pty and self._pty.isalive():
            try:
                self._pty.write(data)
            except Exception as e:
                self._query_one_write(f"[WRITE ERROR] {e}")

    def write(self, text: str) -> None:
        """Public API to write text to terminal output."""
        self._query_one_write(text)

    def _query_one_write(self, text: str) -> None:
        """Write text to RichLog, always stripping ANSI codes."""
        log = self.query_one("#term-output", RichLog)
        log.write(strip_ansi(text))

    async def on_unmount(self) -> None:
        if self._read_task:
            self._read_task.cancel()
        if self._pty and self._pty.isalive():
            self._pty.terminate()

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
        yield Input(id="term-input", placeholder="❯")

    def on_mount(self) -> None:
        self._start_pty()

    def _start_pty(self) -> None:
        """Start the PowerShell process."""
        log = self.query_one("#term-output", RichLog)
        try:
            self._pty = winpty.PtyProcess.spawn(
                "powershell.exe",
                dimensions=(self.ROWS, self.COLS),
            )
            self._read_task = asyncio.get_event_loop().create_task(self._read_loop())
            log.write("PowerShell ready.")
        except Exception as e:
            log.write(f"[ERROR] Failed to start PowerShell: {e}")
