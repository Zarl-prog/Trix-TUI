from textual.events import MouseDown, MouseMove, MouseUp
from textual.widgets import Static
from themes import register_css_template

DIVIDER_CSS = """
Divider {
    width: 1;
    height: 100%;
    background: #1a1d23;
}
Divider:hover {
    background: #5ac1fe;
}
"""
register_css_template("divider", DIVIDER_CSS)


class Divider(Static):
    """Draggable 1-cell divider between panels."""

    DEFAULT_CSS = DIVIDER_CSS

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
        if not self._dragging or not self.parent:
            return
        # Calculate percentage of total width from mouse position
        parent = self.parent
        if not hasattr(parent, "region") or not parent.region:
            return
        total_w = parent.region.width
        if total_w <= 0:
            return
        # Use screen-relative mouse X column relative to parent container X column
        mouse_x_relative = event.screen_x - parent.region.x
        x_pct = (mouse_x_relative / total_w) * 100
        left_pct = max(10, min(x_pct - 1, 70))
        right_pct = max(10, min(100 - x_pct, 70))
        self.parent.query_one(f"#{self._left_id}").styles.width = f"{left_pct}%"
        self.parent.query_one(f"#{self._right_id}").styles.width = f"{right_pct}%"
