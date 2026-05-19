<div align="center">

```
████████╗██████╗ ██╗██╗  ██╗
╚══██╔══╝██╔══██╗██║╚██╗██╔╝
   ██║   ██████╔╝██║ ╚███╔╝
   ██║   ██╔══██╗██║ ██╔██╗
   ██║   ██║  ██║██║██╔╝ ██╗
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
```

**Your Terminal. Reimagined.**

[![PyPI version](https://badge.fury.io/py/trix-ide.svg)](https://pypi.org/project/trix-ide/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/Zarl-prog/Trix-TUI)

</div>

---

TRIX is a lightweight, terminal-native IDE built entirely inside your terminal. No Electron. No browser. No bloat. Just a fast, keyboard-driven development environment that lives where developers actually work.

---

## Preview

```
┌─ T R I X ────────────────────────────────────────────────────────────────────┐
│                                                                               │
│ ┌─ Files ──────┬──── Editor — app.py ──────────────────┬──── Terminal ──────┐ │
│ │ 📁 .git      │  1  from pathlib import Path          │ PowerShell>        │ │
│ │ 📁 trix      │  2  import asyncio                    │ PS C:\> git status  │ │
│ │   app.py     │  3  import json                       │ On branch main     │ │
│ │   main.py    │  4                                    │ nothing to commit  │ │
│ │   themes.py  │  5  from textual.app import App       │                    │ │
│ │   ayu.json   │  6                                    │ PS C:\>            │ │
│ └──────────────┴───────────────────────────────────────┴────────────────────┘ │
│ TRIX  main.py  Ln 6, Col 1  Python  main  ? Help                              │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

**Editor**
- 3-panel layout — File Tree, Editor, Terminal side by side
- Syntax highlighting for 20+ languages
- Open, edit, and save files with `Ctrl+S`
- Inline search with `Ctrl+F` — highlights matches, jump with `Enter`
- Global search across all files with `Ctrl+Shift+F`
- Create new files directly from the file tree with `N`

**Terminal**
- Fully embedded native PowerShell via winpty
- Real shell behavior — `cd`, `git`, `npm`, everything works
- Command history with `↑` `↓`
- Copy terminal output with `Ctrl+Shift+C`

**Layout**
- Resizable panels — drag the dividers to resize
- Toggle file tree with `Ctrl+B`
- Zen mode — fullscreen editor focus with `Ctrl+Shift+Z`
- Horizontal/vertical layout toggle with `Ctrl+Shift+H`

**Themes**
- Built-in Ayu Dark, Ayu Light, and Ayu Mirage themes
- Cycle themes with `Ctrl+T`

**Keyboard First**
- Full keyboard shortcut system
- Press `?` anytime to see all shortcuts
- Global shortcuts work from any panel

---

## Installation

**Via pip**
```bash
pip install trix-ide
```

**Via pipx (recommended — isolated environment)**
```bash
pipx install trix-ide
```

**From source**
```bash
git clone https://github.com/Zarl-prog/Trix-TUI.git
cd Trix-TUI
pip install -e .
```

---

## Requirements

- Python 3.10+
- Windows (PowerShell support via winpty)
- Terminal with Unicode support recommended

---

## Running TRIX

After installing via pip or pipx:
```bash
trix
```

From source:
```bash
python main.py
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save current file |
| `Ctrl+O` | Open folder |
| `Ctrl+N` | New file |
| `Ctrl+W` | Close current file |
| `Ctrl+F` | Search in file |
| `Ctrl+Shift+F` | Search across all files |
| `Ctrl+B` | Toggle file tree |
| `Ctrl+Shift+Z` | Zen mode |
| `Ctrl+Shift+H` | Toggle layout direction |
| `Ctrl+T` | Cycle themes |
| `Ctrl+1` | Focus file tree |
| `Ctrl+2` | Focus editor |
| `Ctrl+3` | Focus terminal |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+/` | Toggle comment |
| `Ctrl+D` | Duplicate line |
| `Ctrl+Q` | Quit |
| `?` | Show all shortcuts |

---

## Tech Stack

- [Textual](https://github.com/Textualize/textual) — TUI framework
- [winpty](https://github.com/rprichard/winpty) — Native PowerShell embedding
- [pyperclip](https://github.com/asweigart/pyperclip) — Clipboard support
- Ayu color theme by [dempfi](https://github.com/dempfi/ayu)

---

## Roadmap

- [ ] Status bar (line, column, git branch, file type)
- [ ] TRIX splash screen + branding
- [ ] File rename and delete operations
- [ ] Multi-file tabs
- [ ] Git integration (status indicators, commit, push, pull)
- [ ] Claude AI integration
- [ ] LSP support (autocomplete, go to definition)
- [ ] Linux and macOS support
- [ ] Plugin system

---

## Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you would like to change.

```bash
git clone https://github.com/Zarl-prog/Trix-TUI.git
cd Trix-TUI
pip install -e .
python main.py
```

---

## Author

Built by **Asim** — [GitHub](https://github.com/Zarl-prog)

---

## License

[MIT](https://choosealicense.com/licenses/mit/)

---

<div align="center">
  <sub>If you find TRIX useful, leave a ⭐ on GitHub — it helps a lot!</sub>
</div>
# TRIX

[![PyPI version](https://badge.fury.io/py/trix-ide.svg)](https://pypi.org/project/trix-ide/)

A terminal-native IDE built with Textual.
