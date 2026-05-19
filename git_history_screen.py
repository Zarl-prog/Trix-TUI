import subprocess
from datetime import datetime, timezone
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static


GIT_HISTORY_CSS = """
GitHistoryScreen {
    align: right middle;
}
#git-history-panel {
    width: 60;
    height: 100%;
    background: #1f2127;
    border-left: solid #5ac1fe;
}
#gh-header {
    height: 3;
    dock: top;
    background: #1a1e26;
    border-bottom: solid #3f4043;
    padding: 0 1;
    layout: horizontal;
}
#gh-title { width: auto; color: #5ac1fe; text-style: bold; }
#gh-branch { width: 1fr; color: #5ac1fe; text-align: right; content-align: center middle; }
#gh-commit-count { width: auto; color: #4b4c4e; }

#gh-content {
    height: 1fr;
    layout: vertical;
}

#gh-commits {
    height: 1fr;
    background: #1f2127;
}
#gh-commits ListItem {
    height: auto;
    padding: 0 1;
}
#gh-commit-item {
    height: auto;
    padding: 1 0;
}

#gh-detail {
    height: 1fr;
    display: none;
}

#gh-detail-header {
    height: auto;
    dock: top;
    background: #1a1e26;
    border-bottom: solid #3f4043;
    padding: 1;
}
#gh-detail-hash { color: #5ac1fe; text-style: bold; }
#gh-detail-author { color: #aad84c; }
#gh-detail-date { color: #4b4c4e; }
#gh-detail-message { color: #bfbdb6; margin-top: 1; }

#gh-files {
    height: 1fr;
    padding: 1;
}

#gh-actions {
    height: 3;
    dock: bottom;
    background: #1a1e26;
    border-top: solid #3f4043;
    layout: horizontal;
    padding: 0 1;
}
#gh-action-hint { width: 1fr; color: #4b4c4e; content-align: center middle; }

#gh-back-hint {
    height: 3;
    dock: bottom;
    background: #1a1e26;
    border-top: solid #3f4043;
    layout: horizontal;
    padding: 0 1;
}

#gh-empty {
    width: 100%;
    height: 100%;
    content-align: center middle;
    text-align: center;
    color: #4b4c4e;
}
"""


class CommitDetail:
    """Represents a single commit with all its details."""
    def __init__(self, hash7: str, full_hash: str, message: str, author: str,
                 author_email: str, date: str):
        self.hash7 = hash7
        self.full_hash = full_hash
        self.message = message.strip()
        self.author = author
        self.author_email = author_email
        self.date = date
        self._files: list | None = None  # lazy-loaded

    def get_files(self, repo_path: str) -> list:
        """Lazily fetch files changed in this commit."""
        if self._files is not None:
            return self._files
        try:
            result = subprocess.run(
                ["git", "show", "--numstat", "--format=", self.full_hash],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
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
    """Git commit history panel that slides in from the right."""

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
        self.current_commit: CommitDetail | None = None
        self.showing_detail = False

    def compose(self) -> ComposeResult:
        with Vertical(id="git-history-panel"):
            with Horizontal(id="gh-header"):
                yield Label("📜 Git History", id="gh-title")
                yield Label("", id="gh-branch")
                yield Label("", id="gh-commit-count")
            with Vertical(id="gh-content"):
                yield ListView(id="gh-commits")
                with Vertical(id="gh-detail"):
                    with Vertical(id="gh-detail-header"):
                        yield Label("", id="gh-detail-hash")
                        yield Label("", id="gh-detail-author")
                        yield Label("", id="gh-detail-date")
                        yield Label("", id="gh-detail-message")
                    with ScrollableContainer(id="gh-files"):
                        pass
            with Horizontal(id="gh-actions"):
                yield Label("Enter: View  C: Copy  O: Open Files  Esc: Close", id="gh-action-hint")
            with Horizontal(id="gh-back-hint"):
                yield Label("Esc: Back to list", id="gh-back-hint-label")

    def on_mount(self) -> None:
        self.query_one("#gh-back-hint").display = False
        self._load_git_data()

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

    def _load_git_data(self) -> None:
        if not self._is_git_repo():
            self.query_one("#gh-commits", ListView).display = False
            self.query_one("#gh-content", Vertical).mount(
                Static("Not a git repository", id="gh-empty")
            )
            self.query_one("#gh-branch", Label).update("")
            self.query_one("#gh-commit-count", Label).update("")
            return

        branch = self._get_current_branch()
        count = self._get_commit_count()
        self.query_one("#gh-branch", Label).update(f"🌿 {branch}")
        self.query_one("#gh-commit-count", Label).update(f"{count} commits")

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
                    item_text = f"{hash7}  {message[:40]:<40}  {author:<10}  {time_ago}"
                    list_view.append(ListItem(Static(item_text, classes="gh-commit-item")))

        except Exception as e:
            self.notify(f"Error loading git history: {e}", severity="error")

    def _format_time_ago(self, date_str: str) -> str:
        try:
            dt = datetime.fromisoformat(date_str)
            now = datetime.now(timezone.utc)
            # Make dt timezone-aware if it isn't
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

    def action_close(self) -> None:
        self.dismiss()

    def action_show_detail(self) -> None:
        if self.showing_detail:
            return
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is None:
            return
        self.current_commit = self.commits[list_view.index]
        self._show_commit_detail()
        self.showing_detail = True

    def _show_commit_detail(self) -> None:
        if not self.current_commit:
            return
        commit = self.current_commit

        self.query_one("#gh-detail-hash", Label).update(f"Commit: {commit.full_hash}")
        self.query_one("#gh-detail-author", Label).update(f"{commit.author} <{commit.author_email}>")
        self.query_one("#gh-detail-date", Label).update(commit.date)
        self.query_one("#gh-detail-message", Label).update(commit.message)

        files_container = self.query_one("#gh-files", ScrollableContainer)
        files_container.remove_children()

        files = commit.get_files(self.repo_path)
        if files:
            for i, (filename, adds, dels) in enumerate(files):
                files_container.mount(Horizontal(
                    Static(filename, classes="gh-file-name"),
                    Static(f"+{adds}" if adds else "", classes="gh-file-add"),
                    Static(f"-{dels}" if dels else "", classes="gh-file-del"),
                    id=f"gh-file-item-{i}"
                ))
        else:
            files_container.mount(Static("No files changed", id="gh-empty-files"))

        self.query_one("#gh-commits", ListView).display = False
        self.query_one("#gh-detail").display = True
        self.query_one("#gh-actions").display = False
        self.query_one("#gh-back-hint").display = True

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
            if self.showing_detail:
                self.query_one("#gh-commits", ListView).display = True
                self.query_one("#gh-detail").display = False
                self.query_one("#gh-actions").display = True
                self.query_one("#gh-back-hint").display = False
                self.showing_detail = False
                event.prevent_default()
            else:
                self.action_close()
                event.prevent_default()
