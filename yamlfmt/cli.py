"""Command-line entry point: format files given as arguments, or stdin."""

import argparse
import sys

from . import YamlFormatError, format_text


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="yamlfmt",
        description="Normalize the formatting of a YAML config file.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="YAML files to format. Omit to read from stdin.",
    )
    parser.add_argument(
        "-i", "--in-place",
        action="store_true",
        help="rewrite each file in place instead of printing to stdout",
    )
    args = parser.parse_args(argv)

    if not args.files:
        if args.in_place:
            parser.error("--in-place needs at least one file; stdin has nowhere to write back to")
        try:
            formatted = format_text(sys.stdin.read())
        except YamlFormatError as exc:
            print(f"yamlfmt: <stdin>: {exc}", file=sys.stderr)
            return 1
        sys.stdout.write(formatted)
        return 0

    exit_code = 0
    announce = len(args.files) > 1 and not args.in_place
    for path in args.files:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            print(f"yamlfmt: {path}: {exc.strerror}", file=sys.stderr)
            exit_code = 1
            continue
        try:
            formatted = format_text(text)
        except YamlFormatError as exc:
            print(f"yamlfmt: {path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        if args.in_place:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(formatted)
        else:
            if announce:
                print(f"# {path}")
            sys.stdout.write(formatted)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
