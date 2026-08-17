# Python print_r

`python-print-r` is a zero-runtime-dependency formatter for developers who want
PHP-style `print_r` output while debugging Python values. It safely expands nested
containers and objects, detects circular references, and can color terminal output.

## Features

- Formats mappings, lists, tuples, sets, namedtuples, dataclasses, and custom objects.
- Detects circular references without confusing repeated non-recursive values.
- Limits recursive expansion with `max_depth`.
- Automatically enables ANSI colors for terminals and disables them for redirected output.
- Redacts selected mapping keys and object fields using case-insensitive matching.
- Produces reusable strings with `format_r` or writes to a chosen stream with `print_r`.
- Includes type information and has no runtime dependencies outside the Python standard library.

## Installation

Python 3.10 or newer is required.

Install the project directly from GitHub:

```bash
python -m pip install "git+https://github.com/Fidelissimus/print_r.git"
```

For local development, clone the repository and install it in editable mode:

```bash
git clone https://github.com/Fidelissimus/print_r.git
cd print_r
python -m pip install --editable .
```

## Usage

### Print a nested value

```python
from print_r import print_r

payload = {
    "id": 1001,
    "active": True,
    "tags": ["python", "debugging"],
}

print_r(payload)
```

When output is redirected, the result contains no terminal escape sequences:

```text
dict(3) {
  ['id'] => 1001
  ['active'] => True
  ['tags'] =>
    list(2) [
      [0] => 'python'
      [1] => 'debugging'
    ]
}
```

### Format, limit depth, and redact fields

```python
from dataclasses import dataclass

from print_r import format_r


@dataclass(slots=True)
class Account:
    username: str
    password: str


account = Account(username="alice", password="correct-horse-battery-staple")
result = format_r(
    {"account": account, "metadata": {"source": "demo"}},
    max_depth=2,
    redact={"password"},
)
print(result)
```

### Control the output stream and colors

```python
import sys

from print_r import print_r

print_r({"status": "ok"}, ANSI_colors=False, file=sys.stderr)
```

`ANSI_colors` accepts `True`, `False`, or `"auto"`. The default, `"auto"`, enables
color only when the selected stream reports that it is a terminal. The original
positional parameters remain supported for compatibility.

## Project Structure

- `print_r/core.py` contains formatting and stream-output behavior.
- `print_r/__init__.py` exposes the public API and package version.
- `tests/` contains the standard-library `unittest` suite.
- `.github/workflows/ci.yml` verifies supported Python versions.

## Testing

Run the complete test suite without installing third-party test dependencies:

```bash
python -m unittest discover -s tests -v
```

Build distribution artifacts with the standard Python packaging frontend:

```bash
python -m pip install build
python -m build
```

The package itself has no runtime dependencies. `build` and Ruff are development tools used
for producing distribution archives and automated style checks.

## Versioning

This project follows [Semantic Versioning](https://semver.org/). Release history is recorded
in [CHANGELOG.md](CHANGELOG.md).

## License

No license has been selected. Copyright remains with the repository owner until a license is
added explicitly.
