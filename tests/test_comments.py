import unittest

from yamlfmt import format_text
from yamlfmt.parser import load_with_comments


class CommentPreservationTests(unittest.TestCase):
    def test_leading_and_trailing_comments_on_top_level_keys(self):
        text = "# top\nname: web  # the name\nport: 8080\n"
        self.assertEqual(format_text(text), text)

    def test_trailing_comment_spacing_is_normalized(self):
        self.assertEqual(format_text("a: 1     # one\n"), "a: 1  # one\n")

    def test_comment_follows_its_key_when_reindented(self):
        text = "server:\n    # listen port\n    port: 80\n"
        self.assertEqual(format_text(text), "server:\n  # listen port\n  port: 80\n")

    def test_comment_on_a_key_with_nested_value(self):
        text = "server:  # main\n  port: 80\n"
        self.assertEqual(format_text(text), text)

    def test_sequence_item_comments(self):
        text = "tags:\n- a # first\n# before b\n- b\n"
        expected = "tags:\n  - a  # first\n  # before b\n  - b\n"
        self.assertEqual(format_text(text), expected)

    def test_comments_on_sequence_of_mappings(self):
        text = "# first\n- name: a # n\n  v: 1\n# second\n- name: b\n  v: 2\n"
        expected = (
            "# first\n- name: a  # n\n  v: 1\n# second\n- name: b\n  v: 2\n"
        )
        self.assertEqual(format_text(text), expected)

    def test_comments_after_the_last_node_are_kept(self):
        text = "a: 1\n# end of file\n"
        self.assertEqual(format_text(text), text)

    def test_comment_only_file_is_returned_as_is(self):
        text = "# just a note\n"
        self.assertEqual(format_text(text), text)

    def test_hash_inside_quotes_is_not_treated_as_a_comment(self):
        text = 'k: "a # b"\n'
        self.assertEqual(format_text(text), text)

    def test_output_is_stable_when_formatted_twice(self):
        text = "# c1\na:\n    - x # cx\n    # c2\n    - y\nb: 2 # cb\n# tail\n"
        once = format_text(text)
        self.assertEqual(format_text(once), once)


class CommentCollectionTests(unittest.TestCase):
    def test_comments_are_keyed_by_path(self):
        text = "# about a\na:\n  b: 1  # about b\n"
        _, comments = load_with_comments(text)
        self.assertEqual(comments.leading[("a",)], ["# about a"])
        self.assertEqual(comments.trailing[("a", "b")], "# about b")

    def test_sequence_item_owns_the_line_with_its_first_key(self):
        _, comments = load_with_comments("- k: v  # note\n")
        self.assertEqual(comments.trailing[(0,)], "# note")
        self.assertNotIn((0, "k"), comments.trailing)


if __name__ == "__main__":
    unittest.main()
