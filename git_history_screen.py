import subprocess
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Static


GIT_HISTORY_CSS = """
GitHistoryScreen {
    align: center right;
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

#gh-commit-list {
    height: 1fr;
    background: #1f2127;
}
#gh-commit-list ListItem {
    height: auto;
    padding: 0 1;
}
#gh-commit-item {
    layout: vertical;
    height: auto;
    padding: 1 0;
}
#gh-hash { color: #5ac1fe; text-style: bold; }
#gh-message { color: #bfbdb6; }
#gh-author { color: #aad84c; }
#gh-time { color: #4b4c4e; }

#gh-detail {
    height: 1fr;
    display: none;
}
#gh-detail.visible { display: block; }

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
#gh-file-item {
    layout: horizontal;
    height: auto;
    padding: 0 1;
}
#gh-file-name { width: 1fr; color: #bfbdb6; }
#gh-file-add { color: #aad84c; }
#gh-file-del { color: #ef7177; }

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
                 author_email: str, date: str, files: list):
        self.hash7 = hash7
        self.full_hash = full_hash
        self.message = message.strip()
        self.author = author
        self.author_email = author_email
        self.date = date
        self.files = files  # list of (filename, additions, deletions)


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
                with ScrollableContainer(id="gh-commit-list"):
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
            with Horizontal(id="gh-back-hint", display="none"):
                yield Label("Esc: Back to list", id="gh-back-hint-label")

    def on_mount(self) -> None:
        self._load_git_data()

    def _is_git_repo(self) -> bool:
        """Check if the current path is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip() == "true"
        except Exception:
            return False

    def _get_current_branch(self) -> str:
        """Get the current git branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def _get_commit_count(self) -> int:
        """Get total number of commits."""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=2
            )
            return int(result.stdout.strip())
        except Exception:
            return 0

    def _load_git_data(self) -> None:
        """Load git commit history."""
        if not self._is_git_repo():
            self.query_one("#gh-commit-list", ListView).display = False
            self.query_one("#gh-content", Vertical).mount(
                Static("Not a git repository", id="gh-empty")
            )
            self.query_one("#gh-branch", Label).update("")
            self.query_one("#gh-commit-count", Label).update("")
            return

        # Get branch and count
        branch = self._get_current_branch()
        count = self._get_commit_count()
        self.query_one("#gh-branch", Label).update(f"🌿 {branch}")
        self.query_one("#gh-commit-count", Label).update(f"{count} commits")

        # Get commit log
        try:
            result = subprocess.run(
                ["git", "log", "--format=%H|%h|%s|%an|%ae|%ai", "-n", "50"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
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
                    
                    # Get files changed for this commit
                    files = self._get_commit_files(full_hash)
                    
                    commit = CommitDetail(hash7, full_hash, message, author, email, date, files)
                    self.commits.append(commit)
                    
                    # Format: hash7  message  author  time_ago
                    time_ago = self._format_time_ago(date)
                    item_text = f"{hash7}  {message[:40]:<40}  {author:<10}  {time_ago}"
                    list_view.add(ListItem(
                        Static(item_text, id="gh-commit-item")
                    ))
                    
        except Exception as e:
            self.notify(f"Error loading git history: {e}", severity="error")

    def _get_commit_files(self, full_hash: str) -> list:
        """Get list of files changed in a commit."""
        try:
            result = subprocess.run(
                ["git", "show", "--stat", "--format=", full_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            files = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip() or "|" not in line:
                    continue
                parts = line.split("|")
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    stats = parts[1].strip()
                    # Parse additions and deletions
                    add = 0
                    del_count = 0
                    if "+" in stats:
                        add_parts = stats.split("+")
                        try:
                            add = int(add_parts[-1].strip().split()[0])
                        except (IndexError, ValueError):
                            pass
                    if "-" in stats:
                        del_parts = stats.split("-")
                        try:
                            del_count = int(del_parts[-1].strip().split()[0])
                        except (IndexError, ValueError):
                            pass
                    files.append((filename, add, del_count))
            return files
        except Exception:
            return []

    def _format_time_ago(self, date_str: str) -> str:
        """Format the date as relative time (e.g., '2 hours ago')."""
        try:
            # Parse ISO format date
            dt = datetime.fromisoformat(date_str.replace(" +0000", "").replace(" -0000", ""))
            now = datetime.now()
            diff = now - dt
            
            minutes = diff.total_seconds() / 60
            hours = minutes / 60
            days = hours / 24
            
            if minutes < 60:
                return f"{int(minutes)} minutes ago"
            elif hours < 24:
                return f"{int(hours)} hours ago"
            elif days < 7:
                return f"{int(days)} days ago"
            elif days < 30:
                weeks = int(days / 7)
                return f"{weeks} weeks ago"
            elif days < 365:
                months = int(days / 30)
                return f"{months} months ago"
            else:
                years = int(days / 365)
                return f"{years} years ago"
        except Exception:
            return date_str

    def action_close(self) -> None:
        """Close the git history panel."""
        self.dismiss()

    def action_show_detail(self) -> None:
        """Show detailed commit info."""
        if self.showing_detail:
            return
            
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is None:
            return
            
        self.current_commit = self.commits[list_view.index]
        self._show_commit_detail()
        self.showing_detail = True

    def _show_commit_detail(self) -> None:
        """Display the commit detail view."""
        if not self.current_commit:
            return
            
        commit = self.current_commit
        
        # Update detail view
        self.query_one("#gh-detail-hash", Label).update(f"Commit: {commit.full_hash}")
        self.query_one("#gh-detail-author", Label).update(f"{commit.author} <{commit.author_email}>")
        self.query_one("#gh-detail-date", Label).update(commit.date)
        self.query_one("#gh-detail-message", Label).update(commit.message)
        
        # Show files
        files_container = self.query_one("#gh-files", ScrollableContainer)
        files_container.remove_children()
        
        if commit.files:
            for filename, adds, dels in commit.files:
                file_item = Horizontal(
                    Static(filename, id="gh-file-name"),
                    Static(f"+{adds}" if adds else "", id="gh-file-add") if adds else Static("", id="gh-file-add"),
                    Static(f"-{dels}" if dels else "", id="gh-file-del") if dels else Static("", id="gh-file-del"),
                    id="gh-file-item"
                )
                files_container.mount(file_item)
        else:
            files_container.mount(Static("No files changed", id="gh-empty-files"))
        
        # Toggle views
        self.query_one("#gh-commit-list", ListView).display = False
        self.query_one("#gh-detail").display = True
        self.query_one("#gh-actions").display = False
        self.query_one("#gh-back-hint").display = True

    def action_copy_hash(self) -> None:
        """Copy the selected commit hash to clipboard."""
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is not None and list_view.index < len(self.commits):
            commit = self.commits[list_view.index]
            self.app.copy_to_clipboard(commit.full_hash)
            self.notify(f"Copied: {commit.full_hash}")

    def action_open_files(self) -> None:
        """Open the changed files from selected commit."""
        list_view = self.query_one("#gh-commits", ListView)
        if list_view.index is not None and list_view.index < len(self.commits):
            commit = self.commits[list_view.index]
            if commit.files:
                # Show notification for now - file opening can be enhanced later
                files_list = ", ".join([f[0] for f in commit.files[:5]])
                if len(commit.files) > 5:
                    files_list += f" +{len(commit.files) - 5} more"
                self.notify(f"Files changed: {files_list}")

    def on_key(self, event) -> None:
        """Handle key events."""
        if event.key == "escape":
            if self.showing_detail:
                # Go back to list
                self.query_one("#gh-commit-list", ListView).display = True
                self.query_one("#gh-detail").display = False
                self.query_one("#gh-actions").display = True
                self.query_one("#gh-back-hint").display = False
                self.showing_detail = False
            else:
                self.action_close()
            event.prevent_default()
        else:
            super().on_key(event)