from pathlib import Path
from textual.widgets import TextArea


def _read_highlight_query(package_name: str) -> str | None:
    try:
        import importlib
        mod = importlib.import_module(package_name)
        pkg_path = Path(mod.__file__).parent
        query_path = pkg_path / "queries" / "highlights.scm"
        if query_path.exists():
            return query_path.read_text()
    except Exception:
        pass
    return None


EXTRA_LANGUAGES = [
    "typescript",
    "c",
    "cpp",
    "ruby",
    "php",
    "lua",
]


def register_extra_languages(text_area: TextArea) -> None:
    from textual._tree_sitter import get_language, _tree_sitter
    from textual.widgets._text_area import TextAreaLanguage
    from tree_sitter import Language

    if not _tree_sitter:
        return

    def _load_grammar(name: str):
        grammar = get_language(name)
        if grammar is not None:
            return grammar
        fallbacks = {
            "typescript": ("tree_sitter_typescript", "language_typescript"),
            "php":        ("tree_sitter_php",        "language_php"),
        }
        if name in fallbacks:
            try:
                pkg_name, func_name = fallbacks[name]
                import importlib
                mod = importlib.import_module(pkg_name)
                return Language(getattr(mod, func_name)())
            except Exception:
                pass
        return None

    for lang_name in EXTRA_LANGUAGES:
        if lang_name in text_area._languages:
            continue
        grammar = _load_grammar(lang_name)
        if grammar is None:
            continue
        query = _read_highlight_query(f"tree_sitter_{lang_name}")
        if query is None:
            continue
        text_area._languages[lang_name] = TextAreaLanguage(
            lang_name, grammar, query
        )

    # tsx: grammar lives in tree_sitter_typescript package
    if "tsx" not in text_area._languages:
        tsx_query = _read_highlight_query("tree_sitter_typescript")
        if tsx_query is not None:
            try:
                import tree_sitter_typescript
                tsx_grammar = Language(tree_sitter_typescript.language_tsx())
                text_area._languages["tsx"] = TextAreaLanguage(
                    "tsx", tsx_grammar, tsx_query
                )
            except Exception:
                pass
