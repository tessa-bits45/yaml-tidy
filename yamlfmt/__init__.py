"""yamlfmt: normalize the formatting of YAML config files."""

from .parser import load, load_with_comments, YamlFormatError
from .formatter import dump

__version__ = "0.1.0"

__all__ = ["load", "dump", "format_text", "YamlFormatError", "__version__"]


def format_text(text):
    """Parse and re-render YAML text, keeping comments.

    Returns "" for blank input. A file with only comments comes back as
    just those comments.
    """
    if text.strip() == "":
        return ""
    value, comments = load_with_comments(text)
    if value is None:
        return "".join(line + "\n" for line in comments.footer)
    return dump(value, comments)
