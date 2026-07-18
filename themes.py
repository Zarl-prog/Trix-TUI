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
    },
    {
        "name": "Solarized Dark",
        "background": "#002b36",
        "surface": "#073642",
        "panel": "#073642",
        "border": "#586e75",
        "border_focused": "#268bd2",
        "text": "#839496",
        "text_muted": "#586e75",
        "accent": "#268bd2",
        "accent_alt": "#2aa198",
        "success": "#859900",
        "warning": "#b58900",
        "error": "#dc322f",
        "line_number": "#586e75",
        "cursor_line": "#073642",
        "scrollbar": "#586e75",
        "scrollbar_thumb": "#268bd2",
    },
    {
        "name": "Midnight Blue",
        "background": "#0d1117",
        "surface": "#090d14",
        "panel": "#090d14",
        "border": "#1e2a3a",
        "border_focused": "#58a6ff",
        "text": "#c9d1d9",
        "text_muted": "#484f58",
        "accent": "#58a6ff",
        "accent_alt": "#79c0ff",
        "success": "#3fb950",
        "warning": "#d29922",
        "error": "#f85149",
        "line_number": "#484f58",
        "cursor_line": "#161b22",
        "scrollbar": "#1e2a3a",
        "scrollbar_thumb": "#58a6ff",
    },
    {
        "name": "Rosé Pine",
        "background": "#191724",
        "surface": "#1f1d2e",
        "panel": "#1f1d2e",
        "border": "#403d52",
        "border_focused": "#c4a7e7",
        "text": "#e0def4",
        "text_muted": "#6e6a86",
        "accent": "#c4a7e7",
        "accent_alt": "#ebbcba",
        "success": "#31748f",
        "warning": "#f6c177",
        "error": "#eb6f92",
        "line_number": "#6e6a86",
        "cursor_line": "#26233a",
        "scrollbar": "#403d52",
        "scrollbar_thumb": "#c4a7e7",
    },
]


def _safe_color(val, default: str = "#888888") -> str:
    """Safely extract a 6-char hex color, handling None and 8-char #rrggbbaa."""
    if val is None:
        return default
    s = str(val).strip()
    if s.startswith("#"):
        # Strip alpha channel: #rrggbbaa → #rrggbb
        if len(s) == 9:
            return s[:7]
        if len(s) == 7:
            return s
    return default


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
        except Exception as e:
            import sys
            print(f"Warning: Failed to load custom theme {f}: {e}", file=sys.stderr)
    return themes


def get_all_themes() -> list[dict]:
    themes = []

    # 1. Load Ayu themes from local JSON
    try:
        data = json.loads((Path(__file__).parent / "ayu.json").read_text())
        for t in data["themes"]:
            s = t["style"]
            name = t["name"]

            bg    = _safe_color(s.get("background"),                  "#313337")
            surf  = _safe_color(s.get("surface.background"),          "#1f2127")
            pan   = _safe_color(s.get("elevated_surface.background"), "#1f2127")
            txt   = _safe_color(s.get("text"),                        "#bfbdb6")
            txt_m = _safe_color(s.get("text.muted"),                  "#8a8986")
            acc   = _safe_color(s.get("text.accent"),                 "#5ac1fe")
            err   = _safe_color(s.get("error"),                       "#ef7177")
            suc   = _safe_color(s.get("success"),                     "#aad84c")
            war   = _safe_color(s.get("warning"),                     "#e6b450")
            brd   = _safe_color(s.get("border"),                      "#3f4043")
            brd_f = _safe_color(s.get("panel.focused_border"),        acc)
            acc_a = _safe_color(s.get("terminal.ansi.bright_magenta"), "#39bae5")
            ln    = _safe_color(s.get("editor.line_number"),          "#4b4c4e")
            cl    = _safe_color(s.get("editor.active_line.background"), "#1f2127")
            sb    = _safe_color(s.get("scrollbar.track.border"),      "#3f4043")
            sbt   = _safe_color(s.get("scrollbar.thumb.background"),  "#5ac1fe")

            theme_dict = {
                "name":           name,
                "background":     bg,
                "surface":        surf,
                "panel":          pan,
                "border":         brd,
                "border_focused": brd_f,
                "text":           txt,
                "text_muted":     txt_m,
                "accent":         acc,
                "accent_alt":     acc_a,
                "success":        suc,
                "warning":        war,
                "error":          err,
                "line_number":    ln,
                "cursor_line":    cl,
                "scrollbar":      sb,
                "scrollbar_thumb": sbt,
            }
            themes.append(theme_dict)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to load Ayu themes: {e}")

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


def build_theme_css(theme: dict) -> str:
    """Generate dynamic CSS overrides for a given theme dict."""
    bg     = theme.get("background",     "#0d1016")
    surf   = theme.get("surface",        "#1f2127")
    panel  = theme.get("panel",          "#1f2127")
    brd    = theme.get("border",         "#3f4043")
    brd_f  = theme.get("border_focused", "#5ac1fe")
    txt    = theme.get("text",           "#bfbdb6")
    txt_m  = theme.get("text_muted",     "#8a8986")
    acc    = theme.get("accent",         "#5ac1fe")
    acc_a  = theme.get("accent_alt",     "#39bae5")
    succ   = theme.get("success",        "#aad84c")
    warn   = theme.get("warning",        "#e6b450")
    err    = theme.get("error",          "#ef7177")
    ln     = theme.get("line_number",    "#4b4c4e")
    cl     = theme.get("cursor_line",    "#1f2127")
    sb     = theme.get("scrollbar",      "#3f4043")
    sbt    = theme.get("scrollbar_thumb", "#5ac1fe")

    return f"""
    Screen {{ background: {bg}; }}
    #header {{ background: {bg}; }}
    #hdr-brand {{ color: {acc}; }}
    #hdr-folder {{ color: {txt_m}; }}
    #hdr-theme {{ color: {txt_m}; }}
    #main-area {{ background: {bg}; }}
    LayoutContainer, Container, #files-panel, #editor-panel {{ background: {bg}; }}
    #files-panel.--panel-active {{ border-left: tall {acc}; }}
    #editor-panel.--panel-active {{ border-left: tall {acc}; }}
    DirectoryTree {{ background: {bg}; scrollbar-color: {sbt}; scrollbar-background: {bg}; }}
    DirectoryTree > .tree--cursor {{ background: {acc}; color: {bg}; }}
    DirectoryTree > .tree--highlight {{ background: {acc}; color: {bg}; }}
    DirectoryTree > .tree--guides {{ color: {brd}; }}
    TextArea {{ background: {bg}; color: {txt}; scrollbar-color: {sbt}; scrollbar-background: {bg}; }}
    TextArea .text-area--gutter {{ background: {bg}; color: {ln}; }}
    TextArea .text-area--gutter-active {{ background: {bg}; color: {acc}; }}
    TextArea .text-area--cursor {{ background: {acc}; }}
    TextArea .text-area--cursor-line {{ background: {cl}; }}
    #bottom-bar {{ background: {surf}; }}
    .kb-key {{ color: {acc}; }}
    .kb-desc {{ color: {txt_m}; }}
    #sb-unsaved {{ color: {warn}; }}
    #sb-lang {{ color: {txt_m}; }}
    #sb-cursor {{ color: {txt_m}; }}
    #sb-branch {{ color: {succ}; }}
    Divider {{ background: {brd}; }}
    Divider:hover {{ background: {acc}; }}
    TabStrip {{ background: {bg}; }}
    .tab-item {{ color: {txt_m}; background: {bg}; }}
    .tab-item.--tab-active {{ color: {txt}; background: {surf}; }}
    .tab-item.--tab-unsaved {{ color: {warn}; }}
    WelcomePanel {{ background: {bg}; }}
    #welcome-header {{ color: {acc}; }}
    #welcome-tagline {{ color: {txt_m}; }}
    #welcome-recent-label {{ color: {txt_m}; }}
    #welcome-recent-list {{ background: {bg}; }}
    #welcome-recent-list > ListItem {{ background: {bg}; color: {txt}; }}
    #welcome-recent-list > ListItem:hover {{ background: {surf}; color: {acc}; }}
    #welcome-hint {{ color: {brd}; }}
    Toast {{ background: {surf}; border-left: tall {acc}; color: {txt}; }}
    Toast.-information {{ border-left: tall {acc}; }}
    Toast.-warning {{ border-left: tall {warn}; background: {surf}; }}
    Toast.-error {{ border-left: tall {err}; background: {surf}; }}
    Toast .toast--title {{ color: {acc}; }}
    Toast.-warning .toast--title {{ color: {warn}; }}
    Toast.-error .toast--title {{ color: {err}; }}
    """
