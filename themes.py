from pathlib import Path

FAMOUS_THEMES = [
    {
        "name": "Ayu Dark",
        "background": "#0d1016",
        "surface": "#1a1d23",
        "panel": "#131721",
        "border": "#2e3038",
        "border_focused": "#5ac1fe",
        "text": "#bfbdb6",
        "text_muted": "#686868",
        "accent": "#5ac1fe",
        "accent_alt": "#39bae5",
        "success": "#aad84c",
        "warning": "#feb454",
        "error": "#ef7177",
        "line_number": "#3a3c42",
        "cursor_line": "#15181f",
        "scrollbar": "#2e3038",
        "scrollbar_thumb": "#5ac1fe",
        "dark": True,
    },
    {
        "name": "Ayu Mirage",
        "background": "#1e2330",
        "surface": "#1a1e2a",
        "panel": "#171b24",
        "border": "#3e4251",
        "border_focused": "#72cffe",
        "text": "#cccac2",
        "text_muted": "#737982",
        "accent": "#72cffe",
        "accent_alt": "#2b6c7b",
        "success": "#d5fe80",
        "warning": "#fecf72",
        "error": "#f18779",
        "line_number": "#4a4f5e",
        "cursor_line": "#1a1e2a",
        "scrollbar": "#3e4251",
        "scrollbar_thumb": "#72cffe",
        "dark": True,
    },
    {
        "name": "Dracula",
        "background": "#1e1f29",
        "surface": "#242536",
        "panel": "#2a2b3e",
        "border": "#3d3f5a",
        "border_focused": "#bd93f9",
        "text": "#f8f8f2",
        "text_muted": "#6b7094",
        "accent": "#bd93f9",
        "accent_alt": "#ff79c6",
        "success": "#50fa7b",
        "warning": "#ffb86c",
        "error": "#ff5555",
        "line_number": "#4a4d6e",
        "cursor_line": "#282936",
        "scrollbar": "#3d3f5a",
        "scrollbar_thumb": "#bd93f9",
        "dark": True,
    },
    {
        "name": "One Dark",
        "background": "#21252b",
        "surface": "#282c34",
        "panel": "#1e2229",
        "border": "#3a3f4b",
        "border_focused": "#61afef",
        "text": "#abb2bf",
        "text_muted": "#5c6370",
        "accent": "#61afef",
        "accent_alt": "#c678dd",
        "success": "#98c379",
        "warning": "#d19a66",
        "error": "#e06c75",
        "line_number": "#3a3f4b",
        "cursor_line": "#2c313c",
        "scrollbar": "#3a3f4b",
        "scrollbar_thumb": "#61afef",
        "dark": True,
    },
    {
        "name": "Tokyo Night",
        "background": "#14151f",
        "surface": "#1a1b2e",
        "panel": "#20223a",
        "border": "#363b54",
        "border_focused": "#7aa2f7",
        "text": "#a9b1d6",
        "text_muted": "#545c7e",
        "accent": "#7aa2f7",
        "accent_alt": "#bb9af3",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
        "line_number": "#363b54",
        "cursor_line": "#1e2038",
        "scrollbar": "#363b54",
        "scrollbar_thumb": "#7aa2f7",
        "dark": True,
    },
    {
        "name": "Midnight Blue",
        "background": "#0a0e17",
        "surface": "#0f1623",
        "panel": "#161d2f",
        "border": "#1e2d4a",
        "border_focused": "#58a6ff",
        "text": "#c9d1d9",
        "text_muted": "#484f58",
        "accent": "#58a6ff",
        "accent_alt": "#79c0ff",
        "success": "#3fb950",
        "warning": "#d29922",
        "error": "#f85149",
        "line_number": "#1e2d4a",
        "cursor_line": "#0f1623",
        "scrollbar": "#1e2d4a",
        "scrollbar_thumb": "#58a6ff",
        "dark": True,
    },
    {
        "name": "Catppuccin Mocha",
        "background": "#11111b",
        "surface": "#181825",
        "panel": "#1e1e2e",
        "border": "#313244",
        "border_focused": "#89b4fa",
        "text": "#cdd6f4",
        "text_muted": "#6c7086",
        "accent": "#89b4fa",
        "accent_alt": "#cba6f7",
        "success": "#a6e3a1",
        "warning": "#fab387",
        "error": "#f38ba8",
        "line_number": "#45475a",
        "cursor_line": "#1e1e2e",
        "scrollbar": "#313244",
        "scrollbar_thumb": "#89b4fa",
        "dark": True,
    },
    {
        "name": "Catppuccin Macchiato",
        "background": "#151524",
        "surface": "#1d1d32",
        "panel": "#1f1f38",
        "border": "#363b54",
        "border_focused": "#7aa2f7",
        "text": "#cad3f5",
        "text_muted": "#6e7391",
        "accent": "#7aa2f7",
        "accent_alt": "#c6a0f6",
        "success": "#a6da95",
        "warning": "#eed49f",
        "error": "#ed8796",
        "line_number": "#363b54",
        "cursor_line": "#1f1f38",
        "scrollbar": "#363b54",
        "scrollbar_thumb": "#7aa2f7",
        "dark": True,
    },
    {
        "name": "Everforest Dark",
        "background": "#1e2326",
        "surface": "#252c31",
        "panel": "#2d353b",
        "border": "#3d484d",
        "border_focused": "#a7c080",
        "text": "#d3c6aa",
        "text_muted": "#6f7b7d",
        "accent": "#a7c080",
        "accent_alt": "#e69875",
        "success": "#a7c080",
        "warning": "#dbbc7f",
        "error": "#f85552",
        "line_number": "#3d484d",
        "cursor_line": "#252c31",
        "scrollbar": "#3d484d",
        "scrollbar_thumb": "#a7c080",
        "dark": True,
    },
    {
        "name": "Nord",
        "background": "#1e2129",
        "surface": "#242831",
        "panel": "#2b2f3a",
        "border": "#3b4252",
        "border_focused": "#81a1c1",
        "text": "#d8dee9",
        "text_muted": "#616c82",
        "accent": "#81a1c1",
        "accent_alt": "#b48ead",
        "success": "#a3be8c",
        "warning": "#d08770",
        "error": "#bf616a",
        "line_number": "#3b4252",
        "cursor_line": "#242831",
        "scrollbar": "#3b4252",
        "scrollbar_thumb": "#81a1c1",
        "dark": True,
    },
    ]

THEMES: list[dict] = FAMOUS_THEMES

CSS_TEMPLATES: dict[str, str] = {}

def register_css_template(name: str, css: str) -> None:
    CSS_TEMPLATES[name] = css


def build_git_menu_css(theme: dict) -> str:
    bg     = theme.get("background",     "#0d1016")
    surf   = theme.get("surface",        "#1a1d23")
    panel  = theme.get("panel",          "#131721")
    brd    = theme.get("border",         "#2e3038")
    brd_f  = theme.get("border_focused", "#5ac1fe")
    txt    = theme.get("text",           "#bfbdb6")
    txt_m  = theme.get("text_muted",     "#686868")
    acc    = theme.get("accent",         "#5ac1fe")
    acc_a  = theme.get("accent_alt",     "#39bae5") or acc
    succ   = theme.get("success",        "#aad84c")
    warn   = theme.get("warning",        "#feb454")
    err    = theme.get("error",          "#ef7177")
    return f"""
GitMenuScreen {{
    align: center middle;
    background: #030508;
}}
#gm-popup {{
    width: 80%;
    height: 78%;
    min-width: 60;
    background: {panel};
    border: tall {acc};
    layout: vertical;
}}
#gm-header {{
    height: 3; dock: top;
    background: {bg};
    border-bottom: solid {brd};
    padding: 0 2; align: left middle;
}}
#gm-title  {{ width: auto; color: {acc}; text-style: bold; }}
#gm-meta   {{ width: 1fr; content-align: right middle; color: {txt_m}; }}

/* ── Body: single vertical column ── */
#gm-body {{
    height: 1fr;
    layout: vertical;
}}

/* ── Commit area ── */
#gm-commit-area {{
    height: auto;
    padding: 1 3 1 3;
    background: {bg};
    border-bottom: solid {brd};
    align: center middle;
    layout: vertical;
}}
#gm-message {{
    width: 100%; height: 3;
    border: solid {brd}; background: {panel}; color: {txt};
    padding: 0 1;
}}
#gm-message:focus {{ border: solid {brd_f}; }}
#gm-message::placeholder {{ color: {txt_m}; text-style: italic; }}
#gm-buttons {{
    height: auto; margin-top: 1;
    layout: horizontal;
    align: center middle;
}}
#gm-buttons Button {{
    margin: 0 1; padding: 0 3; min-width: 12;
}}
#gm-commit-btn {{
    background: {acc}; color: {bg}; text-style: bold;
    border: none;
}}
#gm-commit-btn:disabled {{ background: {brd}; color: {txt_m}; }}
#gm-push-btn {{
    background: transparent; color: {acc_a}; text-style: bold;
    border: solid {acc_a};
}}
#gm-push-btn:disabled {{ border-color: {brd}; color: {txt_m}; }}
#gm-error {{
    height: 1; color: {err}; text-align: center; margin-top: 1;
}}

/* ── History header + scrollable list ── */
#gm-history-header {{
    height: 3; padding: 0 2;
    color: {txt_m}; text-style: bold;
    background: {panel}; align: left middle;
}}
#gm-list {{
    height: 1fr;
    background: {panel};
    scrollbar-color: {acc}; scrollbar-background: {brd};
    scrollbar-size: 1 1;
    overflow-y: auto;
}}

/* ── Commit items (accordion) ── */
.gm-commit {{
    height: auto;
    background: {panel};
    border-bottom: solid {brd};
}}
.gm-commit.gm-focused {{
    border-left: tall {acc};
    background: {bg};
}}
.gm-commit:hover {{
    background: {bg};
}}
.gm-row {{
    height: auto;
    padding: 1 2;
}}
.gm-expanded {{
    height: auto;
    padding: 0 2 1 2;
    background: {surf};
}}
.gm-divider {{
    height: 1;
    border-top: solid {brd};
    margin: 0 0 1 0;
}}
.gm-actions-row {{
    height: auto;
    layout: horizontal;
    align: center middle;
    margin-top: 1;
}}
.gm-actions-row Button {{
    margin: 0 1; padding: 0 2; min-width: 8;
}}

/* ── Footer ── */
#gm-footer {{
    height: auto; min-height: 3; dock: bottom;
    background: {bg};
    border-top: solid {brd};
    padding: 1 2;
    layout: horizontal;
    align: left middle;
}}
#gm-footer > .gm-key {{
    width: auto; color: {acc}; text-style: bold;
    margin-right: 1;
}}
#gm-footer > .gm-key-desc {{
    width: auto; color: {txt_m};
    margin-right: 2;
}}
#gm-empty {{
    width: 100%; height: 100%;
    content-align: center middle; text-align: center;
    color: {txt_m};
}}
"""


def build_text_area_theme(theme: dict) -> "TextAreaTheme":
    from rich.style import Style
    from textual.widgets.text_area import TextAreaTheme

    acc    = theme.get("accent", "#5ac1fe")
    acc_a  = theme.get("accent_alt", "#39bae5") or acc
    succ   = theme.get("success", "#aad84c")
    warn   = theme.get("warning", "#feb454")
    err    = theme.get("error", "#ef7177")
    txt    = theme.get("text", "#bfbdb6")
    txt_m  = theme.get("text_muted", "#686868")
    bg     = theme.get("background", "#0d1016")
    surf   = theme.get("surface", "#1a1d23")
    cl     = theme.get("cursor_line", "#15181f")
    brd    = theme.get("border", "#2e3038")
    ln     = theme.get("line_number", "#3a3c42")

    def s(c: str) -> Style:
        return Style(color=c)

    def b(c: str) -> Style:
        return Style(color=c, bold=True)

    slug = theme["name"].lower().replace(" ", "-")
    name = f"trix-{slug}"

    return TextAreaTheme(
        name=name,
        base_style=s(txt),
        gutter_style=s(ln),
        cursor_style=s(acc),
        cursor_line_style=Style(bgcolor=cl),
        cursor_line_gutter_style=Style(bgcolor=cl),
        selection_style=Style(bgcolor="#1f4a6e"),
        bracket_matching_style=Style(bgcolor=brd),
        syntax_styles={
            "keyword":               s(acc_a),
            "keyword.function":      s(acc),
            "keyword.return":        s(acc),
            "keyword.operator":      s(acc),
            "string":                s(warn),
            "string.documentation":  s(warn),
            "comment":               s(txt_m),
            "number":                s(acc),
            "float":                 s(acc),
            "boolean":               s(succ),
            "function":              s(succ),
            "function.call":         s(succ),
            "class":                 s(succ),
            "type":                  s(acc_a),
            "type.builtin":          s(acc),
            "type.class":            s(succ),
            "method":                s(succ),
            "method.call":           s(succ),
            "operator":              s(txt),
            "conditional":           s(acc_a),
            "repeat":                s(acc_a),
            "include":               s(acc_a),
            "exception":             s(err),
            "tag":                   s(acc_a),
            "constant.builtin":      s(acc),
            "variable.builtin":      s(txt),
            "punctuation.bracket":   s(txt),
            "punctuation.delimiter": s(txt),
            "punctuation.special":   s(acc_a),
            "heading":               b(acc_a),
            "bold":                  Style(bold=True),
            "italic":                Style(italic=True),
            "strikethrough":         Style(strike=True),
        },
    )


def build_theme_css(theme: dict) -> str:
    bg     = theme.get("background",     "#0d1016")
    surf   = theme.get("surface",        "#1a1d23")
    panel  = theme.get("panel",          "#131721")
    brd    = theme.get("border",         "#2e3038")
    brd_f  = theme.get("border_focused", "#5ac1fe")
    txt    = theme.get("text",           "#bfbdb6")
    txt_m  = theme.get("text_muted",     "#686868")
    acc    = theme.get("accent",         "#5ac1fe")
    acc_a  = theme.get("accent_alt",     "#39bae5")
    succ   = theme.get("success",        "#aad84c")
    warn   = theme.get("warning",        "#feb454")
    err    = theme.get("error",          "#ef7177")
    ln     = theme.get("line_number",    "#3a3c42")
    cl     = theme.get("cursor_line",    "#15181f")
    sb     = theme.get("scrollbar",      "#2e3038")
    sbt    = theme.get("scrollbar_thumb", "#5ac1fe")

    return f"""
    Screen {{ background: {bg}; }}

    /* ── Header ── */
    #header {{ background: {bg}; border-bottom: solid {brd}; }}
    #hdr-brand {{ color: {acc}; }}
    #hdr-folder {{ color: {txt_m}; }}
    #hdr-theme {{ color: {txt_m}; }}

    /* ── Main area ── */
    #main-area {{ background: {bg}; }}
    LayoutContainer, Container, #files-panel, #editor-panel {{ background: {bg}; }}
    #files-panel.--panel-active {{ border-left: tall {acc}; }}
    #editor-panel.--panel-active {{ border-left: tall {acc}; }}

    /* ── File Tree ── */
    DirectoryTree {{ background: {bg}; scrollbar-color: {sbt}; scrollbar-background: {bg}; }}
    DirectoryTree > .tree--cursor {{ background: {acc}; color: {bg}; text-style: bold; }}
    DirectoryTree > .tree--highlight {{ background: {acc}; color: {bg}; }}
    DirectoryTree > .tree--guides {{ color: {brd}; }}

    /* ── Editor ── */
    TextArea {{ background: {bg}; color: {txt}; scrollbar-color: {sbt}; scrollbar-background: {bg}; }}
    TextArea .text-area--gutter {{ background: {bg}; color: {ln}; }}
    TextArea .text-area--gutter-active {{ background: {bg}; color: {acc}; text-style: bold; }}
    TextArea .text-area--cursor {{ background: {acc}; }}
    TextArea .text-area--cursor-line {{ background: {cl}; }}
    TextArea .text-area--selection {{ background: #1f4a6e; }}

    /* ── Bottom Bar ── */
    #bottom-bar {{ background: {surf}; border-top: solid {brd}; }}
    .kb-key {{ color: {acc}; text-style: bold; }}
    .kb-desc {{ color: {txt_m}; }}
    .bb-item:hover {{ background: {panel}; }}

    #sb-unsaved {{ color: {warn}; }}
    #sb-lang {{ color: {txt_m}; }}
    #sb-cursor {{ color: {txt_m}; }}
    #sb-branch {{ color: {succ}; }}

    /* ── Tab Strip ── */
    TabStrip {{ background: {bg}; }}
    .tab-item {{ color: {txt_m}; background: {bg}; }}
    .tab-item.--tab-active {{ color: {txt}; background: {panel}; text-style: bold; }}
    .tab-item.--tab-unsaved {{ color: {warn}; }}

    /* ── Welcome Panel ── */
    WelcomePanel {{ background: {bg}; }}
    #welcome-header {{ color: {acc}; }}
    #welcome-tagline {{ color: {txt_m}; }}
    #welcome-recent-label {{ color: {txt_m}; }}
    #welcome-recent-list {{ background: {bg}; }}
    #welcome-recent-list > ListItem {{ background: {bg}; color: {txt}; }}
    #welcome-recent-list > ListItem:hover {{ background: {panel}; color: {acc}; }}
    #welcome-hint {{ color: {brd}; }}

    /* ── Toast Notifications ── */
    Toast {{ background: {panel}; border-left: tall {acc}; color: {txt}; }}
    Toast.-information {{ border-left: tall {acc}; }}
    Toast.-warning {{ border-left: tall {warn}; background: {panel}; }}
    Toast.-error {{ border-left: tall {err}; background: {panel}; }}
    Toast .toast--title {{ color: {acc}; text-style: bold; }}
    Toast.-warning .toast--title {{ color: {warn}; }}
    Toast.-error .toast--title {{ color: {err}; }}
    """


def build_modal_css(theme: dict) -> str:
    bg     = theme.get("background",     "#0d1016")
    surf   = theme.get("surface",        "#1a1d23")
    panel  = theme.get("panel",          "#131721")
    brd    = theme.get("border",         "#2e3038")
    brd_f  = theme.get("border_focused", "#5ac1fe")
    txt    = theme.get("text",           "#bfbdb6")
    txt_m  = theme.get("text_muted",     "#686868")
    acc    = theme.get("accent",         "#5ac1fe")
    err    = theme.get("error",          "#ef7177")
    return f"""
    *Screen {{ background: #030508; align: center middle; }}
    .modal-dialog {{
        width: 54; height: auto;
        background: {panel};
        border: tall {acc};
        padding: 0;
    }}
    .modal-titlebar {{
        width: 100%; height: 3;
        background: {bg};
        border-bottom: solid {brd};
        padding: 0 2;
        align: left middle;
    }}
    .modal-title {{ color: {acc}; text-style: bold; width: 1fr; }}
    .modal-hint  {{ width: auto; color: {txt_m}; }}
    .modal-body  {{ width: 100%; color: {txt}; padding: 1 2; }}
    .modal-footer {{
        width: 100%; height: 1;
        text-align: center; color: {txt_m};
        border-top: solid {brd};
    }}
    """
