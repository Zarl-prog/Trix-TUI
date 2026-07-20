Changing this whole repo to Python (Core Features) with python textual framework.
This might take some time... 
but dont miss the Output


vvv

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

<img width="1907" height="952" alt="Screenshot 2026-05-19 150836" src="https://github.com/user-attachments/assets/73dfffc6-8d39-4ff5-854e-28a06fa11fef" />

---

## Features

**Editor**
- 3-panel layout — File Tree, Editor, Terminal side by side
- Syntax highlighting for 20+ languages
- Open, edit, and save files with `Ctrl+S`
- Inline search with `Ctrl+F` — highlights matches, jump with `Enter`
- Global search across all files with `Ctrl+Shift+F`
- Create new files with `Ctrl+N`
- Rename files with `F2`
- Delete files with `Delete` (focus file tree first)
- Undo / Redo with `Ctrl+Z` / `Ctrl+Y`
- Duplicate line with `Ctrl+D`
- Toggle comment with `Ctrl+_`

**Git**
- Git History popup with `Ctrl+G` — floating modal overlay
- Two-column view: commit list on the left, commit details + files changed on the right
- Copy commit hash with `C`, navigate with `↑↓`, preview with `Enter`

**Terminal**
- Fully embedded native PowerShell via winpty
- Real shell behavior — `cd`, `git`, `npm`, everything works
- Command history with `↑` `↓`
- Copy terminal output with `Ctrl+Shift+C`

**Layout**
- Resizable panels — drag the dividers to resize
- Toggle file tree with `Ctrl+B`
- Zen mode — fullscreen editor focus with `Ctrl+\`
- Cycle panels with `Ctrl+]`

**Themes**
- Built-in Ayu Dark, Ayu Light, and Ayu Mirage themes
- Cycle themes with `Ctrl+T`
- Theme picker with `Ctrl+Shift+T`

**Status Bar**
- Live line and column indicator
- Current git branch
- Active theme name
- File language detection

**Keyboard First**
- Full keyboard shortcut system
- Press `F1` anytime to see all shortcuts
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
| `Ctrl+\` | Zen mode |
| `Ctrl+]` | Cycle panels |
| `Ctrl+T` | Cycle themes |
| `Ctrl+Shift+T` | Theme picker |
| `Ctrl+G` | Git History |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+A` | Select all |
| `Ctrl+_` | Toggle comment |
| `Ctrl+D` | Duplicate line |
| `Ctrl+R` | Reload file tree |
| `F2` | Rename file |
| `Delete` | Delete file (focus file tree first) |
| `Ctrl+Q` | Quit |
| `F1` | Show all shortcuts |

---

## Tech Stack

- [Textual](https://github.com/Textualize/textual) — TUI framework
- [winpty](https://github.com/rprichard/winpty) — Native PowerShell embedding
- [pyperclip](https://github.com/asweigart/pyperclip) — Clipboard support
- Ayu color theme by [dempfi](https://github.com/dempfi/ayu)

---

## Roadmap

- [x] Status bar (line, column, git branch, file type)
- [x] TRIX splash screen + branding
- [x] File rename and delete operations
- [x] Git History popup (commit list, diff preview, copy hash)
- [x] Theme picker with live preview
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


A terminal-native IDE built with Textual.
