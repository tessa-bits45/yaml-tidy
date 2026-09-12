"""A parser for a practical subset of block-style YAML.

Supports nested mappings and sequences, plain/quoted scalars, and
comments. Does not support flow collections ({}/[]), anchors/aliases,
multi-line block scalars (| and >), or multi-document streams.
"""

import re

class YamlFormatError(Exception):
    """Raised when the input can't be parsed as the supported subset."""


_BOOL_TRUE = {"true", "yes"}
_BOOL_FALSE = {"false", "no"}
_NULL_WORDS = {"null", "~", ""}
_INT_RE = re.compile(r"[+-]?\d+")
_FLOAT_RE = re.compile(r"[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?|[+-]?\d+[eE][+-]?\d+")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "0": "\0"}


def load(text):
    """Parse YAML text into plain dict/list/scalar values."""
    lines = _preprocess(text)
    if not lines:
        return None
    value, idx = _parse_node(lines, 0, lines[0][0])
    if idx != len(lines):
        _, _, lineno = lines[idx]
        raise YamlFormatError(f"line {lineno}: unexpected indentation or content")
    return value


def _preprocess(text):
    lines = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        content = _strip_comment(raw.rstrip())
        stripped = content.strip()
        if stripped == "" or stripped in ("---", "..."):
            continue
        indent = len(content) - len(content.lstrip(" "))
        lines.append((indent, stripped, lineno))
    return lines


def _strip_comment(line):
    in_single = False
    in_double = False
    out = []
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or line[i - 1] in " \t":
                break
        out.append(ch)
    return "".join(out).rstrip()


def _find_key_separator(content):
    in_single = False
    in_double = False
    for i, ch in enumerate(content):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            if i + 1 == len(content) or content[i + 1] == " ":
                return i
    return -1


def _parse_node(lines, idx, indent):
    _, content, _ = lines[idx]
    if content == "-" or content.startswith("- "):
        return _parse_sequence(lines, idx, indent)
    return _parse_mapping(lines, idx, indent)


def _parse_sequence(lines, idx, indent):
    items = []
    while idx < len(lines):
        line_indent, content, lineno = lines[idx]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise YamlFormatError(f"line {lineno}: unexpected indentation")
        if not (content == "-" or content.startswith("- ")):
            break
        rest = "" if content == "-" else content[2:].strip()
        idx += 1
        if rest == "":
            if idx < len(lines) and lines[idx][0] > indent:
                value, idx = _parse_node(lines, idx, lines[idx][0])
            else:
                value = None
        elif _find_key_separator(rest) != -1:
            value, idx = _parse_inline_mapping(lines, idx, indent, rest, lineno)
        else:
            value = _parse_scalar(rest)
        items.append(value)
    return items, idx


def _parse_inline_mapping(lines, idx, seq_indent, first_line, lineno):
    # "- key: value" puts the first mapping key on the dash's own line, so
    # its virtual indent is two past the dash rather than the next line's.
    virtual_indent = seq_indent + 2
    sub_lines = [(virtual_indent, first_line, lineno)]
    while idx < len(lines) and lines[idx][0] >= virtual_indent:
        sub_lines.append(lines[idx])
        idx += 1
    value, _ = _parse_mapping(sub_lines, 0, virtual_indent)
    return value, idx


def _parse_mapping(lines, idx, indent):
    mapping = {}
    while idx < len(lines):
        line_indent, content, lineno = lines[idx]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise YamlFormatError(f"line {lineno}: unexpected indentation")
        sep = _find_key_separator(content)
        if sep == -1:
            break
        key = _parse_scalar(content[:sep].strip())
        value_raw = content[sep + 1:].strip()
        idx += 1
        if value_raw != "":
            value = _parse_scalar(value_raw)
        elif idx < len(lines) and lines[idx][0] > indent:
            value, idx = _parse_node(lines, idx, lines[idx][0])
        elif idx < len(lines) and lines[idx][0] == indent and (
            lines[idx][1] == "-" or lines[idx][1].startswith("- ")
        ):
            # A sequence value may sit at the same indent as its key.
            value, idx = _parse_sequence(lines, idx, indent)
        else:
            value = None
        mapping[key] = value
    return mapping, idx


def _parse_scalar(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return _parse_quoted(text)
    lowered = text.lower()
    if lowered in _NULL_WORDS:
        return None
    if lowered in _BOOL_TRUE:
        return True
    if lowered in _BOOL_FALSE:
        return False
    if _INT_RE.fullmatch(text):
        return int(text)
    if _FLOAT_RE.fullmatch(text):
        return float(text)
    return text


def _parse_quoted(text):
    quote = text[0]
    inner = text[1:-1]
    if quote == '"':
        return _unescape_double(inner)
    return inner.replace("''", "'")


def _unescape_double(s):
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] in _ESCAPES:
            out.append(_ESCAPES[s[i + 1]])
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)
