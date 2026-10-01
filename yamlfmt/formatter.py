"""Serializes parsed data back into normalized YAML."""

import re

from .parser import Comments

_SPECIAL_LEADING = set("!&*?|>%@`\"'#,[]{}")
_RESERVED_WORDS = {"true", "false", "yes", "no", "null", "~"}
_NUMERIC_LOOKALIKE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


def dump(data, comments=None):
    """Render parsed data as normalized YAML text, 2-space indented.

    comments is an optional parser.Comments; its comments are re-attached
    to the nodes they were found on.
    """
    notes = comments if comments is not None else Comments()
    lines = _dump_node(data, 0, (), notes)
    lines.extend(notes.footer)
    return "\n".join(lines) + "\n"


def _annotate(entry, pad, path, notes):
    """Put the comments for path above and after the first line of entry."""
    out = [pad + comment for comment in notes.leading.get(path, ())]
    first = entry[0]
    trailing = notes.trailing.get(path)
    if trailing:
        first = f"{first}  {trailing}"
    out.append(first)
    out.extend(entry[1:])
    return out


def _dump_node(data, level, path, notes):
    pad = "  " * level
    if isinstance(data, dict):
        return _dump_mapping(data, level, pad, path, notes)
    if isinstance(data, list):
        return _dump_sequence(data, level, pad, path, notes)
    return [pad + format_scalar(data)]


def _dump_mapping(data, level, pad, path, notes):
    if not data:
        return [pad + "{}"]
    lines = []
    for key, value in data.items():
        key_str = format_scalar(key)
        key_path = path + (key,)
        if isinstance(value, (dict, list)) and value:
            entry = [f"{pad}{key_str}:"]
            entry.extend(_dump_node(value, level + 1, key_path, notes))
        elif isinstance(value, dict):
            entry = [f"{pad}{key_str}: {{}}"]
        elif isinstance(value, list):
            entry = [f"{pad}{key_str}: []"]
        else:
            entry = [f"{pad}{key_str}: {format_scalar(value)}"]
        lines.extend(_annotate(entry, pad, key_path, notes))
    return lines


def _dump_sequence(data, level, pad, path, notes):
    if not data:
        return [pad + "[]"]
    lines = []
    for index, item in enumerate(data):
        item_path = path + (index,)
        if isinstance(item, dict) and item:
            sub_lines = _dump_node(item, level + 1, item_path, notes)
            entry = [f"{pad}- {sub_lines[0].lstrip()}"]
            entry.extend(sub_lines[1:])
        elif isinstance(item, list) and item:
            entry = [f"{pad}-"]
            entry.extend(_dump_node(item, level + 1, item_path, notes))
        elif isinstance(item, dict):
            entry = [f"{pad}- {{}}"]
        elif isinstance(item, list):
            entry = [f"{pad}- []"]
        else:
            entry = [f"{pad}- {format_scalar(item)}"]
        lines.extend(_annotate(entry, pad, item_path, notes))
    return lines


def format_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    return _format_string(value)


def _format_string(text):
    if _needs_quoting(text):
        return '"' + _escape_double(text) + '"'
    return text


def _needs_quoting(text):
    if text == "":
        return True
    if text != text.strip():
        return True
    if text[0] in _SPECIAL_LEADING:
        return True
    if text[0] == "-" and (len(text) == 1 or text[1] == " "):
        return True
    if ": " in text or text.endswith(":"):
        return True
    if " #" in text:
        return True
    if text.lower() in _RESERVED_WORDS:
        return True
    if _NUMERIC_LOOKALIKE.fullmatch(text):
        return True
    return False


def _escape_double(text):
    out = text.replace("\\", "\\\\").replace('"', '\\"')
    return out.replace("\n", "\\n").replace("\t", "\\t")
