# TRIX TUI — Detailed Technical Documentation

## Project Overview

**TRIX** is a lightweight, terminal-native IDE built entirely inside your terminal using Python and the **Textual** TUI framework. No Electron, no browser, no bloat — just a fast, keyboard-driven development environment that lives where developers actually work.

**Version:** 0.2.0  
**Author:** Asim Junaidi  
**License:** MIT  
**Python:** 3.10+  
**Platform:** Windows (primary), Linux/macOS (planned)  
**Framework:** Textual ≥ 0.80.0  
**Entry Point:** `trix` (via `pip install trix-ide` or `pipx install trix-ide`)

---

## Architecture Overview

### High-Level Structure

```
trix-ide/
├── main.py                 # Main application class (TrixApp) - 1400+ lines
├── app.py                  # Entry point wrapper
├── screens.py              # Modal screens (Help, Confirm, NewFile, Rename, FolderPicker, Splash, ThemePicker)
├── themes.py               # Theme definitions (Ayu Dark/Light/Mirage + 5 famous themes)
├── themes_loader.py        # Ayu JSON theme loader (ayu.json)
├── divider_widget.py       # Draggable panel divider
├── search_widget.py        # EditorSearch (Ctrl+F) + GlobalSearch (Ctrl+Shift+F)
├── git_history_screen.py   # Git History modal (Ctrl+G)
├── terminal_widget.py      # Embedded PowerShell terminal (winpty)
├── main.py (legacy)        # Legacy main file (being phased out)
├── ayu.json               # Ayu theme definitions
├── pyproject.toml          # Package configuration
└── README.md               # User-facing documentation
```

### Core Application Class: `TrixApp` (main.py:661)

The main application class inherits from `textual.app.App` and manages:

- **State Management**: File tabs, unsaved changes, active theme, panel visibility
- **Theme System**: 8 built-in themes with persistence (~/.trix/config.json)
- **Tab System**: Multi-file tab strip with unsaved indicators and close buttons
- **Panel Layout**: 3-panel layout (File Tree | Editor | Terminal) with draggable dividers
- **Git Integration**: Status indicators in file tree, Git History modal
- **Search**: In-file (Ctrl+F) + Global project search (Ctrl+Shift+F)
- **Terminal**: Embedded PowerShell via winpty
- **Splash Screen**: Animated 2-second splash on startup

---

## Detailed Module Breakdown

### 1. main.py — Core Application Logic (~1400 lines)

#### Key Classes

**`TrixApp`** (line 661) — Main application class

**State Management:**
```python
_current_file: Path | None           # Currently active file
_has_changes: bool                   # Unsaved changes flag
_open_files: list[Path]              # All open tabs
_open_files_dirty: dict[Path, bool]  # Unsaved state per file
_open_files_content: dict[Path, str] # Cached content per file
_active_tab: int                     # Active tab index
_theme_index: int                    # Current theme index
_filetree_visible: bool              # File tree visibility
_zen_mode: bool                      # Zen mode state
```

**Theme System (lines 878-936):**
- 8 built-in themes: Ayu Dark, Ayu Light, Ayu Mirage, Dracula, Nord, Monokai, Gruvbox Dark, One Dark, Tokyo Night
- Registered as Textual themes with custom CSS properties
- Persisted to `~/.trix/config.json` with theme name
- Live preview in Theme Picker (Ctrl+Shift+T)
- Cycle themes with Ctrl+T

**Tab Management (lines 940-1018):**
- `_open_in_tab(path, content)` — Open file in tab, reuse if already open
- `_switch_tab(idx)` — Switch tabs, preserve editor state
- `_close_tab(idx)` — Close tab with unsaved changes confirmation
- `TabStrip` widget (line 403) — Horizontal tab bar with close buttons, unsaved indicators

**Panel Layout (CSS lines 664-833):**
```
┌─────────────────────────────────────────────────────────────┐
│ Header: TRIX | folder-name | theme-name                     │
├─────────────────────────────────────────────────────────────┤
│ Files Panel (20%) │ Divider │ Editor Panel (2fr)            │
│  ┌─────────────┐  │   │    ┌─────────────────────────┐      │
│  │ GlobalSearch │  │   │    │ TabStrip                │      │
│  ├─────────────┤  │   │    ├─────────────────────────┤      │
│  │ DirectoryTree│  │   │    │ EditorSearch (Ctrl+F)   │      │
│  │ (Clickable)  │  │   │    ├─────────────────────────┤      │
│  └─────────────┘  │   │    │ ClickableTextArea       │      │
│                   │   │    │ WelcomePanel (empty)    │      │
└───────────────────┴───┴────┴─────────────────────────┘
│ Bottom Bar: [^Q Quit] [F1 Help] [^G Git] [^T Theme] [^B Files] [^O Open] | Ln 1, Col 1 | py | 🌿 main | ● unsaved │
└─────────────────────────────────────────────────────────────┘
```

**Key Bindings (lines 835-852):**
| Binding | Action | Description |
|---------|--------|-------------|
| Ctrl+Q | quit_app | Quit (confirms if unsaved) |
| Ctrl+S | save | Save current file |
| Ctrl+N | new_file | New file |
| Ctrl+W | close_file | Close current tab |
| Ctrl+O | open_folder | Open folder picker |
| Ctrl+R | reload_tree | Reload file tree |
| Ctrl+F | search | In-file search |
| Ctrl+Shift+F | global_search | Global project search |
| Ctrl+T | cycle_theme | Cycle themes |
| Ctrl+Shift+T | pick_theme | Theme picker |
| Ctrl+Shift+C | copy_selection | Copy selection |
| Ctrl+B | toggle_filetree | Toggle file tree |
| Ctrl+\ | zen_mode | Zen mode (editor only) |
| Ctrl+G | show_git_history | Git history modal |
| F2 | rename_file | Rename file |
| F1 | show_help | Help screen |
| Ctrl+] | _cycle_panels | Cycle panels (Files ↔ Editor) |
| Delete | delete_file | Delete file (tree focused) |
| Ctrl+Z/Y/A/_/D | Editor shortcuts | Undo/Redo/Select All/Comment/Duplicate |

**Mouse Handling (lines 1041-1087):**
- Bottom bar items clickable (Quit, Help, Git, Theme, Files, Open)
- Click any panel to focus it
- Coordinate-based fallback for clicks on headers/padding

**Git Integration (lines 31-40, 179-206, 246-255):**
- `_git_branch()` — Get current branch for status bar
- `ClickableDirectoryTree` caches `git status --porcelain` for file status badges
- File tree shows git status colors: Modified (orange), Untracked (green), Deleted (red), Added (green)
- Git status refreshed on tree reload/path change

**Configuration Persistence (lines 43-90):**
- Config file: `~/.trix/config.json`
- Stores: theme name, recent files (max 15)
- Auto-saves on theme change, file open

---

### 2. screens.py — Modal Screens (443 lines)

All screens inherit from `textual.screen.Screen` with custom CSS registered via `register_css_template()`.

| Screen | Trigger | Purpose |
|--------|---------|---------|
| `SplashScreen` | App startup | Animated 2s splash with progress bar |
| `HelpScreen` | F1 | Keyboard shortcuts reference |
| `ConfirmScreen` | Quit/Delete/Close unsaved | Yes/No confirmation dialog |
| `NewFileScreen` | Ctrl+N | Prompt for new filename |
| `RenameScreen` | F2 | Rename selected file |
| `FolderPicker` | Ctrl+O | Enter folder path |
| `ThemePickerScreen` | Ctrl+Shift+T | Theme selector with live preview |

**ThemePickerScreen** (lines 392-442) — Notable for live theme preview on highlight

---

### 3. themes.py — Theme Definitions (443 lines)

**Ayu Themes (from ayu.json):**
- Ayu Dark (default)
- Ayu Light
- Ayu Mirage

**Famous Themes (FAMOUS_THEMES, lines 4-100):**
- Dracula
- Nord
- Monokai
- Gruvbox Dark
- One Dark
- Tokyo Night

**Theme Schema (22 properties):**
```python
{
    "name": str,
    "background": str,      # Main background
    "surface": str,         # Elevated surfaces
    "panel": str,           # Panel backgrounds
    "border": str,          # Default borders
    "border_focused": str,  # Focused panel borders
    "text": str,            # Primary text
    "text_muted": str,      # Secondary text
    "accent": str,          # Primary accent (links, highlights)
    "accent_alt": str,      # Secondary accent
    "success": str,         # Success/green
    "warning": str,         # Warning/orange
    "error": str,           # Error/red
    "line_number": str,     # Editor line numbers
    "cursor_line": str,     # Current line highlight
    "scrollbar": str,       # Scrollbar track
    "scrollbar_thumb": str, # Scrollbar thumb
}
```

**CSS Template Registration (lines 102-143):**
- `register_css_template(name, css)` — Registers CSS templates for screens
- Templates: `help_screen`, `confirm_screen`, `new_file_screen`, `rename_screen`, `folder_picker`, `splash_screen`, `theme_picker_screen`, `divider`, `global_search`, `editor_search`

---

### 4. themes_loader.py — Ayu JSON Loader (45 lines)

Loads `ayu.json` (38KB) containing full Ayu theme specifications with Textual-compatible CSS variable mappings. Used to register Ayu themes at runtime.

---

### 5. divider_widget.py — Draggable Divider (51 lines)

**`Divider` class** (line 18):
- 1-cell wide vertical divider
- Mouse drag to resize adjacent panels
- Calculates percentage widths from mouse position
- Min 10%, max 70% per panel
- Hover effect (accent color)

---

### 6. search_widget.py — Search Widgets (314 lines)

#### `EditorSearch` (lines 1-126) — Ctrl+F Inline Search
- Docked above editor, slides down on open
- Input + match counter + prev/next/close buttons
- Real-time highlighting via `TextArea.find()`
- Enter = next match, Shift+Enter = previous, Escape = close

#### `GlobalSearch` (lines 128-314) — Ctrl+Shift+F Project Search
- Docked in file tree panel
- Recursive file search from project root
- Results list: `path:line  preview`
- Click/Enter opens file at match line
- Limits to 200 results
- Escape to close

---

### 7. git_history_screen.py — Git History Modal (421 lines)

**`GitHistoryScreen`** — ModalScreen (Ctrl+G)

**Features:**
- Two-column layout: Commit list (40%) | Commit details (60%)
- Loads last 50 commits: `git log --format=%H|%h|%s|%an|%ae|%ai -n 50`
- Commit list shows: ● hash | message | author · time-ago
- Detail panel shows: Full hash, Author, Date, Message, Files changed (+lines/-lines)
- **Bindings:**
  - ↑↓ — Navigate commits
  - Enter — Show detail
  - C — Copy full hash to clipboard
  - O — List changed files (notify)
  - Esc — Close

**`CommitDetail` class** (line 149) — Lazy-loads file stats via `git show --numstat`

---

### 8. terminal_widget.py — Embedded Terminal (Planned/Partial)

Referenced in pyproject.toml but not fully implemented in main.py yet. Uses `pywinpty` for native PowerShell embedding on Windows.

---

### 9. Custom Widgets (defined in main.py)

| Widget | Line | Purpose |
|--------|------|---------|
| `ClickableTextArea` | 156 | TextArea that focuses on click |
| `ClickableDirectoryTree` | 166 | DirectoryTree with git status, click focus, file icons |
| `PanelHeader` | 359 | Harlequin-style header: `── Title ────────` |
| `TabStrip` | 403 | Horizontal tab bar with close buttons, unsaved dots |
| `WelcomePanel` | 487 | Welcome screen with recent files list |
| `LayoutContainer` | 147 | Focus-passing container for layout |
| `HorizontalContainer` | 139 | Focus-passing horizontal container |

**ClickableDirectoryTree Highlights:**
- File type icons (300+ extensions mapped)
- Git status badges and colors
- Custom folder icons (expanded/collapsed)
- Special file name icons (Dockerfile, Makefile, README, etc.)

---

## Data Flow & Key Workflows

### Opening a File
1. User clicks file in `DirectoryTree` → `on_directory_tree_file_selected`
2. Or selects from `WelcomePanel` recent files → `on_welcome_panel_file_clicked`
3. `_open_in_tab(path, content)` called
4. If already open → `_switch_tab(existing_index)`
5. Else → append to `_open_files`, cache content, `_switch_tab(new_index)`
6. `_switch_tab` saves current editor content, loads new file, updates tab strip, refreshes UI

### Saving a File
1. Ctrl+S → `action_save()`
2. Write editor text to `_current_file`
3. Clear `_has_changes` and dirty flag
4. Refresh git status in tree
5. `_refresh_ui()` updates tab strip and status bar

### Theme Switching
1. Ctrl+T / Ctrl+Shift+T → `action_cycle_theme()` / `action_pick_theme()`
2. `apply_theme(theme_dict)` called
3. Creates Textual `Theme` object, registers, sets `self.theme = slug`
4. Persists to `~/.trix/config.json`
5. Updates header theme name

### Git Status in File Tree
1. `ClickableDirectoryTree.on_mount()` → `_refresh_git_status()`
2. Runs `git status --porcelain -u` and `git rev-parse --show-toplevel`
3. Caches `{abs_path: status_code}` in class variable
4. `render_label()` applies colors/badges based on status code
5. Refreshes on `watch_path` (tree path change) and after file save

### Global Search
1. Ctrl+Shift+F → `action_global_search()` → `GlobalSearch.open()`
2. User types → `on_input_changed` → `_run_search(query)`
3. Walks project root, reads files, matches lines (case-insensitive)
4. Populates `ListView` with `path:line  preview`
5. Selection → loads file in editor, jumps to line, selects match, closes search

---

## Configuration & Persistence

### Config File: `~/.trix/config.json`
```json
{
  "theme": "Ayu Dark",
  "recent_files": ["/path/to/file1.py", "/path/to/file2.md"]
}
```

### Theme Registration
Themes registered at startup in `on_mount()` → `_register_all_themes()`. Each theme gets a Textual theme slug (lowercase, hyphenated).

---

## Keyboard Shortcuts Reference

| Shortcut | Action | Context |
|----------|--------|---------|
| **File Operations** |
| Ctrl+N | New File | Global |
| Ctrl+O | Open Folder | Global |
| Ctrl+S | Save File | Global |
| Ctrl+W | Close Tab | Global |
| F2 | Rename File | Tree focused |
| Delete | Delete File | Tree focused |
| Ctrl+R | Reload Tree | Global |
| **Editor** |
| Ctrl+Z | Undo | Editor focused |
| Ctrl+Y | Redo | Editor focused |
| Ctrl+A | Select All | Editor focused |
| Ctrl+_ | Toggle Comment | Editor focused |
| Ctrl+D | Duplicate Line | Editor focused |
| Ctrl+F | Search in File | Global |
| **Search** |
| Ctrl+Shift+F | Global Search | Global |
| Enter | Next Match | In search |
| Shift+Enter | Prev Match | In search |
| Escape | Close Search | In search |
| **Layout** |
| Ctrl+B | Toggle File Tree | Global |
| Ctrl+\ | Zen Mode | Global |
| Ctrl+] | Cycle Panels | Global |
| Click Panel | Focus Panel | Mouse |
| Drag Divider | Resize Panels | Mouse |
| **Git** |
| Ctrl+G | Git History | Global |
| ↑↓ | Navigate Commits | Git History |
| Enter | View Details | Git History |
| C | Copy Hash | Git History |
| O | List Files | Git History |
| **Themes** |
| Ctrl+T | Cycle Theme | Global |
| Ctrl+Shift+T | Theme Picker | Global |
| ↑↓ | Navigate Themes | Theme Picker |
| Enter | Select Theme | Theme Picker |
| **General** |
| F1 | Help | Global |
| Ctrl+Q | Quit | Global |
| Ctrl+Shift+C | Copy Selection | Global |

---

## Installation & Development

### Install from PyPI
```bash
pip install trix-ide
# or isolated
pipx install trix-ide
```

### Run from Source
```bash
git clone https://github.com/Zarl-prog/Trix-TUI.git
cd Trix-TUI
pip install -e .
python main.py
# or
trix
```

### Dependencies
```toml
dependencies = [
    "textual>=0.80.0",
    "pyperclip",
]
[project.optional-dependencies]
windows = ["pywinpty"]  # For embedded terminal
```

---

## Roadmap Status

| Feature | Status |
|---------|--------|
| Status bar (line, col, git branch, file type) | ✅ Done |
| TRIX splash screen + branding | ✅ Done |
| File rename and delete | ✅ Done |
| Git History popup | ✅ Done |
| Theme picker with live preview | ✅ Done |
| Multi-file tabs | ✅ Done |
| Git integration (status, commit, push, pull) | 🟡 Partial (status only) |
| Claude AI integration | ⬜ Planned |
| LSP support (autocomplete, go to definition) | ⬜ Planned |
| Linux/macOS support | ⬜ Planned |
| Plugin system | ⬜ Planned |

---

## Code Quality & Conventions

- **No type hints** in most of main.py (legacy), newer files use type hints
- **No docstrings** on most methods
- **CSS-in-Python**: All styling in `CSS = """..."""` class attributes
- **Message classes** for inter-widget communication (e.g., `TabStrip.TabClicked`)
- **@work decorator** for async operations (Textual workers)
- **push_screen_wait** for modal dialogs returning values
- **CSS templates** registered via `register_css_template()` for screens

---

## Known Limitations

1. **Windows-only terminal** (winpty/PowerShell)
2. **No LSP/autocomplete** — pure text editing
3. **No multi-tab terminal** — single embedded shell
4. **Git operations read-only** — no commit/push/pull UI yet
5. **No session persistence** — tabs not restored on restart
6. **Large file performance** — TextArea loads entire file into memory

---

## Extension Points

1. **Themes**: Add to `FAMOUS_THEMES` in themes.py or drop JSON in ayu.json format
2. **Commands**: Extend `TrixCommandProvider.COMMANDS` for command palette
3. **Key Bindings**: Add to `TrixApp.BINDINGS`
4. **File Icons**: Extend `_EXT_ICONS` / `_NAME_ICONS` in `ClickableDirectoryTree`
5. **Screens**: Add new `Screen` subclasses to screens.py
6. **Search**: Extend `GlobalSearch._run_search()` for ripgrep/rg integration

---

## File Map Quick Reference

| File | Lines | Purpose |
|------|-------|---------|
| main.py | ~1500 | Core app, UI, state, actions, widgets |
| app.py | 13 | Entry point wrapper |
| screens.py | 443 | Modal screens |
| themes.py | 443 | Theme definitions + CSS templates |
| themes_loader.py | 45 | Ayu JSON loader |
| divider_widget.py | 51 | Draggable panel divider |
| search_widget.py | 314 | In-file + global search |
| git_history_screen.py | 421 | Git history modal |
| terminal_widget.py | ~200 | Embedded terminal (partial) |
| ayu.json | ~1000 | Ayu theme definitions |
| pyproject.toml | 28 | Package config |

---

## Contributing

```bash
git clone https://github.com/Zarl-prog/Trix-TUI.git
cd Trix-TUI
pip install -e .
python main.py
```

PRs welcome. For major changes, open an issue first.

---

*Generated from source code analysis — TRIX TUI v0.2.0*