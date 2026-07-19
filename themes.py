from pathlib import Path

FAMOUS_THEMES = [
    {
        "name": "Ayu Dark",
        "background": "#0d1016",
        "surface": "#1f2127",
        "panel": "#1f2127",
        "border": "#3f4043",
        "border_focused": "#5ac1fe",
        "text": "#bfbdb6",
        "text_muted": "#8a8986",
        "accent": "#5ac1fe",
        "accent_alt": "#39bae5",
        "success": "#aad84c",
        "warning": "#feb454",
        "error": "#ef7177",
        "line_number": "#4b4c4e",
        "cursor_line": "#1f2127",
        "scrollbar": "#3f4043",
        "scrollbar_thumb": "#5ac1fe",
    },
    {
        "name": "Ayu Mirage",
        "background": "#242835",
        "surface": "#1f232a",
        "panel": "#1f232a",
        "border": "#53565d",
        "border_focused": "#72cffe",
        "text": "#cccac2",
        "text_muted": "#9a9a98",
        "accent": "#72cffe",
        "accent_alt": "#2b6c7b",
        "success": "#d5fe80",
        "warning": "#fecf72",
        "error": "#f18779",
        "line_number": "#575c6b",
        "cursor_line": "#1f232a",
        "scrollbar": "#53565d",
        "scrollbar_thumb": "#72cffe",
    },
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
    ]


def get_all_themes() -> list[dict]:
    return FAMOUS_THEMES


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
