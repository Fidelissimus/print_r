"""Behavioral tests for the public :mod:`print_r` API."""

from __future__ import annotations

import io
import unittest
from collections import namedtuple
from dataclasses import dataclass

from print_r import __version__, format_r, print_r


class _TerminalBuffer(io.StringIO):
    """String buffer with a configurable terminal capability."""

    def __init__(self, *, is_terminal: bool) -> None:
        super().__init__()
        self.is_terminal = is_terminal

    def isatty(self) -> bool:
        """Return whether the buffer should behave like a terminal."""
        return self.is_terminal


class _BrokenRepresentation:
    """Object used to verify safe representation fallbacks."""

    __slots__ = ()

    def __repr__(self) -> str:
        """Raise an error to simulate an unsafe custom representation."""
        raise RuntimeError("cannot render")


class FormatRTests(unittest.TestCase):
    """Verify deterministic, safe formatting behavior."""

    def test_formats_nested_mappings_and_sequences(self) -> None:
        output = format_r({"values": [1, True, None]})

        self.assertIn("dict(1) {", output)
        self.assertIn("['values'] =>", output)
        self.assertIn("list(3) [", output)
        self.assertIn("[1] => True", output)
        self.assertIn("[2] => None", output)

    def test_detects_circular_references(self) -> None:
        value: list[object] = []
        value.append(value)

        output = format_r(value)

        self.assertIn("<circular reference: list>", output)

    def test_repeated_non_recursive_values_are_not_cycles(self) -> None:
        child = [1]

        output = format_r([child, child])

        self.assertNotIn("circular reference", output)
        self.assertEqual(output.count("list(1) ["), 2)

    def test_expands_namedtuple_fields(self) -> None:
        point_type = namedtuple("Point", "x y")

        output = format_r(point_type(3, 4))

        self.assertIn("Point(2) {", output)
        self.assertIn("[x] => 3", output)
        self.assertIn("[y] => 4", output)

    def test_expands_nested_slotted_dataclass(self) -> None:
        @dataclass(slots=True)
        class Configuration:
            enabled: bool

        output = format_r([Configuration(enabled=True)])

        self.assertIn("Configuration(1) {", output)
        self.assertIn("[enabled] => True", output)

    def test_redacts_matching_mapping_keys_and_fields(self) -> None:
        @dataclass
        class Credentials:
            username: str
            password: str

        output = format_r(
            {"Token": "abc", "user": Credentials("alice", "secret")},
            redact={"token", "password"},
        )

        self.assertNotIn("abc", output)
        self.assertNotIn("secret", output)
        self.assertEqual(output.count("<redacted>"), 2)

    def test_limits_expansion_depth(self) -> None:
        output = format_r({"child": {"value": 1}}, max_depth=0)

        self.assertIn("... (max depth reached)", output)
        self.assertNotIn("['value']", output)

    def test_sorts_sets_by_safe_representation(self) -> None:
        output = format_r({3, 1, 2})

        self.assertLess(output.index("=> 1"), output.index("=> 2"))
        self.assertLess(output.index("=> 2"), output.index("=> 3"))

    def test_handles_broken_representations(self) -> None:
        output = format_r(_BrokenRepresentation())

        self.assertEqual(output, "<unprintable _BrokenRepresentation: RuntimeError>")

    def test_rejects_invalid_options(self) -> None:
        with self.assertRaises(TypeError):
            format_r({}, indent=True)
        with self.assertRaises(ValueError):
            format_r({}, max_depth=-1)
        with self.assertRaises(TypeError):
            format_r({}, redact=["token", 1])  # type: ignore[list-item]


class PrintRTests(unittest.TestCase):
    """Verify stream output and compatibility behavior."""

    def test_bool_uses_boolean_color(self) -> None:
        stream = io.StringIO()

        print_r(True, ANSI_colors=True, file=stream)

        self.assertEqual(stream.getvalue(), "\033[96mTrue\033[0m\n")

    def test_auto_color_follows_stream_terminal_state(self) -> None:
        terminal = _TerminalBuffer(is_terminal=True)
        redirected = _TerminalBuffer(is_terminal=False)

        print_r("value", file=terminal)
        print_r("value", file=redirected)

        self.assertIn("\033[", terminal.getvalue())
        self.assertNotIn("\033[", redirected.getvalue())

    def test_color_setting_propagates_to_nested_values(self) -> None:
        @dataclass(slots=True)
        class Value:
            count: int

        stream = io.StringIO()

        print_r(Value(2), ANSI_colors=False, file=stream)

        self.assertNotIn("\033[", stream.getvalue())

    def test_supports_original_positional_arguments(self) -> None:
        stream = io.StringIO()

        print_r({"value": 1}, 2, 3, 0, False, file=stream)

        self.assertTrue(stream.getvalue().startswith("  dict(1)"))

    def test_version_uses_semantic_versioning(self) -> None:
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
