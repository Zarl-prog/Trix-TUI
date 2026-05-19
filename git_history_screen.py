import subprocess
from datetime import datetime, timezone
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static


GIT_HISTORY_CSS = """
GitHistoryScreen {
    align: center middle;
    background: rgba(0,0,0,0.6);
}

#git-popup {
    width: 80%;
    height: 80%;
    background: #1a1e26;
    border: solid #5ac1fe;
    layout: vertical;
}

/* ── Header ── */
#gh-header {
    height: 3;
    dock: top;
    background: #141820;
    border-bottom: solid #3f4043;
    padding: 0 2;
    align: left middle;
}
#gh-title { width: auto; color: #5ac1fe; text-style: bold; }
#gh-meta  { width: 1fr; content-align: right middle; }

/* ── Two-column body ── */
#gh-body {
    height: 1fr;
    layout: horizontal;
}

/* ── Left: commit list ── */
#gh-left {
    width: 40%;
    height: 100%;
    border-right: solid #3f4043;
}
#gh-commits {
    height: 1fr;
    background: #1a1e26;
    scrollbar-color: #5ac1fe;
    scrollbar-size: 1 1;
}
#gh-commits > ListItem {
    height: auto;
    padding: 0;
    background: #1a1e26;
    border-bottom: solid #2d2f34;
}
#gh-commits > ListItem:hover { background: #1f2430; }
#gh-commits > ListItem.--highlight {
    background: #1f2430;
    border-left: tall #5ac1fe;
}
.gh-row        { height: auto; padding: 1 2; }
.gh-row-top    { height: auto; layout: horizontal; }
.gh-dot        { width: 2; color: #5ac1fe; }
.gh-hash       { width: auto; color: #feb454; text-style: bold; }
.gh-msg        { width: 1fr; color: #bfbdb6; padding: 0 1; }
.gh-row-bottom { height: auto; padding: 0 2; layout: horizontal; }
.gh-author     { width: auto; color: #aad84c; }
.gh-sep        { width: auto; color: #4b4c4e; padding: 0 1; }
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
    color: #4b4c4e;
}
#gh-detail-title {
    height: 2;
    background: #141820;
    border-bottom: solid #3f4043;
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
.gh-field-label { width: 12; color: #4b4c4e; }
.gh-field-value { width: 1fr; color: #bfbdb6; }
#gh-detail-divider {
    height: 1;
    border-top: solid #3f4043;
    margin: 1 2;
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
.gh-file-dot  { width: 2; color: #5ac1fe; }
.gh-file-name { width: 1fr; color: #bfbdb6; }
.gh-file-add  { width: 6; color: #aad84c; text-align: right; }
.gh-file-del  { width: 6; color: #ef7177; text-align: right; }

/* ── Footer ── */
#gh-footer {
    height: 3;
    dock: bottom;
    background: #141820;
    border-top: solid #3f4043;
    padding: 0 2;
    align: left middle;
}
.gh-key      { width: auto; background: #1f2127; color: #5ac1fe; padding: 0 1; margin-right: 1; }
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
        ("escape", "close", "Close"),
        ("enter", "show_detail", "Show Detail"),
        ("c", "copy_hash", "Copy Hash"),
        ("o", "open_files", "Open Files"),
    ]

    def __init__(self, repo_path: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.repo_path = repo_path
        self.commits: list[CommitDetail] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="git-popup"):
            # Header
            with Horizontal(id="gh-header"):
                yield Label(" Git History", id="gh-title")
                yield Label("", id="gh-meta")
            # Body: two columns
            with Horizontal(id="gh-body"):
                # Left — commit list
                with Vertical(id="gh-left"):
                    yield ListView(id="gh-commits")
                # Right — detail
                with Vertical(id="gh-right"):
                    yield Static("Select a commit and press Enter to view details", id="gh-detail-placeholder")
                    with Vertical(id="gh-detail"):
                        yield Label(" Commit Details", id="gh-detail-title")
                        with Vertical(id="gh-detail-body"):
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Hash", classes="gh-field-label")
                                yield Label("", id="gh-detail-hash", classes="gh-field-value")
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Author", classes="gh-field-label")
                                yield Label("", id="gh-detail-author", classes="gh-field-value")
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Date", classes="gh-field-label")
                                yield Label("", id="gh-detail-date", classes="gh-field-value")
                            with Horizontal(classes="gh-field-row"):
                                yield Label("Message", classes="gh-field-label")
                                yield Label("", id="gh-detail-message", classes="gh-field-value")
                        yield Static("", id="gh-detail-divider")
                        yield Label(" Files Changed", id="gh-files-title")
                        with ScrollableContainer(id="gh-files"):
                            pass
            # Footer
            with Horizontal(id="gh-footer"):
                yield Label("↑↓", classes="gh-key")
                yield Label("Navigate", classes="gh-key-desc")
                yield Label("Enter", classes="gh-key")
                yield Label("View", classes="gh-key-desc")
                yield Label("C", classes="gh-key")
                yield Label("Copy", classes="gh-key-desc")
                yield Label("O", classes="gh-key")
                yield Label("Open Files", classes="gh-key-desc")
                yield Label("Esc", classes="gh-key")
                yield Label("Close", classes="gh-key-desc")

    def on_mount(self) -> None:
        self.query_one("#gh-detail").display = False
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
            if minutes < 60:
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
            self.query_one("#gh-left", Vertical).mount(Static("Not a git repository", id="gh-empty"))
            self.query_one("#gh-meta", Label).update("")
            return

        branch = self._get_current_branch()
        count = self._get_commit_count()
        self.query_one("#gh-meta", Label).update(
            f"[#aad84c]🌿 {branch}[/#aad84c] [#4b4c4e]·[/#4b4c4e] [#4b4c4e]{count} commits[/#4b4c4e]"
        )

        try:
            result = subprocess.run(
                ["git", "log", "--format=%H|%h|%s|%an|%ae|%ai", "-n", "50"],
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
                    list_view.append(ListItem(
                        Vertical(
                            Horizontal(
                                Static("●", classes="gh-dot"),
                                Static(hash7, classes="gh-hash"),
                                Static(message[:36], classes="gh-msg"),
                                classes="gh-row-top",
                            ),
                            Horizontal(
                                Static(author, classes="gh-author"),
                                Static("·", classes="gh-sep"),
                                Static(time_ago, classes="gh-time"),
                                classes="gh-row-bottom",
                            ),
                            classes="gh-row",
                        )
                    ))
        except Exception as e:
            self.notify(f"Error loading git history: {e}", severity="error")

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_close(self) -> None:
        self.dismiss()

    def action_show_detail(self) -> None:
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is None or list_view.index >= len(self.commits):
            return
        self._show_commit_detail(self.commits[list_view.index])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is not None and list_view.index < len(self.commits):
            self._show_commit_detail(self.commits[list_view.index])

    def _show_commit_detail(self, commit: CommitDetail) -> None:
        self.query_one("#gh-detail-hash", Label).update(commit.full_hash)
        self.query_one("#gh-detail-author", Label).update(f"{commit.author} <{commit.author_email}>")
        self.query_one("#gh-detail-date", Label).update(commit.date)
        self.query_one("#gh-detail-message", Label).update(commit.message)

        files_container = self.query_one("#gh-files", ScrollableContainer)
        files_container.remove_children()

        files = commit.get_files(self.repo_path)
        if files:
            for i, (filename, adds, dels) in enumerate(files):
                files_container.mount(Horizontal(
                    Static("●", classes="gh-file-dot"),
                    Static(filename, classes="gh-file-name"),
                    Static(f"+{adds}" if adds else "", classes="gh-file-add"),
                    Static(f"-{dels}" if dels else "", classes="gh-file-del"),
                    classes="gh-file-row",
                    id=f"gh-file-{i}",
                ))
        else:
            files_container.mount(Static("No files changed", id="gh-empty-files"))

        self.query_one("#gh-detail-placeholder").display = False
        self.query_one("#gh-detail").display = True

    def action_copy_hash(self) -> None:
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is not None and list_view.index < len(self.commits):
            commit = self.commits[list_view.index]
            self.app.copy_to_clipboard(commit.full_hash)
            self.notify(f"Copied: {commit.full_hash}")

    def action_open_files(self) -> None:
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is not None and list_view.index < len(self.commits):
            commit = self.commits[list_view.index]
            files = commit.get_files(self.repo_path)
            if files:
                files_list = ", ".join([f[0] for f in files[:5]])
                if len(files) > 5:
                    files_list += f" +{len(files) - 5} more"
                self.notify(f"Files changed: {files_list}")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.action_close()
            event.prevent_default()
