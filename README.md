<div align="center">

```
████████╗██████╗ ██╗██╗  ██╗
╚══██╔══╝██╔══██╗██║╚██╗██╔╝
   ██║   ██████╔╝██║ ╚███╔╝
   ██║   ██╔══██╗██║ ██╔██╗
   ██║   ██║  ██║██║██╔╝ ██╗
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
```

<h3>Your terminal. Your IDE. No compromises.</h3>

[![PyPI version](https://img.shields.io/pypi/v/trix-ide?color=5ac1fe&style=flat-square)](https://pypi.org/project/trix-ide/)
[![Python version](https://img.shields.io/pypi/pyversions/trix-ide?color=aad84c&style=flat-square)](https://python.org)
[![License](https://img.shields.io/pypi/l/trix-ide?color=686868&style=flat-square)](LICENSE)
[![Windows](https://img.shields.io/badge/win-10%2B-39bae5?style=flat-square)](#)
[![GitHub stars](https://img.shields.io/github/stars/Zarl-prog/Trix-TUI?color=e6b450&style=flat-square)](https://github.com/Zarl-prog/Trix-TUI/stargazers)

[![Install](https://img.shields.io/badge/-INSTALL-5ac1fe?style=for-the-badge)](https://pypi.org/project/trix-ide/)
[![Docs](https://img.shields.io/badge/-DOCS-39bae5?style=for-the-badge)](#)
[![Issues](https://img.shields.io/badge/-ISSUES-ef7177?style=for-the-badge)](https://github.com/Zarl-prog/Trix-TUI/issues)

</div>

---

## Preview

```
┌─────────────────────────────────────────────────────────────┐
│ ✦ TRIX              /home/user/project          Ayu Dark   │
├──────────────┬──────────────────────────────────────────────┤
│ ── Explorer ─┴─ Editor ─────────────────────────────────── │
│ 📂 .         │ #!/usr/bin/env python3                      │
│ ├── src/     │                                              │
│ │ ├── main. ▶│ import sys                                  │
│ │ ├── util.  │ from pathlib import Path                    │
│ │ └── trix.  │                                              │
│ ├── tests/   │ def main():                                 │
│ ├── README.m │     print("Hello, Trix!")                   │
│ ├── pyprojec │                                              │
│ └── .git/    │ Ln 5  Col 1   Python            🌿 main     │
├──────────────┴──────────────────────────────────────────────┤
│ ^Q Quit  F1 Help  ^G Git  ^T Theme  ^B Files  ^O Open  ^S │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

<div align="center">

<table>
<tr>
<td align="center" width="33%"><b>📝 Editor</b></td>
<td align="center" width="33%"><b>📁 File Management</b></td>
<td align="center" width="33%"><b>🎨 Terminal + UX</b></td>
</tr>
<tr>
<td valign="top">

▸ Syntax highlighting — 20+ languages, tree-sitter powered  
▸ Undo / Redo — `Ctrl+Z` / `Ctrl+Y`  
▸ Search in file — real-time matches, `↑↓` navigate  
▸ Save — `Ctrl+S`, dirty dot (●) indicator  
▸ Line numbers — gutter with active line highlight  
▸ Toggle comment — `Ctrl+_` on current line  
▸ Duplicate line — `Ctrl+D`  
▸ Select all — `Ctrl+A`  
▸ Copy selection — `Ctrl+Shift+C`

</td>
<td valign="top">

▸ File tree — Nerd Font icons for 130+ file types  
▸ Open folder — `Ctrl+O`, full directory navigation  
▸ Create file — dialog with auto parent dir creation  
▸ Rename — `F2`, updates open tabs automatically  
▸ Delete — `Del` with confirmation dialog  
▸ Multi-tab — `Ctrl+Tab` / `Ctrl+Shift+Tab` nav  
▸ Close tab — `Ctrl+W`, dirty-file confirmation  
▸ Git status badges — `M` `A` `D` `??` color-coded  
▸ Reload tree — `Ctrl+R`

</td>
<td valign="top">

▸ 10 themes — Ayu, Dracula, One Dark, Tokyo Night, Catppuccin, Nord, Everforest, Midnight Blue  
▸ Zen mode — `Ctrl+\`, full-screen focus  
▸ Click to focus — click any panel, it gets keyboard focus  
▸ Help screen — `F1`, all shortcuts listed  
▸ Bottom bar — clickable shortcuts with key hints  
▸ Splash screen — animated logo fill, loading status  
▸ Command palette — `Ctrl+P`, search any action  
▸ Toast notifications — info, warning, error  
▸ Theme picker — `Ctrl+Shift+T`, live preview

</td>
</tr>
</table>

</div>

---

## Installation

<table>
<tr><th>Method</th><th>Run this</th><th></th></tr>
<tr><td><b>pip</b><br><sub>recommended</sub></td>
<td>

```
pip install trix-ide
```

</td>
<td><a href="https://pypi.org/project/trix-ide/"><img src="https://img.shields.io/pypi/v/trix-ide?color=5ac1fe&style=flat-square&label="></a></td></tr>
<tr><td><b>pipx</b></td>
<td>

```
pipx install trix-ide
```

</td>
<td><a href="https://pypi.org/project/trix-ide/"><img src="https://img.shields.io/pypi/v/trix-ide?color=5ac1fe&style=flat-square&label="></a></td></tr>
<tr><td><b>uv</b></td>
<td>

```
uv tool install trix-ide
```

</td>
<td><a href="https://pypi.org/project/trix-ide/"><img src="https://img.shields.io/pypi/v/trix-ide?color=5ac1fe&style=flat-square&label="></a></td></tr>
<tr><td><b>npm</b></td>
<td>

```
npm install -g trix-ide
```

</td>
<td><a href="https://www.npmjs.com/package/trix-ide"><img src="https://img.shields.io/npm/v/trix-ide?color=39bae5&style=flat-square&label="></a></td></tr>
<tr><td><b>Homebrew</b></td>
<td>

```
brew tap Zarl-prog/trix https://github.com/Zarl-prog/Trix-TUI
brew install Zarl-prog/trix/trix-ide
```

</td>
<td><a href="Formula/trix-ide.rb"><img src="https://img.shields.io/badge/-formula-aad84c?style=flat-square"></a></td></tr>
</table>

Run `trix` to start.

---

## Keyboard Shortcuts

<table>
<tr>
<th colspan="2">Navigation</th>
</tr>
<tr><td><code>Ctrl+]</code></td><td>Cycle panels (file tree ↔ editor)</td></tr>
<tr><td><code>Ctrl+Tab</code></td><td>Next tab</td></tr>
<tr><td><code>Ctrl+Shift+Tab</code></td><td>Previous tab</td></tr>
<tr><td><code>Ctrl+B</code></td><td>Toggle file tree visibility</td></tr>
<tr><td><code>Ctrl+\</code></td><td>Zen mode — hide all panels</td></tr>
<tr>
<th colspan="2">File</th>
</tr>
<tr><td><code>Ctrl+N</code></td><td>New file</td></tr>
<tr><td><code>Ctrl+S</code></td><td>Save current file</td></tr>
<tr><td><code>Ctrl+W</code></td><td>Close current tab</td></tr>
<tr><td><code>Ctrl+O</code></td><td>Open folder</td></tr>
<tr><td><code>F2</code></td><td>Rename file</td></tr>
<tr><td><code>Del</code></td><td>Delete file</td></tr>
<tr>
<th colspan="2">Editor</th>
</tr>
<tr><td><code>Ctrl+Z</code></td><td>Undo</td></tr>
<tr><td><code>Ctrl+Y</code></td><td>Redo</td></tr>
<tr><td><code>Ctrl+A</code></td><td>Select all</td></tr>
<tr><td><code>Ctrl+_</code></td><td>Toggle comment on current line</td></tr>
<tr><td><code>Ctrl+D</code></td><td>Duplicate current line</td></tr>
<tr><td><code>Ctrl+Shift+C</code></td><td>Copy selected text</td></tr>
<tr>
<th colspan="2">Search</th>
</tr>
<tr><td><code>Ctrl+F</code></td><td>Search within current file</td></tr>
<tr><td><code>Ctrl+Shift+F</code></td><td>Search across all files in tree</td></tr>
<tr><td><code>Ctrl+P</code></td><td>Command palette</td></tr>
<tr>
<th colspan="2">Git & Theme</th>
</tr>
<tr><td><code>Ctrl+G</code></td><td>Open Git menu (commit, push, history)</td></tr>
<tr><td><code>Ctrl+T</code></td><td>Cycle through themes</td></tr>
<tr><td><code>Ctrl+Shift+T</code></td><td>Theme picker dialog</td></tr>
<tr><td><code>Ctrl+R</code></td><td>Reload file tree</td></tr>
<tr>
<th colspan="2">General</th>
</tr>
<tr><td><code>Ctrl+Q</code></td><td>Quit (with unsaved confirmation)</td></tr>
<tr><td><code>F1</code></td><td>Show help screen</td></tr>
<tr><td><code>Esc</code></td><td>Close any dialog</td></tr>
</table>

---

## Project Structure

```
app.py              # Entry point — run()
main.py             # Main app, screens, widgets, bindings, actions
screens.py          # All modal dialogs: Help, Confirm, New/Rename,
                    # Folder picker, Splash, Theme picker
themes.py           # 10 theme definitions + dynamic CSS builders
search_widget.py    # Inline editor search + global file search
git_menu_screen.py  # Full Git UI: commit, push, history accordion
syntax_setup.py     # Extra tree-sitter language registration
pyproject.toml      # Package metadata, dependencies, entry point
```

---

## Tech Stack

[![Textual](https://img.shields.io/badge/Textual-0.80%2B-5ac1fe?style=flat-square)](https://textual.textualize.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-aad84c?style=flat-square)](https://python.org)
[![Theme](https://img.shields.io/badge/Themes-Ayu%20%7C%20Dracula%20%7C%20Nord-39bae5?style=flat-square)](themes.py)
[![License](https://img.shields.io/badge/License-MIT-686868?style=flat-square)](LICENSE)

**Textual** — Terminal app framework. Powers layout, event system, CSS engine, and the command palette.

**Python** — Cross-platform runtime, zero-compile install, launches in under a second.

**Tree-Sitter** — Incremental parsing for accurate syntax highlighting across 20+ languages.

**Rich** — Terminal styling for labels, badges, and markdown rendering in dialogs.

---

## Roadmap

<table>
<tr><td>☑ In-editor search with match navigation</td><td>☐ Language Server Protocol (LSP) integration</td></tr>
<tr><td>☑ Global file search across project</td><td>☐ Claude AI code assistant</td></tr>
<tr><td>☑ Git integration (status, commit, push, history)</td><td>☐ Multi-root workspaces</td></tr>
<tr><td>☑ 10 dark themes with syntax highlighting</td><td>☐ Built-in terminal panel</td></tr>
<tr><td>☑ Multi-tab file management with dirty tracking</td><td>☐ Plugin system</td></tr>
<tr><td>☑ Splash screen, welcome panel, recent files</td><td>☐ macOS / Linux native packages</td></tr>
<tr><td>☑ Nerd Font file icons for 130+ types</td><td>☐ Configurable key bindings</td></tr>
<tr><td>☑ Zen mode, command palette, toast notifications</td><td>☐ File watcher for external changes</td></tr>
</table>

---

## Contributing

```
git clone https://github.com/Zarl-prog/Trix-TUI
pip install -e .
trix
```

Submit a PR at [github.com/Zarl-prog/Trix-TUI](https://github.com/Zarl-prog/Trix-TUI).

---

<div align="center">

Built with ❤️ by [Asim](https://github.com/Zarl-prog) · Give it a ⭐ if you find it useful

[GitHub](https://github.com/Zarl-prog/Trix-TUI) · [PyPI](https://pypi.org/project/trix-ide/) · [Issues](https://github.com/Zarl-prog/Trix-TUI/issues)

</div>
