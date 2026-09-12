"""yamlfmt: normalize the formatting of YAML config files."""

from .parser import load, YamlFormatError
from .formatter import dump

__version__ = "0.1.0"

__all__ = ["load", "dump", "format_text", "YamlFormatError", "__version__"]


def format_text(text):
    """Parse and re-render YAML text. Returns "" for blank input."""
    if text.strip() == "":
        return ""
    return dump(load(text))
