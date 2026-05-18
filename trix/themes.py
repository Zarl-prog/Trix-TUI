from pathlib import Path
import json

from textual.theme import Theme


def _load_themes() -> list[dict]:
    try:
        data = json.loads((Path(__file__).parent.parent / "ayu.json").read_text())
    except Exception:
        return []
    result = []
    for t in data["themes"]:
        s = t["style"]
        name = t["name"]
        slug = name.lower().replace(" ", "-")
        dark = t.get("appearance", "dark") == "dark"
        theme = Theme(
            name=slug,
            primary=s.get("text.accent", "#5ac1fe")[:7],
            secondary=s.get("text.muted", "#8a8986")[:7],
            accent=s.get("text.accent", "#5ac1fe")[:7],
            background=s.get("background", "#313337")[:7],
            surface=s.get("surface.background", "#1f2127")[:7],
            panel=s.get("elevated_surface.background", "#1f2127")[:7],
            foreground=s.get("text", "#bfbdb6")[:7],
            error=s.get("error", "#ef7177")[:7],
            success=s.get("success", "#aad84c")[:7],
            warning=s.get("warning", "#e6b450")[:7],
            dark=dark,
        )
        result.append({"name": name, "slug": slug, "theme": theme})
    return result


THEMES: list[dict] = _load_themes() or [
    {"name": "Ayu Dark", "slug": "textual-dark", "theme": None}
]
