"""Format and print Python values in a readable, PHP ``print_r``-like style."""

from __future__ import annotations

import dataclasses
import enum
import sys
from collections.abc import Iterable, Mapping, Set
from typing import Literal, TextIO

ColorOption = bool | Literal["auto"]

_INDENT_STEP = 4
_COLORS = {
    "reset": "\033[0m",
    "green": "\033[32m",
    "white": "\033[37m",
    "bright_red": "\033[91m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
}


class _UnreadableAttribute:
    """Represent an attribute whose value could not be read safely."""

    def __init__(self, error: Exception) -> None:
        self.error_name = type(error).__name__


class _Formatter:
    """Build formatted output while tracking active recursive containers."""

    def __init__(
        self,
        *,
        max_depth: int | None,
        ansi_colors: bool,
        redacted_fields: frozenset[str],
    ) -> None:
        self.max_depth = max_depth
        self.ansi_colors = ansi_colors
        self.redacted_fields = redacted_fields
        self._active_object_ids: set[int] = set()

    def format(self, obj: object, *, indent: int, current_depth: int) -> str:
        lines = self._format_lines(obj, indent=indent, depth=current_depth)
        return "\n".join(lines)

    def _format_lines(self, obj: object, *, indent: int, depth: int) -> list[str]:
        if self.max_depth is not None and depth > self.max_depth:
            return [self._spaces(indent) + self._paint("... (max depth reached)", "bright_red")]

        structure = self._structure_for(obj)
        if structure is None:
            return [self._spaces(indent) + self._format_scalar(obj)]

        object_id = id(obj)
        if object_id in self._active_object_ids:
            marker = f"<circular reference: {type(obj).__name__}>"
            return [self._spaces(indent) + self._paint(marker, "bright_red")]

        self._active_object_ids.add(object_id)
        try:
            header, opening, closing, entries = structure
            return self._render_entries(
                header,
                opening,
                closing,
                entries,
                indent=indent,
                depth=depth,
            )
        finally:
            self._active_object_ids.remove(object_id)

    def _structure_for(
        self, obj: object
    ) -> tuple[str, str, str, list[tuple[object, object, bool]]] | None:
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            entries = [
                (field.name, self._read_attribute(obj, field.name), True)
                for field in dataclasses.fields(obj)
            ]
            return type(obj).__name__, "{", "}", entries

        if self._is_namedtuple(obj):
            field_names = type(obj)._fields
            entries = [
                (field_name, self._read_attribute(obj, field_name), True)
                for field_name in field_names
            ]
            return type(obj).__name__, "{", "}", entries

        if isinstance(obj, Mapping):
            entries = [(key, value, False) for key, value in obj.items()]
            return type(obj).__name__, "{", "}", entries

        if isinstance(obj, list):
            entries = [(index, value, True) for index, value in enumerate(obj)]
            return "list", "[", "]", entries

        if isinstance(obj, tuple):
            entries = [(index, value, True) for index, value in enumerate(obj)]
            return "tuple", "(", ")", entries

        if isinstance(obj, (Set, frozenset)) and not isinstance(obj, (str, bytes, bytearray)):
            values = sorted(obj, key=self._safe_repr)
            entries = [(index, value, True) for index, value in enumerate(values)]
            return type(obj).__name__, "{", "}", entries

        attributes = self._object_attributes(obj)
        if attributes:
            entries = [(name, value, True) for name, value in attributes]
            return type(obj).__name__, "{", "}", entries

        return None

    def _render_entries(
        self,
        header: str,
        opening: str,
        closing: str,
        entries: list[tuple[object, object, bool]],
        *,
        indent: int,
        depth: int,
    ) -> list[str]:
        padding = self._spaces(indent)
        type_label = self._paint(header, "bright_blue")
        length = self._paint(str(len(entries)), "bright_yellow")
        lines = [f"{padding}{type_label}({length}) {self._paint(opening, 'white')}"]

        for key, value, plain_key in entries:
            key_text = str(key) if plain_key else self._safe_repr(key)
            key_label = self._paint(key_text, "bright_magenta")
            entry_prefix = f"{padding}  [{key_label}] =>"

            if self._is_redacted(key):
                lines.append(f"{entry_prefix} {self._paint('<redacted>', 'bright_red')}")
            elif self._is_expandable(value):
                lines.append(entry_prefix)
                lines.extend(
                    self._format_lines(
                        value,
                        indent=indent + _INDENT_STEP,
                        depth=depth + 1,
                    )
                )
            else:
                lines.append(f"{entry_prefix} {self._format_scalar(value)}")

        lines.append(padding + self._paint(closing, "white"))
        return lines

    def _is_expandable(self, obj: object) -> bool:
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return True
        if self._is_namedtuple(obj):
            return True
        if isinstance(obj, (Mapping, list, tuple)):
            return True
        if isinstance(obj, (Set, frozenset)) and not isinstance(obj, (str, bytes, bytearray)):
            return True
        return bool(self._object_attributes(obj))

    def _object_attributes(self, obj: object) -> list[tuple[str, object]]:
        if self._is_scalar(obj):
            return []

        try:
            namespace = vars(obj)
        except (TypeError, AttributeError):
            namespace = {}

        if namespace:
            return [(str(name), value) for name, value in namespace.items()]

        attributes: list[tuple[str, object]] = []
        seen_names: set[str] = set()
        for cls in type(obj).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            if isinstance(slots, str):
                slots = (slots,)
            for name in slots:
                if name in {"__dict__", "__weakref__"} or name in seen_names:
                    continue
                seen_names.add(name)
                attributes.append((name, self._read_attribute(obj, name)))
        return attributes

    @staticmethod
    def _read_attribute(obj: object, name: str) -> object:
        try:
            return getattr(obj, name)
        except Exception as error:
            return _UnreadableAttribute(error)

    @staticmethod
    def _is_namedtuple(obj: object) -> bool:
        fields = getattr(type(obj), "_fields", None)
        return (
            isinstance(obj, tuple)
            and isinstance(fields, tuple)
            and all(isinstance(field, str) for field in fields)
        )

    @staticmethod
    def _is_scalar(obj: object) -> bool:
        return obj is None or isinstance(
            obj,
            (str, bytes, bytearray, bool, int, float, complex, enum.Enum),
        )

    def _format_scalar(self, value: object) -> str:
        if isinstance(value, _UnreadableAttribute):
            text = f"<unreadable: {value.error_name}>"
            return self._paint(text, "bright_red")
        if value is None:
            return self._paint("None", "bright_red")
        if isinstance(value, bool):
            return self._paint(str(value), "bright_cyan")
        if isinstance(value, str):
            return self._paint(repr(value), "green")
        if isinstance(value, (int, float, complex)):
            return self._paint(str(value), "bright_yellow")
        return self._paint(self._safe_repr(value), "white")

    def _is_redacted(self, key: object) -> bool:
        return isinstance(key, str) and key.casefold() in self.redacted_fields

    def _paint(self, text: str, color: str) -> str:
        if not self.ansi_colors:
            return text
        return f"{_COLORS[color]}{text}{_COLORS['reset']}"

    @staticmethod
    def _safe_repr(value: object) -> str:
        try:
            return repr(value)
        except Exception as error:
            return f"<unprintable {type(value).__name__}: {type(error).__name__}>"

    @staticmethod
    def _spaces(count: int) -> str:
        return " " * count


def format_r(
    obj: object,
    *,
    indent: int = 0,
    max_depth: int | None = None,
    ansi_colors: bool = False,
    redact: Iterable[str] | str | None = None,
) -> str:
    """Return a PHP ``print_r``-style representation of a Python value.

    Args:
        obj: Value to format.
        indent: Number of leading spaces for the top-level value.
        max_depth: Deepest child depth to expand. ``None`` removes the limit.
        ansi_colors: Whether to include ANSI terminal color sequences.
        redact: Field names or mapping string keys whose values should be hidden.
            Matching is case-insensitive. A single field name may be passed as a
            string.

    Returns:
        The formatted representation without a trailing newline.

    Raises:
        TypeError: If an integer option or redaction field has an invalid type.
        ValueError: If ``indent`` or ``max_depth`` is negative.

    Example:
        >>> print(format_r({"ready": True}))
        dict(1) {
          ['ready'] => True
        }
    """
    _validate_nonnegative_integer("indent", indent)
    if max_depth is not None:
        _validate_nonnegative_integer("max_depth", max_depth)
    if not isinstance(ansi_colors, bool):
        raise TypeError("ansi_colors must be a bool")

    formatter = _Formatter(
        max_depth=max_depth,
        ansi_colors=ansi_colors,
        redacted_fields=_normalize_redacted_fields(redact),
    )
    return formatter.format(obj, indent=indent, current_depth=0)


def print_r(
    obj: object,
    indent: int = 0,
    max_depth: int | None = None,
    current_depth: int = 0,
    ANSI_colors: ColorOption = "auto",  # noqa: N803 - retained for API compatibility
    *,
    file: TextIO | None = None,
    redact: Iterable[str] | str | None = None,
) -> None:
    """Print a PHP ``print_r``-style representation of a Python value.

    The first five parameters preserve the original project's calling
    convention. New code should normally leave ``current_depth`` at zero.

    Args:
        obj: Value to print.
        indent: Number of leading spaces for the top-level value.
        max_depth: Deepest child depth to expand. ``None`` removes the limit.
        current_depth: Initial depth retained for backward compatibility.
        ANSI_colors: ``True`` or ``False`` to force color behavior, or ``"auto"``
            to enable colors only when the output stream is a terminal.
        file: Text stream that receives the output. Defaults to ``sys.stdout``.
        redact: Field names or mapping string keys whose values should be hidden.
            Matching is case-insensitive.

    Returns:
        None.

    Raises:
        TypeError: If an option has an invalid type or ``file`` is not writable.
        ValueError: If a depth or indentation value is negative, or if the color
            option is invalid.
        OSError: If writing to the output stream fails.
    """
    _validate_nonnegative_integer("indent", indent)
    _validate_nonnegative_integer("current_depth", current_depth)
    if max_depth is not None:
        _validate_nonnegative_integer("max_depth", max_depth)

    stream = sys.stdout if file is None else file
    if not hasattr(stream, "write"):
        raise TypeError("file must be a writable text stream")

    formatter = _Formatter(
        max_depth=max_depth,
        ansi_colors=_resolve_color_option(ANSI_colors, stream),
        redacted_fields=_normalize_redacted_fields(redact),
    )
    output = formatter.format(obj, indent=indent, current_depth=current_depth)
    stream.write(output + "\n")


def _resolve_color_option(option: ColorOption, stream: TextIO) -> bool:
    if isinstance(option, bool):
        return option
    if option != "auto":
        raise ValueError('ANSI_colors must be True, False, or "auto"')
    try:
        return bool(stream.isatty())
    except (AttributeError, OSError):
        return False


def _normalize_redacted_fields(
    fields: Iterable[str] | str | None,
) -> frozenset[str]:
    if fields is None:
        return frozenset()
    if isinstance(fields, str):
        fields = (fields,)

    normalized: set[str] = set()
    try:
        for field in fields:
            if not isinstance(field, str):
                raise TypeError("redact entries must be strings")
            normalized.add(field.casefold())
    except TypeError as error:
        if str(error) == "redact entries must be strings":
            raise
        raise TypeError("redact must be a string or an iterable of strings") from error
    return frozenset(normalized)


def _validate_nonnegative_integer(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
