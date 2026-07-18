import subprocess
from datetime import datetime, timezone
from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static


GIT_HISTORY_CSS = """
GitHistoryScreen {
    align: center middle;
    background: rgba(0,0,0,0.82);
}

#git-popup {
    width: 88%;
    height: 85%;
    background: #141820;
    border: tall #5ac1fe;
    layout: vertical;
}

/* ── Header ── */
#gh-header {
    height: 3;
    dock: top;
    background: #0d1016;
    border-bottom: solid #1f2a3a;
    padding: 0 2;
    align: left middle;
}
#gh-title  { width: auto; color: #5ac1fe; text-style: bold; }
#gh-meta   { width: 1fr; content-align: right middle; color: #4b4c4e; }

/* ── Two-column body ── */
#gh-body {
    height: 1fr;
    layout: horizontal;
}

/* ── Left: commit list ── */
#gh-left {
    width: 42%;
    height: 100%;
    border-right: solid #1f2a3a;
}
#gh-commits {
    height: 1fr;
    background: #141820;
    scrollbar-color: #5ac1fe;
    scrollbar-size: 1 1;
}
#gh-commits > ListItem {
    height: auto;
    padding: 0;
    background: #141820;
    border-bottom: solid #1a1e26;
}
#gh-commits > ListItem:hover { background: #1a1f2b; }
#gh-commits > ListItem.--highlight {
    background: #1a2540;
    border-left: tall #5ac1fe;
}

.gh-row        { height: auto; padding: 1 2; }
.gh-row-top    { height: auto; layout: horizontal; }
.gh-dot        { width: 2; color: #5ac1fe; }
.gh-hash       { width: 8; color: #e6b450; text-style: bold; }
.gh-msg        { width: 1fr; color: #bfbdb6; padding: 0 1; }
.gh-row-bottom { height: auto; padding: 0 2; layout: horizontal; }
.gh-author     { width: auto; color: #aad84c; }
.gh-sep        { width: auto; color: #3f4043; padding: 0 1; }
.gh-time       { width: auto; color: #4b4c4e; text-style: italic; }

/* ── Right: detail panel ── */
#gh-right {
    width: 1fr;
    height: 100%;
    layout: vertical;
}
#gh-detail-placeholder {
    width: 100%;
    height: 100%;
    content-align: center middle;
    text-align: center;
    color: #3f4043;
}
#gh-detail-titlebar {
    height: 3;
    background: #0d1016;
    border-bottom: solid #1f2a3a;
    padding: 0 2;
    color: #5ac1fe;
    text-style: bold;
    content-align: left middle;
}
#gh-detail-body {
    height: auto;
    padding: 1 2;
}
.gh-field-row   { height: 1; layout: horizontal; margin-bottom: 1; }
.gh-field-label { width: 10; color: #4b4c4e; text-style: bold; }
.gh-field-value { width: 1fr; color: #bfbdb6; }
#gh-detail-divider {
    height: 1;
    border-top: solid #1f2a3a;
    margin: 0 2 1 2;
}
#gh-files-title {
    height: 1;
    padding: 0 2;
    color: #4b4c4e;
    text-style: bold;
    margin-bottom: 1;
}
#gh-files {
    height: 1fr;
    padding: 0 2;
    scrollbar-color: #5ac1fe;
    scrollbar-size: 1 1;
}
.gh-file-row  { height: 1; layout: horizontal; margin-bottom: 1; }
.gh-file-dot  { width: 2; color: #3f4043; }
.gh-file-name { width: 1fr; color: #bfbdb6; }
.gh-file-add  { width: 7; color: #aad84c; text-align: right; }
.gh-file-del  { width: 7; color: #ef7177; text-align: right; }

/* ── Footer ── */
#gh-footer {
    height: 1;
    dock: bottom;
    background: #0d1016;
    border-top: solid #1f2a3a;
    padding: 0 2;
    align: left middle;
}
.gh-key      { width: auto; color: #5ac1fe; text-style: bold; margin-right: 1; }
.gh-sep-f    { width: auto; color: #3f4043; margin-right: 2; }
.gh-key-desc { width: auto; color: #4b4c4e; margin-right: 2; }

#gh-empty {
    width: 100%;
    height: 100%;
    content-align: center middle;
    text-align: center;
    color: #4b4c4e;
}
"""


class CommitDetail:
    def __init__(self, hash7: str, full_hash: str, message: str, author: str,
                 author_email: str, date: str):
        self.hash7 = hash7
        self.full_hash = full_hash
        self.message = message.strip()
        self.author = author
        self.author_email = author_email
        self.date = date
        self._files: list | None = None

    def get_files(self, repo_path: str) -> list:
        if self._files is not None:
            return self._files
        try:
            result = subprocess.run(
                ["git", "show", "--numstat", "--format=", self.full_hash],
                cwd=repo_path, capture_output=True, text=True, timeout=5
            )
            files = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) == 3:
                    try:
                        adds = int(parts[0]) if parts[0] != "-" else 0
                        dels = int(parts[1]) if parts[1] != "-" else 0
                    except ValueError:
                        adds, dels = 0, 0
                    files.append((parts[2].strip(), adds, dels))
            self._files = files
        except Exception:
            self._files = []
        return self._files


class GitHistoryScreen(ModalScreen):
    CSS = GIT_HISTORY_CSS
    BINDINGS = [
        ("escape", "close",       "Close"),
        ("enter",  "show_detail", "Detail"),
        ("c",      "copy_hash",   "Copy Hash"),
        ("o",      "open_files",  "Open Files"),
        ("r",      "refresh",     "Refresh"),
    ]

    def __init__(self, repo_path: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.repo_path = repo_path
        self.commits: list[CommitDetail] = []
        self._active_hash = None

    def compose(self) -> ComposeResult:
        with Vertical(id="git-popup"):
            with Horizontal(id="gh-header"):
                yield Label("🌿  Git History", id="gh-title")
                yield Label("", id="gh-meta")
            with Horizontal(id="gh-body"):
                with Vertical(id="gh-left"):
                    yield ListView(id="gh-commits")
                with Vertical(id="gh-right"):
                    yield Static(
                        "Select a commit to view details\n\n"
                        "[dim]↑↓ Navigate   Enter View   C Copy hash[/dim]",
                        id="gh-detail-placeholder",
                        markup=True,
                    )
                    with Vertical(id="gh-detail"):
                        yield Label(" Commit Details", id="gh-detail-titlebar")
                        with Vertical(id="gh-detail-body"):
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Hash",    classes="gh-field-label")
                                yield Label("",        id="gh-detail-hash",    classes="gh-field-value")
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Author",  classes="gh-field-label")
                                yield Label("",        id="gh-detail-author",  classes="gh-field-value")
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Date",    classes="gh-field-label")
                                yield Label("",        id="gh-detail-date",    classes="gh-field-value")
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Message", classes="gh-field-label")
                                yield Label("",        id="gh-detail-message", classes="gh-field-value")
                        yield Static("", id="gh-detail-divider")
                        yield Label("  Changed Files", id="gh-files-title")
                        with ScrollableContainer(id="gh-files"):
                            pass
            with Horizontal(id="gh-footer"):
                yield Label("↑↓", classes="gh-key")
                yield Label("Navigate", classes="gh-key-desc")
                yield Label("Enter",    classes="gh-key")
                yield Label("View",     classes="gh-key-desc")
                yield Label("C",        classes="gh-key")
                yield Label("Copy",     classes="gh-key-desc")
                yield Label("O",        classes="gh-key")
                yield Label("Open",     classes="gh-key-desc")
                yield Label("R",        classes="gh-key")
                yield Label("Refresh",  classes="gh-key-desc")
                yield Label("Esc",      classes="gh-key")
                yield Label("Close",    classes="gh-key-desc")

    def on_mount(self) -> None:
        self.query_one("#gh-detail").display = False
        self._debounce_timer = None
        self._load_git_data()

    # ── Git helpers ──────────────────────────────────────────────────────────

    def _is_git_repo(self) -> bool:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip() == "true"
        except Exception:
            return False

    def _get_current_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def _get_commit_count(self) -> int:
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=2
            )
            return int(result.stdout.strip())
        except Exception:
            return 0

    def _format_time_ago(self, date_str: str) -> str:
        try:
            dt = datetime.fromisoformat(date_str)
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            diff = now - dt
            minutes = diff.total_seconds() / 60
            hours = minutes / 60
            days = hours / 24
            if minutes < 1:
                return "just now"
            elif minutes < 60:
                return f"{int(minutes)}m ago"
            elif hours < 24:
                return f"{int(hours)}h ago"
            elif days < 7:
                return f"{int(days)}d ago"
            elif days < 30:
                return f"{int(days / 7)}w ago"
            elif days < 365:
                return f"{int(days / 30)}mo ago"
            else:
                return f"{int(days / 365)}y ago"
        except Exception:
            return date_str

    def _load_git_data(self) -> None:
        if not self._is_git_repo():
            self.query_one("#gh-commits", ListView).display = False
            self.query_one("#gh-left", Vertical).mount(
                Static("⚠  Not a git repository", id="gh-empty")
            )
            self.query_one("#gh-meta", Label).update("")
            return

        branch = self._get_current_branch()
        count = self._get_commit_count()
        self.query_one("#gh-meta", Label).update(
            f"[#aad84c]🌿 {branch}[/#aad84c]  [#3f4043]·[/#3f4043]  [#4b4c4e]{count} commits[/#4b4c4e]"
        )

        try:
            result = subprocess.run(
                ["git", "log", "--format=%H|%h|%s|%an|%ae|%ai", "-n", "80"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=5
            )
            self.commits = []
            list_view = self.query_one("#gh-commits", ListView)
            list_view.clear()

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("|")
                if len(parts) >= 6:
                    full_hash, hash7, message, author, email, date = parts[:6]
                    commit = CommitDetail(hash7, full_hash, message, author, email, date)
                    self.commits.append(commit)
                    time_ago = self._format_time_ago(date)
                    # Truncate message to fit panel
                    short_msg = message[:38] if len(message) > 38 else message
                    markup_text = (
                        f"[#5ac1fe]●[/#5ac1fe] [#e6b450]{escape(hash7)}[/#e6b450]  {escape(short_msg)}\n"
                        f"  [#aad84c]{escape(author)}[/#aad84c] [dim]·[/dim] [italic dim]{escape(time_ago)}[/italic dim]"
                    )
                    list_view.append(ListItem(
                        Static(markup_text, classes="gh-row")
                    ))
        except Exception as e:
            self.notify(f"Error loading git history: {e}", severity="error")

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_close(self) -> None:
        if self._debounce_timer is not None:
            try:
                self._debounce_timer.stop()
            except Exception:
                pass
        self.dismiss()

    def action_refresh(self) -> None:
        self._load_git_data()
        self.notify("Git history refreshed", timeout=1)

    def action_show_detail(self) -> None:
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is None or list_view.index >= len(self.commits):
            return
        self._show_commit_detail(self.commits[list_view.index])

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.index is not None and event.list_view.index < len(self.commits):
            if self._debounce_timer is not None:
                try:
                    self._debounce_timer.stop()
                except Exception:
                    pass
                self._debounce_timer = None
            
            commit = self.commits[event.list_view.index]
            self._debounce_timer = self.set_timer(
                0.15,
                lambda: self._show_commit_detail(commit)
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.index is not None and event.list_view.index < len(self.commits):
            if self._debounce_timer is not None:
                try:
                    self._debounce_timer.stop()
                except Exception:
                    pass
                self._debounce_timer = None
            self._show_commit_detail(self.commits[event.list_view.index])

    def _show_commit_detail(self, commit: CommitDetail) -> None:
        self._active_hash = commit.full_hash
        self.query_one("#gh-detail-hash",    Label).update(
            f"[#e6b450]{commit.hash7}[/#e6b450]  [dim]{commit.full_hash}[/dim]"
        )
        self.query_one("#gh-detail-author",  Label).update(
            f"[#aad84c]{commit.author}[/#aad84c] [dim]<{commit.author_email}>[/dim]"
        )
        self.query_one("#gh-detail-date",    Label).update(
            f"{commit.date}  [dim]({self._format_time_ago(commit.date)})[/dim]"
        )
        self.query_one("#gh-detail-message", Label).update(commit.message)

        files_container = self.query_one("#gh-files", ScrollableContainer)
        files_container.remove_children()
        files_container.mount(Static("[dim]Loading changed files...[/dim]", markup=True, id="gh-files-loading"))

        self.query_one("#gh-detail-placeholder").display = False
        self.query_one("#gh-detail").display = True

        self._load_changed_files(commit)

    @work(exclusive=True)
    async def _load_changed_files(self, commit: CommitDetail) -> None:
        import asyncio
        loop = asyncio.get_running_loop()
        # Fetch changed files on a background thread pool executor to prevent event loop lag
        files = await loop.run_in_executor(None, commit.get_files, self.repo_path)
        if self._active_hash == commit.full_hash:
            self._update_files_ui(files)

    def _update_files_ui(self, files: list) -> None:
        files_container = self.query_one("#gh-files", ScrollableContainer)
        files_container.remove_children()
        if files:
            import time
            unique = int(time.time() * 1000)
            for i, (filename, adds, dels) in enumerate(files):
                add_str = f"[#aad84c]+{adds}[/#aad84c]" if adds else ""
                del_str = f"[#ef7177]-{dels}[/#ef7177]" if dels else ""
                files_container.mount(Horizontal(
                    Static("▸", classes="gh-file-dot"),
                    Static(filename, classes="gh-file-name"),
                    Static(add_str, markup=True, classes="gh-file-add"),
                    Static(del_str, markup=True, classes="gh-file-del"),
                    classes="gh-file-row",
                    id=f"gh-file-{unique}-{i}",
                ))
        else:
            files_container.mount(Static("[dim]No file changes recorded[/dim]", markup=True, id="gh-empty-files"))


    def action_copy_hash(self) -> None:
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is not None and list_view.index < len(self.commits):
            commit = self.commits[list_view.index]
            self.app.copy_to_clipboard(commit.full_hash)
            self.notify(f"Copied: {commit.hash7}", timeout=2)

    def action_open_files(self) -> None:
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is not None and list_view.index < len(self.commits):
            commit = self.commits[list_view.index]
            files = commit.get_files(self.repo_path)
            if files:
                files_list = ", ".join([f[0] for f in files[:5]])
                if len(files) > 5:
                    files_list += f" +{len(files) - 5} more"
                self.notify(f"Files: {files_list}", timeout=4)
            else:
                self.notify("No files changed in this commit", timeout=2)
