# Python print_r Utility

A debugging utility function for Python that provides a structured, PHP-like `print_r` output for complex data types like **dictionaries**, **lists**, **tuples**, and **objects**.

## Key Features

* **Recursive Display:** Handles nested data structures.
* **ANSI Colors:** Uses terminal colors (on by default) for enhanced readability.
* **Max Depth:** Prevents infinite recursion or overly long output with the `max_depth` parameter.
* **Object Handling:** Supports standard objects, named tuples, and dataclasses.

## Usage

Simply import the `print_r` function and pass your variable to it.

```python
from print_r import print_r

# A custom class to demonstrate object handling,.. should be printed by print_r but not pprint (the built-in one, 'from pprint import pprint')
class UserConfig:
    def __init__(self, username, is_admin):
        self.username = username
        self.is_admin = is_admin
        self._private = "secret_key"

nested_data = [
    {
        'id': 1001,
        'status': True,
        'payload': {
            'data_points': [1.23, 55.4, 0.999],
            'settings': ('fast', 'large', 10),
            'log_msg': "Initial connection successful."
        },
        'error': None
    },
    (
        'transaction_hash',
        b'\xde\xad\xbe\xef', # Bytes data
        UserConfig('alpha_user', False), # Custom object
        {
            'timestamp': 69696969240240,
            'rate_limit': 15
        }
    ),
    [
        'A',
        100,
        False,
    ]
]

print_r(data)
