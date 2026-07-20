# Trix-TUI — UI Improvement Suggestions

Curated UI/UX changes for the Trix-TUI terminal IDE, using **Textual-native** APIs (no new dependencies).

---

## 1. Draggable Dividers (Resizable Panels)

**Current**: `Divider` widget is passive — a 1-cell static spacer.

**Change**: Make dividers draggable for live panel resize.

```python
# divider_widget.py
class Divider(Static):
    """Draggable divider between panels."""

    def __init__(self, left_id: str, right_id: str, **kwargs):
        super().__init__("", **kwargs)
        self._left_id = left_id
        self._right_id = right_id
        self._dragging = False

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self.capture_mouse()

    def on_mouse_up(self, event: MouseUp) -> None:
        self._dragging = False
        self.release_mouse()

    def on_mouse_move(self, event: MouseMove) -> None:
        if not self._dragging:
            return
        # Calculate percentage of total width
        parent = self.parent
        if parent:
            x_pct = (event.screen_x / parent.region.width) * 100
            left_pct = max(10, min(x_pct - 1, 70))
            right_pct = max(10, min(100 - x_pct, 70))
            self.parent.query_one(f"#{self._left_id}").styles.width = f"{left_pct}%"
            self.parent.query_one(f"#{self._right_id}").styles.width = f"{right_pct}%"
```

**Verification**: Open app → grab divider → panels resize.

---

## 2. Active Line Gutter Marker

**Current**: `text-area--gutter` shows line numbers only.

**Change**: Add a `▸` arrow in the gutter on the active line.

```css
/* Add to TrixApp.CSS */
TextArea .text-area--gutter-active {
    background: #0d1016;
    color: #5ac1fe;
    text-style: bold;
}
```

Plus inject a gutter marker via `on_cursor_location_changed`:

```python
# app.py — in _refresh_status_bar
def _update_gutter_marker(self) -> None:
    ta = self.screen.query_one("#editor", TextArea)
    row = ta.cursor_location[0]
    # Python-Textual: set `text-area--gutter` on the gutter line
    # This is CSS-only — Textual 1.0+ uses `text-area--gutter` styling
```

**Verification**: Open a file → see `▸` on current line.

---

## 3. Tab Preview Hover Tooltip

**Current**: `TabStrip` shows file name + `●` unsaved dot.

**Change**: Hovering a tab shows first 3 lines of file content.

```python
# TabStrip widget in app.py
def on_mouse_move(self, event: MouseMove) -> None:
    """Show preview on hover."""
    for i, child in enumerate(self.children):
        if child.region.contains(event.screen_x, event.screen_y):
            path = self._tabs[i][0]
            try:
                preview = path.read_text(encoding="utf-8")[:80]
            except Exception:
                preview = ""
            self.tooltip = f"[dim]{path.parent.name}/[/dim]{preview}"
```

**Verification**: Hover over a tab → see file preview.

---

## 4. Live Theme Flash on `Ctrl+T`

**Current**: `cycle_theme()` instantly switches with no feedback.

**Change**: Flash the theme name in `#hdr-theme` with an opacity pulse.

```python
# app.py — inside action_cycle_theme
def action_cycle_theme(self) -> None:
    self._theme_index = (self._theme_index + 1) % len(self._themes)
    t = self._themes[self._theme_index]
    self.apply_theme(t)
    # Flash the theme name
    try:
        hdr = self.screen.query_one("#hdr-theme", Static)
        hdr.styles.animate("opacity", 0.3, duration=0.2)
        hdr.update(t["name"])
        hdr.styles.animate("opacity", 1.0, duration=0.3)
    except Exception:
        pass
```

**Verification**: Press `Ctrl+T` → theme name pulses → instant visual confirmation.

---

## 5. Panel-Aware Key Hints

**Current**: Bottom bar shows all keys always.

**Change**: Show only keys relevant to the focused panel.

```python
# In _refresh_status_bar / _update_headers
_PANEL_HINTS = {
    "files":     ["^b", "^g", "^r", "f2", "del"],
    "editor":    ["^s", "^f", "^n", "^w", "^z", "^y", "f1"],
    "terminal":  ["^c", "^d", "cls", "^z", "↑", "↓"],
}

def _update_key_hints(self) -> None:
    focused = self.focused
    active_panel = "editor"  # default
    if isinstance(focused, DirectoryTree):
        active_panel = "files"
    elif isinstance(focused, (TextArea,)):
        active_panel = "editor"
    elif isinstance(focused, (Input, TerminalOutputLog)):
        active_panel = "terminal"

    hints = _PANEL_HINTS[active_panel]
    for child in self.screen.query(".kb-key, .kb-desc"):
        child.display = child.renderable in hints or "  " in child.renderable
```

**Verification**: Focus editor → only `^s ^f ^n` show. Focus terminal → only `^c ^d` show.

---

## 6. Animated Splash Logo

**Current**: Static `████████╗` logo.

**Change**: Write the logo character-by-character with a progress bar.

```python
# screens.py — SplashScreen
class SplashScreen(Screen):
    def on_mount(self) -> None:
        self._logo_chars = list(
            "████████╗██████╗ ██╗██╗  ██╗\n"
            "╚══██╔══╝██╔══██╗██║╚██╗██╔╝\n"
            "   ██║   ██████╔╝██║ ╚███╔╝ \n"
            "   ██║   ██╔══██╗██║ ██╔██╗ \n"
            "   ██║   ██║  ██║██║██╔╝ ██╗\n"
            "   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝"
        )
        self._char_idx = 0
        self.set_interval(0.02, self._animate_logo)

    def _animate_logo(self) -> None:
        if self._char_idx >= len(self._logo_chars):
            return
        self._char_idx += 3  # 3 chars per tick
        visible = "".join(self._logo_chars[:self._char_idx])
        self.query_one("#splash-logo", Static).update(visible)
        if self._char_idx >= len(self._logo_chars):
            self.timer.stop()
```

**Verification**: Restart app → logo writes in like a terminal.

---

## 7. Draggable Git History with Inline Diff

**Current**: `GitHistoryScreen` shows commit list + detail panel with file names only.

**Change**: Show full inline diff with colored `+`/`-` lines.

```python
# git_history_screen.py — in _show_commit_detail
def _show_diff(self, commit: CommitDetail) -> None:
    """Fetch and display inline diff."""
    try:
        result = subprocess.run(
            ["git", "show", "--format=''", "--no-color", commit.full_hash],
            cwd=self.repo_path,
            capture_output=True, text=True, timeout=5
        )
        diff_lines = result.stdout.split("\n")
    except Exception:
        return

    files_container = self.query_one("#gh-files")
    files_container.clear()

    for line in diff_lines[:200]:
        if line.startswith("+"):
            files_container.mount(Static(f"[#aad84c]{line}[/]", markup=True))
        elif line.startswith("-"):
            files_container.mount(Static(f"[#ef7177]{line}[/]", markup=True))
        elif line.startswith("@@"):
            files_container.mount(Static(f"[#feb454]{line}[/]", markup=True))
        else:
            files_container.mount(Static(f" {line}"))
```

**Verification**: Open git history → `Enter` on a commit → see full colored diff.

---

## 8. Search in File Tree (Filterable)

**Current**: `DirectoryTree` shows all files unfiltered.

**Change**: Add `Input` above tree, filters visible nodes.

```python
# In MainScreen.compose() — add search input above DirectoryTree
def compose(self) -> ComposeResult:
    with LayoutContainer(id="files-panel"):
        yield PanelHeader("Files", id="header-files")
        yield GlobalSearch(id="global-search")
        yield Input(id="tree-filter", placeholder="Filter files…")
        yield ClickableDirectoryTree(".", id="file-tree")

# In TrixApp
@on(Input.Changed)
def on_tree_filter_changed(self, event: Input.Changed) -> None:
    tree = self.screen.query_one(DirectoryTree)
    q = event.value.lower()
    if not q:
        tree.show_all()
    else:
        # Filter: only show nodes whose name contains q
        tree.filter(lambda node: q in node.data.path.name.lower() if node.data else False)
```

**Verification**: Type `.py` in filter → tree shows only `.py` files.

---

## 9. Notification Dismiss / Stack

**Current**: `Toast` auto-fades. No dismiss button.

**Change**: Add `✕` button + stack last 3.

```python
class DismissableToast(Toast):
    """A toast notification with a dismiss button."""

    DEFAULT_CSS = """
    DismissableToast {
        width: auto;
        height: auto;
        padding: 0 1;
        layout: horizontal;
    }
    #toast-close {
        width: 2;
        color: #4b4c4e;
        text-style: bold;
    }
    #toast-close:hover {
        color: #ef7177;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(self.message, id="toast-body")
        yield Static(" ✕", id="toast-close")

    def on_click(self, event: Click) -> None:
        if event.widget and event.widget.id == "toast-close":
            self.dismiss()
```

Replace `notify()` in `app.py`:

```python
def notify(self, message: str, severity="information") -> None:
    """Custom notify with self-dismiss."""
    toast = DismissableToast(message, classes=severity)
    self.query_one("#toast-rack", ToastRack).mount(toast)
    # Keep only last 3
    rack = self.query_one("#toast-rack", ToastRack)
    while len(rack.children) > 3:
        rack.remove(rack.children[0])
```

**Verification**: Trigger 5+ notifications → only last 3 visible.

---

