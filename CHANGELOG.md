# Changelog

## [0.2.0] - 2026-05-19

### Added
- **Git History popup** (`Ctrl+G`) — floating modal overlay with two-column layout: scrollable commit list on the left, commit details and files changed on the right
- **Theme picker** (`Ctrl+Shift+T`) — live preview theme selector
- **Status bar** — live line/column indicator, current git branch, active theme name, file language detection
- **Splash screen** — animated TRIX branding on startup
- **File rename** (`F2`) — prompts for new name, renames on disk, refreshes tree
- **File delete** (`Delete` with file tree focused) — confirmation dialog before deleting
- **Zen mode** (`Ctrl+\`) — fullscreen editor, hides all other panels
- **Panel cycling** (`Ctrl+]`) — cycle focus between Files → Editor → Terminal
- **Duplicate line** (`Ctrl+D`)
- **Toggle comment** (`Ctrl+_`)
- **Reload file tree** (`Ctrl+R`)
- **Select all** (`Ctrl+A`)
- **Help screen** (`F1`) — full keyboard shortcut reference

### Fixed
- All `var(--*)` CSS variables replaced with literal hex values (Textual does not support CSS custom properties)
- File rename and delete now work from file tree selection even when no file is open in the editor
- Git History `Enter` key now correctly triggers commit preview via `ListView.Selected` event
- Timezone-aware datetime comparison in git log time formatting
- Git file stat parsing switched from `--stat` to `--numstat` for accurate `+/-` counts
- Duplicate widget IDs in git history file list

## [0.1.0] - Initial release

- 3-panel layout: File Tree, Editor, Terminal
- Syntax highlighting for 20+ languages
- Embedded PowerShell terminal via winpty
- Inline search (`Ctrl+F`) and global search (`Ctrl+Shift+F`)
- Ayu Dark, Ayu Light, Ayu Mirage themes (`Ctrl+T`)
- Resizable panels via drag dividers
