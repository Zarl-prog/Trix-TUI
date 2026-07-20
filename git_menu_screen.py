import subprocess
from datetime import datetime, timezone
import asyncio
from rich.markup import escape
from textual import work, on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.events import Click, Key
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Static, Button


_CSS_SOURCE = "trix_git_menu"


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


class GitMenuScreen(ModalScreen):
    CSS = """
GitMenuScreen {
    align: center middle;
    background: rgba(0,0,0,0.82);
}
#gm-popup {
    width: 80%;
    height: 78%;
    min-width: 60;
    background: #131721;
    border: tall #5ac1fe;
    layout: vertical;
}
#gm-header { height: 3; dock: top; background: #0d1016; border-bottom: solid #2e3038; padding: 0 2; align: left middle; }
#gm-title  { width: auto; color: #5ac1fe; text-style: bold; }
#gm-meta   { width: 1fr; content-align: right middle; color: #686868; }
#gm-body   { height: 1fr; layout: vertical; }
#gm-commit-area { height: auto; padding: 0 3 0 3; background: #0d1016; border-bottom: solid #2e3038; align: center middle; layout: vertical; }
#gm-message { width: 100%; height: 3; border: solid #2e3038; background: #131721; color: #bfbdb6; padding: 0 1; margin-top: 1; }
#gm-message:focus { border: solid #5ac1fe; }
#gm-buttons { height: auto; layout: horizontal; align: center middle; }
#gm-buttons Button { margin: 1 1 0 1; padding: 0 5; min-width: 18; }
#gm-commit-btn { background: #5ac1fe; color: #0d1016; text-style: bold; border: none; }
#gm-commit-btn:hover { background: #7dd0ff; }
#gm-commit-btn:disabled { background: #2e3038; color: #686868; }
#gm-push-btn { background: #39bae5; color: #0d1016; text-style: bold; border: none; }
#gm-push-btn:hover { background: #5ac8f0; }
#gm-push-btn:disabled { background: #2e3038; color: #686868; }
#gm-error { height: 1; color: #ef7177; text-align: center; }
#gm-history-header { height: 3; padding: 0 2; color: #686868; text-style: bold; background: #131721; align: left middle; }
#gm-list { height: 1fr; background: #131721; scrollbar-color: #5ac1fe; scrollbar-background: #2e3038; scrollbar-size: 1 1; overflow-y: auto; }
.gm-commit { height: auto; background: #131721; border-bottom: solid #2e3038; }
.gm-commit.gm-focused { border-left: tall #5ac1fe; background: #0d1016; }
.gm-commit:hover { background: #0d1016; }
.gm-row { height: auto; padding: 1 2; }
.gm-expanded { height: auto; padding: 0 2 1 2; background: #1a1d23; }
.gm-divider { height: 1; border-top: solid #2e3038; margin: 0 0 1 0; }
.gm-actions-row { height: auto; layout: horizontal; align: center middle; margin-top: 1; }
.gm-actions-row Button { margin: 0 1; padding: 0 2; min-width: 8; }
#gm-footer { height: auto; min-height: 3; dock: bottom; background: #0d1016; border-top: solid #2e3038; padding: 1 2; layout: horizontal; align: left middle; }
#gm-footer > .gm-key { width: auto; color: #5ac1fe; text-style: bold; margin-right: 1; }
#gm-footer > .gm-key-desc { width: auto; color: #686868; margin-right: 2; }
#gm-empty { width: 100%; height: 100%; content-align: center middle; text-align: center; color: #686868; }
    """
    BINDINGS = [
        ("escape", "close",     "Close"),
        ("enter",  "toggle",    "Toggle"),
        ("up",     "focus_up",  "Up"),
        ("down",   "focus_down","Down"),
        ("c",      "copy_hash", "Copy Hash"),
        ("o",      "open_files","Files"),
        ("r",      "refresh",   "Refresh"),
        ("g",      "focus_input","Commit"),
    ]

    def __init__(self, repo_path: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.repo_path = repo_path
        self.commits: list[CommitDetail] = []
        self._expanded_index: int | None = None
        self._focused_index: int = 0
        self._loading_files_for: int | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="gm-popup"):
            with Horizontal(id="gm-header"):
                yield Label("  Git Menu", id="gm-title")
                yield Label("", id="gm-meta")
            with Vertical(id="gm-body"):
                with Vertical(id="gm-commit-area"):
                    yield Input(id="gm-message", placeholder="Commit message...")
                    with Horizontal(id="gm-buttons"):
                        yield Button("Commit", id="gm-commit-btn")
                        yield Button("Commit && Push", id="gm-push-btn")
                    yield Static("", id="gm-error")
                yield Label("  History", id="gm-history-header")
                yield ScrollableContainer(id="gm-list")
            with Horizontal(id="gm-footer"):
                yield Label("↑↓", classes="gm-key")
                yield Label("Nav ",     classes="gm-key-desc")
                yield Label("Enter",    classes="gm-key")
                yield Label("Toggle",   classes="gm-key-desc")
                yield Label("G",        classes="gm-key")
                yield Label("Msg",      classes="gm-key-desc")
                yield Label("C",        classes="gm-key")
                yield Label("Hash",     classes="gm-key-desc")
                yield Label("O",        classes="gm-key")
                yield Label("Files",    classes="gm-key-desc")
                yield Label("R",        classes="gm-key")
                yield Label("Refr",     classes="gm-key-desc")
                yield Label("Esc",      classes="gm-key")
                yield Label("Close",    classes="gm-key-desc")

    # ── Mount / lifecycle ─────────────────────────────────────────────────

    def on_mount(self) -> None:
        from themes import build_git_menu_css
        try:
            theme = self.app._current_theme_dict
            css = build_git_menu_css(theme)
            self.stylesheet.add_source(css, read_from=(_CSS_SOURCE, ""))
            self.refresh_css(animate=False)
        except Exception:
            pass
        self._load_git_data()

    # ── Git helpers ────────────────────────────────────────────────────────

    def _is_git_repo(self) -> bool:
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=2,
            )
            return r.stdout.strip() == "true"
        except Exception:
            return False

    def _get_current_branch(self) -> str:
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=2,
            )
            return r.stdout.strip()
        except Exception:
            return "unknown"

    def _get_commit_count(self) -> int:
        try:
            r = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=2,
            )
            return int(r.stdout.strip())
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

    # ── Load / build commit list ───────────────────────────────────────────

    def _load_git_data(self) -> None:
        if not self._is_git_repo():
            self.query_one("#gm-list", ScrollableContainer).display = False
            self.query_one("#gm-history-header", Label).display = False
            self.query_one("#gm-body", Vertical).mount(
                Static("  Not a git repository", id="gm-empty"),
                before=0,
            )
            self.query_one("#gm-meta", Label).update("")
            return

        branch = self._get_current_branch()
        count = self._get_commit_count()
        self.query_one("#gm-meta", Label).update(
            f"[#aad84c]{branch}[/#aad84c]  [#2e3038]\u00b7[/#2e3038]  [#686868]{count} commit{'s' if count != 1 else ''}[/#686868]"
        )

        try:
            result = subprocess.run(
                ["git", "log", "--format=%H|%h|%s|%an|%ae|%ai", "-n", "80"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=5,
            )
            self.commits = []
            list_container = self.query_one("#gm-list", ScrollableContainer)
            list_container.remove_children()

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("|")
                if len(parts) >= 6:
                    full_hash, hash7, message, author, email, date = parts[:6]
                    commit = CommitDetail(hash7, full_hash, message, author, email, date)
                    self.commits.append(commit)
                    idx = len(self.commits) - 1
                    list_container.mount(self._build_commit_item(idx, commit))

            if self.commits:
                self._focus_commit(0)
        except Exception as e:
            self.notify(f"Error loading git history: {e}", severity="error")

    def _build_commit_item(self, idx: int, commit: CommitDetail) -> Vertical:
        time_ago = self._format_time_ago(commit.date)
        short_msg = commit.message[:42] if len(commit.message) > 42 else commit.message

        collapsed = Static(
            f"[#5ac1fe]\u25cf[/#5ac1fe] [#e6b450]{escape(commit.hash7)}[/#e6b450]  {escape(short_msg)}\n"
            f"  [#aad84c]{escape(commit.author)}[/#aad84c] [dim]\u00b7[/dim] [italic dim]{escape(time_ago)}[/italic dim]",
            classes="gm-row",
            id=f"gm-row-{idx}",
        )

        expanded = Vertical(
            Static("", classes="gm-divider"),
            Static("", id=f"gm-detail-{idx}"),
            Vertical(id=f"gm-actions-{idx}"),
            classes="gm-expanded",
            id=f"gm-expanded-{idx}",
        )
        expanded.display = False

        return Vertical(
            collapsed, expanded,
            id=f"gm-commit-{idx}",
            classes="gm-commit",
        )

    # ── Focus / highlight ─────────────────────────────────────────────────

    def _focus_commit(self, idx: int) -> None:
        if not self.commits:
            return
        idx = max(0, min(idx, len(self.commits) - 1))
        self._focused_index = idx

        bag = self.query_one("#gm-list", ScrollableContainer)
        for child in bag.children:
            child.set_class(False, "gm-focused")

        target = self.query_one(f"#gm-commit-{idx}", Vertical)
        target.set_class(True, "gm-focused")
        target.scroll_visible()

    def _get_focused_commit(self) -> CommitDetail | None:
        if self.commits and 0 <= self._focused_index < len(self.commits):
            return self.commits[self._focused_index]
        return None

    # ── Accordion toggle ───────────────────────────────────────────────────

    def _toggle_expand(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.commits):
            return
        if self._expanded_index == idx:
            self._collapse(idx)
        else:
            if self._expanded_index is not None:
                self._collapse(self._expanded_index)
            self._expand(idx)

    def _collapse(self, idx: int) -> None:
        try:
            self.query_one(f"#gm-expanded-{idx}", Vertical).display = False
        except Exception:
            pass
        self._expanded_index = None

    def _expand(self, idx: int) -> None:
        commit = self.commits[idx]
        self._expanded_index = idx

        expanded = self.query_one(f"#gm-expanded-{idx}", Vertical)
        detail = self.query_one(f"#gm-detail-{idx}", Static)
        actions = self.query_one(f"#gm-actions-{idx}", Vertical)

        try:
            warn = self.app._current_theme_dict.get("warning", "#e6b450")
            succ = self.app._current_theme_dict.get("success", "#aad84c")
            txt_m = self.app._current_theme_dict.get("text_muted", "#686868")
        except Exception:
            warn, succ, txt_m = "#e6b450", "#aad84c", "#686868"

        detail_content = (
            f"  [{warn}]Hash[/{warn}]    [{txt_m}]{commit.hash7}  {commit.full_hash}[/{txt_m}]\n"
            f"  [{succ}]Author[/{succ}]  [{txt_m}]{escape(commit.author)} <{escape(commit.author_email)}>[/{txt_m}]\n"
            f"  [{warn}]Date[/{warn}]    [{txt_m}]{commit.date}  ({self._format_time_ago(commit.date)})[/{txt_m}]\n"
            f"  [{warn}]Msg[/{warn}]     [{txt_m}]{escape(commit.message)}[/{txt_m}]\n"
            f"  [{succ}]Files[/{succ}]   [{txt_m}]loading...[/{txt_m}]"
        )
        detail.update(detail_content)

        actions.remove_children()
        actions.mount(
            Static("", classes="gm-divider"),
            Horizontal(
                Button("Copy Hash", id=f"gm-copy-{idx}"),
                Button("Open Files", id=f"gm-open-{idx}"),
                classes="gm-actions-row",
            ),
        )

        expanded.display = True
        expanded.scroll_visible()

        self._load_changed_files(idx, commit)

    # ── Key / mouse event handling ────────────────────────────────────────

    def on_key(self, event: Key) -> None:
        if self.query_one("#gm-message", Input).has_focus:
            return
        if event.key == "up":
            self._focus_commit(self._focused_index - 1)
            event.prevent_default()
        elif event.key == "down":
            self._focus_commit(self._focused_index + 1)
            event.prevent_default()
        elif event.key == "enter":
            self._toggle_expand(self._focused_index)
            event.prevent_default()

    def on_click(self, event: Click) -> None:
        if isinstance(event.widget, Button):
            return
        widget = event.widget
        while widget:
            if widget.id and widget.id.startswith("gm-commit-"):
                suffix = widget.id.removeprefix("gm-commit-")
                if suffix.isdigit():
                    idx = int(suffix)
                    self._focus_commit(idx)
                    self._toggle_expand(idx)
                    event.stop()
                    return
            widget = getattr(widget, "parent", None)

    # ── Commit button handlers ────────────────────────────────────────────

    @on(Input.Changed)
    def _on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "gm-message":
            self._update_commit_buttons()

    @on(Button.Pressed, "#gm-commit-btn")
    def _on_commit_pressed(self) -> None:
        self._do_commit(do_push=False)

    @on(Button.Pressed, "#gm-push-btn")
    def _on_push_pressed(self) -> None:
        self._do_commit(do_push=True)

    def _update_commit_buttons(self) -> None:
        msg = self.query_one("#gm-message", Input).value.strip()
        disabled = not msg
        self.query_one("#gm-commit-btn", Button).disabled = disabled
        self.query_one("#gm-push-btn", Button).disabled = disabled

    def _do_commit(self, do_push: bool) -> None:
        msg = self.query_one("#gm-message", Input).value.strip()
        if not msg:
            self.query_one("#gm-error", Static).update("Message is required")
            return
        self._run_commit_work(msg, do_push)

    @work(exclusive=True)
    async def _run_commit_work(self, msg: str, do_push: bool) -> None:
        from main import _run_git, _git_commit, _git_push

        loop = asyncio.get_running_loop()

        stage_ok, stage_msg = await loop.run_in_executor(
            None, _run_git, self.repo_path, ["add", "-A"]
        )
        if not stage_ok:
            self.notify(f"[b]Stage failed[/b]\n{stage_msg}", severity="error", timeout=5)
            self.query_one("#gm-error", Static).update(f"Stage: {stage_msg}")
            return

        commit_ok, commit_msg = await loop.run_in_executor(
            None, _git_commit, msg, self.repo_path
        )
        if not commit_ok:
            self.notify(f"[b]Commit failed[/b]\n{commit_msg}", severity="error", timeout=5)
            self.query_one("#gm-error", Static).update(f"Commit: {commit_msg}")
            return

        if do_push:
            from screens import ConfirmScreen
            confirmed = await self.push_screen_wait(
                ConfirmScreen("Push commits to remote?")
            )
            if not confirmed:
                self.notify("Committed locally (push cancelled)", timeout=3)
                self._post_commit_success()
                return

            push_ok, push_msg = await loop.run_in_executor(
                None, _git_push, self.repo_path
            )
            if not push_ok:
                self.notify(f"[b]Push failed[/b]\n{push_msg}", severity="error", timeout=5)
                self.query_one("#gm-error", Static).update(f"Push: {push_msg}")
                return
            self.notify("[b #aad84c]\u2713 Committed & pushed[/b #aad84c]", timeout=3)
        else:
            self.notify("[b #aad84c]\u2713 Committed[/b #aad84c]", timeout=3)

        self._post_commit_success()

    def _post_commit_success(self) -> None:
        self.query_one("#gm-message", Input).value = ""
        self.query_one("#gm-error", Static).update("")
        self._update_commit_buttons()
        self._expanded_index = None
        self._prepend_new_commit()

        from main import _git_branch
        _git_branch.cache_clear()
        try:
            main_screen = next(
                (s for s in self.app.get_screen_stack()
                 if s.__class__.__name__ == "MainScreen"),
                None,
            )
            if main_screen:
                from textual.widgets import DirectoryTree, Static
                dt = main_screen.query_one(DirectoryTree)
                if hasattr(dt, "_refresh_git_status"):
                    dt._refresh_git_status()
                    dt.refresh()
                try:
                    main_screen.query_one("#sb-branch", Static).update(_git_branch())
                except Exception:
                    pass
        except Exception:
            pass

    def _prepend_new_commit(self) -> None:
        try:
            result = subprocess.run(
                ["git", "log", "--format=%H|%h|%s|%an|%ae|%ai", "-n", "1"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=5,
            )
            line = result.stdout.strip()
            if not line:
                return
            parts = line.split("|")
            if len(parts) < 6:
                return
            full_hash, hash7, message, author, email, date = parts[:6]
            commit = CommitDetail(hash7, full_hash, message, author, email, date)
            self.commits.insert(0, commit)

            list_container = self.query_one("#gm-list", ScrollableContainer)
            list_container.mount(self._build_commit_item(0, commit), before=0)
            self._focus_commit(0)
        except Exception:
            pass

    # ── Changed files (lazy-loaded) ────────────────────────────────────────

    @work(exclusive=False)
    async def _load_changed_files(self, idx: int, commit: CommitDetail) -> None:
        self._loading_files_for = idx
        loop = asyncio.get_running_loop()
        files = await loop.run_in_executor(None, commit.get_files, self.repo_path)
        if self._loading_files_for == idx and self._expanded_index == idx:
            self._update_detail_files(idx, files)

    def _update_detail_files(self, idx: int, files: list) -> None:
        try:
            succ = self.app._current_theme_dict.get("success", "#aad84c")
            err = self.app._current_theme_dict.get("error", "#ef7177")
            txt_m = self.app._current_theme_dict.get("text_muted", "#686868")
        except Exception:
            succ, err, txt_m = "#aad84c", "#ef7177", "#686868"

        detail = self.query_one(f"#gm-detail-{idx}", Static)
        if not files:
            new_text = detail.content.split("\n")[:-1]
            new_text.append(f"  [{succ}]Files[/{succ}]   [{txt_m}]no files changed[/{txt_m}]")
            detail.update("\n".join(new_text))
            return

        lines = detail.content.split("\n")[:-1]
        file_lines = []
        for fname, adds, dels in files[:30]:
            parts = []
            if adds:
                parts.append(f"[{succ}]+{adds}[/{succ}]")
            if dels:
                parts.append(f"[{err}]-{dels}[/{err}]")
            stats = " ".join(parts)
            file_lines.append(f"    [{txt_m}]\u25b8 {escape(fname)}[/{txt_m}]  {stats}")

        if len(files) > 30:
            file_lines.append(f"    [{txt_m}]... +{len(files) - 30} more[/{txt_m}]")

        new_text = "\n".join(lines + file_lines)
        detail.update(new_text)

    # ── Actions ────────────────────────────────────────────────────────────

    def action_close(self) -> None:
        self.dismiss()

    def action_toggle(self) -> None:
        self._toggle_expand(self._focused_index)

    def action_focus_up(self) -> None:
        self._focus_commit(self._focused_index - 1)

    def action_focus_down(self) -> None:
        self._focus_commit(self._focused_index + 1)

    def action_focus_input(self) -> None:
        self.query_one("#gm-message", Input).focus()

    def action_refresh(self) -> None:
        self._expanded_index = None
        self._load_git_data()
        self.notify("Git data refreshed", timeout=1)

    def action_copy_hash(self) -> None:
        commit = self._get_focused_commit()
        if not commit:
            return
        self.app.copy_to_clipboard(commit.full_hash)
        self.notify(f"Copied: {commit.hash7}", timeout=2)

    def action_open_files(self) -> None:
        commit = self._get_focused_commit()
        if not commit:
            return
        files = commit.get_files(self.repo_path)
        if files:
            names = ", ".join(f[0] for f in files[:5])
            if len(files) > 5:
                names += f" +{len(files) - 5} more"
            self.notify(f"Files: {names}", timeout=4)
        else:
            self.notify("No files changed in this commit", timeout=2)
