from textual.events import MouseDown, MouseMove, MouseUp
from textual.widgets import Static
from themes import register_css_template

DIVIDER_CSS = """
Divider {
    width: 1;
    height: 100%;
    background: var(--border);
}
Divider:hover { background: var(--accent); }
"""
register_css_template("divider", DIVIDER_CSS)


class Divider(Static):
    """Draggable 1-cell divider between two panels."""

    DEFAULT_CSS = DIVIDER_CSS

    def __init__(self, left_id: str, right_id: str, **kwargs):
        super().__init__("", **kwargs)
        self._left_id = left_id
        self._right_id = right_id
        self._dragging = False
        self._start_x = 0
        self._left_w = 0
        self._right_w = 0

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self._start_x = event.screen_x
        self._left_w = self.screen.query_one(f"#{self._left_id}").size.width
        self._right_w = self.screen.query_one(f"#{self._right_id}").size.width
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: MouseMove) -> None:
        if not self._dragging:
            return
        _MIN = {"files-panel": 0.10, "editor-panel": 0.20, "terminal-panel": 0.20}
        total = self.app.size.width
        delta = event.screen_x - self._start_x
        new_left = max(int(total * _MIN.get(self._left_id, 0.10)), self._left_w + delta)
        new_right = max(int(total * _MIN.get(self._right_id, 0.20)), self._right_w - delta)
        self.screen.query_one(f"#{self._left_id}").styles.width = new_left
        self.screen.query_one(f"#{self._right_id}").styles.width = new_right
        event.stop()

    def on_mouse_up(self, event: MouseUp) -> None:
        self._dragging = False
        self.release_mouse()
        event.stop()
