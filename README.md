# yamlfmt

A small tool that takes messy YAML config files and re-writes them with
consistent indentation, quoting, and spacing. No third-party dependencies -
just the Python standard library.

## The problem

Config files accumulate inconsistencies over time: three-space indents next
to two-space ones, some strings quoted and others not, trailing whitespace,
tabs someone's editor inserted by accident. None of it is wrong YAML, it's
just inconsistent, and it makes diffs noisy. `yamlfmt` parses the file and
re-emits it in one consistent style.

Given input like:

```yaml
name:    "web"
port: 8080
tags:
    - prod
    - "eu"
retries: yes
```

it produces:

```yaml
name: web
port: 8080
tags:
  - prod
  - eu
retries: true
```

## Usage

Format a file and print the result to stdout:

```sh
python -m yamlfmt config.yaml
```

Rewrite the file in place:

```sh
python -m yamlfmt -i config.yaml
```

Read from stdin (useful in pipelines, or when a file isn't involved at all):

```sh
cat config.yaml | python -m yamlfmt
```

Multiple files at once (each block is preceded by a `# path` marker unless
`-i` is given):

```sh
python -m yamlfmt config/*.yaml
```

If it's installed as a package (`pip install .`), the same commands work
with the `yamlfmt` executable in place of `python -m yamlfmt`.

## What it normalizes

- Indentation to two spaces per level.
- String quoting: quotes are added only where needed to avoid ambiguity
  (a value that would otherwise look like a number, boolean, or null) and
  removed everywhere else.
- Boolean spelling (`yes`/`no`/`True`/`False` -> `true`/`false`).
- Trailing whitespace and inconsistent line endings.

## Current limitations

This is an early version. It handles plain block-style mappings and
sequences, which covers most hand-written config files, but it does not
yet support:

- Flow-style collections (`{a: 1}`, `[1, 2, 3]`)
- Multi-line block scalars (`|` and `>`)
- Anchors and aliases (`&anchor`, `*alias`)
- Multiple documents in one file (`---` separators)
- Comments - they are stripped during formatting, not preserved

Files using those features will either fail to parse (raising
`yamlfmt.YamlFormatError`) or be normalized incorrectly. See the roadmap for
what's planned.

## License

MIT, see LICENSE.
