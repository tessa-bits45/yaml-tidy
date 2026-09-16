import unittest

from yamlfmt.parser import YamlFormatError, load


class EmptyInputTests(unittest.TestCase):
    def test_empty_string(self):
        self.assertIsNone(load(""))

    def test_only_comments_and_blank_lines(self):
        text = "# nothing here\n\n   \n# still nothing\n"
        self.assertIsNone(load(text))

    def test_bare_scalar_is_not_a_valid_document(self):
        # A document has to be a mapping or a sequence at the top level.
        with self.assertRaises(YamlFormatError):
            load("just a string\n")


class MappingTests(unittest.TestCase):
    def test_flat_mapping(self):
        text = "name: web\nport: 8080\n"
        self.assertEqual(load(text), {"name": "web", "port": 8080})

    def test_nested_mapping(self):
        text = "outer:\n  inner: 1\n  other: two\n"
        self.assertEqual(load(text), {"outer": {"inner": 1, "other": "two"}})

    def test_empty_value_is_null(self):
        text = "key:\n"
        self.assertEqual(load(text), {"key": None})

    def test_quoted_key_containing_colon(self):
        text = '"key with: colon": value\n'
        self.assertEqual(load(text), {"key with: colon": "value"})

    def test_sequence_value_at_same_indent_as_key(self):
        text = "items:\n- a\n- b\n"
        self.assertEqual(load(text), {"items": ["a", "b"]})

    def test_rejects_indentation_deeper_than_the_current_key(self):
        text = "a: 1\n  b: 2\n"
        with self.assertRaises(YamlFormatError) as ctx:
            load(text)
        self.assertIn("line 2", str(ctx.exception))

    def test_rejects_content_with_no_key_separator(self):
        text = "a: 1\nnot a mapping line\n"
        with self.assertRaises(YamlFormatError) as ctx:
            load(text)
        self.assertIn("line 2", str(ctx.exception))


class SequenceTests(unittest.TestCase):
    def test_flat_sequence(self):
        text = "- a\n- b\n- c\n"
        self.assertEqual(load(text), ["a", "b", "c"])

    def test_sequence_of_mappings(self):
        text = "- name: a\n  value: 1\n- name: b\n  value: 2\n"
        self.assertEqual(
            load(text),
            [{"name": "a", "value": 1}, {"name": "b", "value": 2}],
        )

    def test_dash_with_no_value_is_null(self):
        text = "- a\n-\n- c\n"
        self.assertEqual(load(text), ["a", None, "c"])

    def test_rejects_sequence_item_indented_less_than_the_others(self):
        text = "- a\n - b\n"
        with self.assertRaises(YamlFormatError):
            load(text)


class ScalarTests(unittest.TestCase):
    def test_double_quoted_string_with_escapes(self):
        text = 'esc: "line1\\nline2\\ttabbed"\n'
        self.assertEqual(load(text), {"esc": "line1\nline2\ttabbed"})

    def test_single_quoted_string_with_escaped_quote(self):
        text = "note: 'it''s fine'\n"
        self.assertEqual(load(text), {"note": "it's fine"})

    def test_quoting_preserves_string_that_looks_like_a_number(self):
        text = 'value: "42"\n'
        self.assertEqual(load(text), {"value": "42"})

    def test_booleans_and_nulls_are_case_insensitive(self):
        text = "a: yes\nb: No\nc: true\nd: FALSE\ne: null\nf: ~\n"
        self.assertEqual(
            load(text),
            {"a": True, "b": False, "c": True, "d": False, "e": None, "f": None},
        )

    def test_numbers(self):
        text = "a: 42\nb: -7\nc: 3.14\nd: .5\ne: 1e10\nf: -2.5e-3\n"
        result = load(text)
        self.assertEqual(result["a"], 42)
        self.assertEqual(result["b"], -7)
        self.assertEqual(result["c"], 3.14)
        self.assertEqual(result["d"], 0.5)
        self.assertEqual(result["e"], 1e10)
        self.assertEqual(result["f"], -2.5e-3)

    def test_lone_dash_as_a_value_is_a_string(self):
        # A "-" only starts a sequence item at the front of a line; as a
        # mapping value it's just a one-character string.
        text = "key: -\n"
        self.assertEqual(load(text), {"key": "-"})


class CommentTests(unittest.TestCase):
    def test_trailing_comment_is_stripped(self):
        text = "key: value  # trailing comment\n"
        self.assertEqual(load(text), {"key": "value"})

    def test_full_line_comment_is_ignored(self):
        text = "# full line comment\nother: 1\n"
        self.assertEqual(load(text), {"other": 1})

    def test_hash_without_leading_space_is_not_a_comment(self):
        text = "key: value#not-a-comment\n"
        self.assertEqual(load(text), {"key": "value#not-a-comment"})

    def test_hash_inside_quotes_is_not_a_comment(self):
        text = 'key: "value # still a value"\n'
        self.assertEqual(load(text), {"key": "value # still a value"})


if __name__ == "__main__":
    unittest.main()
