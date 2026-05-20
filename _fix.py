"""Fix the terminal_widget.py duplication and add missing methods."""
with open("terminal_widget.py", "r") as f:
    c = f.read()

# Remove the duplicated tail section
dup_marker = '        self._hist_idx: int = -1\n        self._startup_phase = True\n        self._spacing = _SpacingTracker()'
dup_pos = c.rfind(dup_marker)
if dup_pos > 0:
    c = c[:dup_pos]
    print("Removed duplicate tail")
else:
    print("No duplicate tail found")

# Fix __init__ and add missing methods
old = (
    '    def __init__(self, **kwargs):\n'
    '        super().__init__(**kwargs)\n'
    '        self._pty: winpty.PtyProcess | None = None\n'
    '        self._read_task: asyncio.Task | None = None\n'
    '        self._history: list[str] = []\n'
    '\n'
    '    async def _read_loop(self) -> None:'
)
new = (
    '    def __init__(self, **kwargs):\n'
    '        super().__init__(**kwargs)\n'
    '        self._pty: winpty.PtyProcess | None = None\n'
    '        self._read_task: asyncio.Task | None = None\n'
    '        self._history: list[str] = []\n'
    '        self._hist_idx: int = -1\n'
    '        self._startup_phase = True\n'
    '        self._spacing = _SpacingTracker()\n'
    '\n'
    '    @property\n'
    '    def input_bar(self) -> Input:\n'
    '        return self.query_one("#term-input", Input)\n'
    '\n'
    '    def on_click(self, event: Click) -> None:\n'
    '        self.input_bar.focus()\n'
    '\n'
    '    def on_mouse_down(self, event: MouseDown) -> None:\n'
    '        self.input_bar.focus()\n'
    '\n'
    '    def compose(self) -> ComposeResult:\n'
    '        yield TerminalOutputLog(id="term-output", auto_scroll=True, markup=False, highlight=False)\n'
    '        yield Input(id="term-input", placeholder="\u276f")\n'
    '\n'
    '    def on_mount(self) -> None:\n'
    '        self._start_pty()\n'
    '\n'
    '    def _start_pty(self) -> None:\n'
    '        log = self.query_one("#term-output", RichLog)\n'
    '        try:\n'
    '            self._pty = winpty.PtyProcess.spawn(\n'
    '                "powershell.exe",\n'
    '                dimensions=(self.ROWS, self.COLS),\n'
    '            )\n'
    '            self._read_task = asyncio.get_event_loop().create_task(self._read_loop())\n'
    '            log.write("PowerShell ready.")\n'
    '        except Exception as e:\n'
    '            log.write(f"[ERROR] Failed to start PowerShell: {e}")\n'
    '\n'
    '    async def _read_loop(self) -> None:'
)

if old in c:
    c = c.replace(old, new, 1)
    print("Fixed __init__ and added missing methods")
else:
    print("FAILED - old text not found!")
    exit(1)

with open("terminal_widget.py", "w", newline="\n", encoding="utf-8") as f:
    f.write(c)

import py_compile
py_compile.compile("terminal_widget.py", doraise=True)
print("File compiles OK!")
