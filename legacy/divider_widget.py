from textual.widgets import Static
from themes import register_css_template

DIVIDER_CSS = """
Divider {
    width: 1;
    height: 100%;
    background: #1a1d23;
}
"""
register_css_template("divider", DIVIDER_CSS)


class Divider(Static):
    """Subtle 1-cell divider between panels (non-interactive in Harlequin style)."""

    DEFAULT_CSS = DIVIDER_CSS

    def __init__(self, left_id: str, right_id: str, **kwargs):
        # The IDs are kept for architectural consistency but interaction is removed
        super().__init__("", **kwargs)
        self._left_id = left_id
        self._right_id = right_id
