from pathlib import Path
import json

FAMOUS_THEMES = [
    {
        "name": "Dracula",
        "background": "#282a36",
        "surface": "#1e1f29",
        "panel": "#1e1f29",
        "border": "#44475a",
        "border_focused": "#bd93f9",
        "text": "#f8f8f2",
        "text_muted": "#6272a4",
        "accent": "#bd93f9",
        "accent_alt": "#ff79c6",
        "success": "#50fa7b",
        "warning": "#ffb86c",
        "error": "#ff5555",
        "line_number": "#6272a4",
        "cursor_line": "#44475a",
        "scrollbar": "#44475a",
        "scrollbar_thumb": "#bd93f9",
    },
    {
        "name": "Nord",
        "background": "#2e3440",
        "surface": "#242933",
        "panel": "#242933",
        "border": "#3b4252",
        "border_focused": "#88c0d0",
        "text": "#d8dee9",
        "text_muted": "#4c566a",
        "accent": "#88c0d0",
        "accent_alt": "#81a1c1",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "error": "#bf616a",
        "line_number": "#4c566a",
        "cursor_line": "#3b4252",
        "scrollbar": "#3b4252",
        "scrollbar_thumb": "#88c0d0",
    },
    {
        "name": "Monokai",
        "background": "#272822",
        "surface": "#1e1f1c",
        "panel": "#1e1f1c",
        "border": "#3e3d32",
        "border_focused": "#f92672",
        "text": "#f8f8f2",
        "text_muted": "#75715e",
        "accent": "#f92672",
        "accent_alt": "#a6e22e",
        "success": "#a6e22e",
        "warning": "#f4bf75",
        "error": "#f92672",
        "line_number": "#75715e",
        "cursor_line": "#3e3d32",
        "scrollbar": "#3e3d32",
        "scrollbar_thumb": "#f92672",
    },
    {
        "name": "Gruvbox Dark",
        "background": "#282828",
        "surface": "#1d2021",
        "panel": "#1d2021",
        "border": "#3c3836",
        "border_focused": "#fe8019",
        "text": "#ebdbb2",
        "text_muted": "#928374",
        "accent": "#fe8019",
        "accent_alt": "#fabd2f",
        "success": "#b8bb26",
        "warning": "#fabd2f",
        "error": "#fb4934",
        "line_number": "#928374",
        "cursor_line": "#3c3836",
        "scrollbar": "#3c3836",
        "scrollbar_thumb": "#fe8019",
    },
    {
        "name": "One Dark",
        "background": "#282c34",
        "surface": "#21252b",
        "panel": "#21252b",
        "border": "#3e4451",
        "border_focused": "#61afef",
        "text": "#abb2bf",
        "text_muted": "#5c6370",
        "accent": "#61afef",
        "accent_alt": "#c678dd",
        "success": "#98c379",
        "warning": "#d19a66",
        "error": "#e06c75",
        "line_number": "#5c6370",
        "cursor_line": "#2c313c",
        "scrollbar": "#3e4451",
        "scrollbar_thumb": "#61afef",
    },
    {
        "name": "Tokyo Night",
        "background": "#1a1b26",
        "surface": "#16161e",
        "panel": "#16161e",
        "border": "#383e5a",
        "border_focused": "#7aa2f7",
        "text": "#a9b1d6",
        "text_muted": "#565f89",
        "accent": "#7aa2f7",
        "accent_alt": "#bb9af3",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
        "line_number": "#565f89",
        "cursor_line": "#292e42",
        "scrollbar": "#383e5a",
        "scrollbar_thumb": "#7aa2f7",
    },
    {
        "name": "Catppuccin",
        "background": "#1e1e2e",
        "surface": "#181825",
        "panel": "#181825",
        "border": "#313244",
        "border_focused": "#cba6f7",
        "text": "#cdd6f4",
        "text_muted": "#585b70",
        "accent": "#cba6f7",
        "accent_alt": "#f5c2e7",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "line_number": "#585b70",
        "cursor_line": "#313244",
        "scrollbar": "#313244",
        "scrollbar_thumb": "#cba6f7",
    }
]


def load_custom_themes() -> list[dict]:
    themes = []
    p = Path.home() / ".trix" / "themes"
    p.mkdir(parents=True, exist_ok=True)
    for f in p.glob("*.json"):
        try:
            theme_dict = json.loads(f.read_text())
            required_keys = [
                "name", "background", "surface", "panel", "border",
                "border_focused", "text", "text_muted", "accent", "accent_alt",
                "success", "warning", "error", "line_number", "cursor_line",
                "scrollbar", "scrollbar_thumb"
            ]
            for key in required_keys:
                if key not in theme_dict:
                    theme_dict[key] = theme_dict.get("background", "#1f2127")
            themes.append(theme_dict)
        except Exception:
            pass
    return themes


def get_all_themes() -> list[dict]:
    themes = []
    
    # 1. Load Ayu themes from local JSON
    try:
        data = json.loads((Path(__file__).parent / "ayu.json").read_text())
        for t in data["themes"]:
            s = t["style"]
            name = t["name"]
            
            bg = s.get("background", "#313337")[:7]
            surf = s.get("surface.background", "#1f2127")[:7]
            pan = s.get("elevated_surface.background", "#1f2127")[:7]
            txt = s.get("text", "#bfbdb6")[:7]
            txt_mut = s.get("text.muted", "#8a8986")[:7]
            acc = s.get("text.accent", "#5ac1fe")[:7]
            err = s.get("error", "#ef7177")[:7]
            suc = s.get("success", "#aad84c")[:7]
            war = s.get("warning", "#e6b450")[:7]
            
            theme_dict = {
                "name": name,
                "background": bg,
                "surface": surf,
                "panel": pan,
                "border": s.get("border", "#3f4043")[:7],
                "border_focused": s.get("panel.focused_border", "#5ac1fe")[:7],
                "text": txt,
                "text_muted": txt_mut,
                "accent": acc,
                "accent_alt": s.get("terminal.ansi.bright_magenta", "#39bae5")[:7],
                "success": suc,
                "warning": war,
                "error": err,
                "line_number": s.get("editor.line_number", "#4b4c4e")[:7],
                "cursor_line": s.get("editor.active_line.background", "#1f2127")[:7],
                "scrollbar": s.get("scrollbar.track.border", "#3f4043")[:7],
                "scrollbar_thumb": s.get("scrollbar.thumb.background", "#5ac1fe")[:7],
            }
            themes.append(theme_dict)
    except Exception:
        pass

    # 2. Load famous themes
    themes.extend(FAMOUS_THEMES)

    # 3. Load custom themes
    themes.extend(load_custom_themes())

    # De-duplicate by name
    seen = set()
    unique_themes = []
    for t in themes:
        if t["name"] not in seen:
            seen.add(t["name"])
            unique_themes.append(t)

    return unique_themes


THEMES: list[dict] = get_all_themes()


CSS_TEMPLATES: dict[str, str] = {}

def register_css_template(name: str, css: str) -> None:
    CSS_TEMPLATES[name] = css


