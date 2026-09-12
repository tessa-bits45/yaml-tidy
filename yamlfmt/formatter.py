"""Serializes parsed data back into normalized YAML."""

import re

_SPECIAL_LEADING = set("!&*?|>%@`\"'#,[]{}")
_RESERVED_WORDS = {"true", "false", "yes", "no", "null", "~"}
_NUMERIC_LOOKALIKE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


def dump(data):
    """Render parsed data as normalized YAML text, 2-space indented."""
    return "\n".join(_dump_node(data, 0)) + "\n"


def _dump_node(data, level):
    pad = "  " * level
    if isinstance(data, dict):
        return _dump_mapping(data, level, pad)
    if isinstance(data, list):
        return _dump_sequence(data, level, pad)
    return [pad + format_scalar(data)]


def _dump_mapping(data, level, pad):
    if not data:
        return [pad + "{}"]
    lines = []
    for key, value in data.items():
        key_str = format_scalar(key)
        if isinstance(value, dict) and value:
            lines.append(f"{pad}{key_str}:")
            lines.extend(_dump_node(value, level + 1))
        elif isinstance(value, list) and value:
            lines.append(f"{pad}{key_str}:")
            lines.extend(_dump_node(value, level + 1))
        elif isinstance(value, dict):
            lines.append(f"{pad}{key_str}: {{}}")
        elif isinstance(value, list):
            lines.append(f"{pad}{key_str}: []")
        else:
            lines.append(f"{pad}{key_str}: {format_scalar(value)}")
    return lines


def _dump_sequence(data, level, pad):
    if not data:
        return [pad + "[]"]
    lines = []
    for item in data:
        if isinstance(item, dict) and item:
            sub_lines = _dump_node(item, level + 1)
            lines.append(f"{pad}- {sub_lines[0].lstrip()}")
            lines.extend(sub_lines[1:])
        elif isinstance(item, list) and item:
            lines.append(f"{pad}-")
            lines.extend(_dump_node(item, level + 1))
        elif isinstance(item, dict):
            lines.append(f"{pad}- {{}}")
        elif isinstance(item, list):
            lines.append(f"{pad}- []")
        else:
            lines.append(f"{pad}- {format_scalar(item)}")
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
