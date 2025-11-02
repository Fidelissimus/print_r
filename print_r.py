
# A simple, recursive pretty-printer for Python data structures (dicts, lists, tuples, objects).
# It's inspired by PHP's `print_r` which I used to it, and includes optional ANSI color-coding for better readability
# in the terminal, which is enabled by default. The function also supports a maximum depth
# to prevent excessively large output.

def print_r(obj, indent=0, max_depth=None, current_depth=0, ANSI_colors = True):
    """PHP-like print_r for Python (handles dicts, lists, tuples, and objects), and has ANSI colors for terminal (true by default)"""
    
    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
    }
    
    def colorize(text, color):
        if ANSI_colors:
            return f"{COLORS[color]}{text}{COLORS['reset']}"
        return text
    
    def format_value(v):
        """Format a value with appropriate coloring"""
        if isinstance(v, str):
            return colorize(repr(v), 'green')
        elif isinstance(v, (int, float)):
            return colorize(str(v), 'bright_yellow')
        elif isinstance(v, bool):
            return colorize(str(v), 'bright_cyan')
        elif v is None:
            return colorize('None', 'bright_red')
        else:
            return colorize(str(v), 'white')
    
    # Check max depth
    if max_depth is not None and current_depth > max_depth:
        print(" " * indent + colorize("... (max depth reached)", 'bright_red'))
        return
    
    spacing = " " * indent
    
    if isinstance(obj, dict):
        print(f"{spacing}{colorize('dict', 'bright_blue')}({colorize(str(len(obj)), 'bright_yellow')}) {colorize('{', 'white')}")
        for k, v in obj.items():
            key_str = colorize(repr(k), 'bright_magenta')
            print(f"{spacing}  [{key_str}] => ", end="")
            if isinstance(v, (dict, list, tuple)) or (hasattr(v, '__dict__') and v.__class__.__name__ not in ['str', 'int', 'float', 'bool']):
                print()
                print_r(v, indent + 4, max_depth, current_depth + 1, ANSI_colors = ANSI_colors)
            else:
                print(format_value(v))
        print(f"{spacing}{colorize('}', 'white')}")
    
    elif isinstance(obj, (list, tuple)):
        typename = colorize(type(obj).__name__, 'bright_blue')
        length = colorize(str(len(obj)), 'bright_yellow')
        bracket_open = colorize('[', 'white') if isinstance(obj, list) else colorize('(', 'white')
        bracket_close = colorize(']', 'white') if isinstance(obj, list) else colorize(')', 'white')
        
        print(f"{spacing}{typename}({length}) {bracket_open}")
        for i, v in enumerate(obj):
            index_str = colorize(str(i), 'bright_magenta')
            print(f"{spacing}  [{index_str}] => ", end="")
            if isinstance(v, (dict, list, tuple)) or (hasattr(v, '__dict__') and v.__class__.__name__ not in ['str', 'int', 'float', 'bool']):
                print()
                print_r(v, indent + 4, max_depth, current_depth + 1, ANSI_colors = ANSI_colors)
            else:
                print(format_value(v))
        print(f"{spacing}{bracket_close}")
    
    else:
        # Handle objects with __dict__ attribute
        if hasattr(obj, "__dict__") and obj.__class__.__name__ not in ['str', 'int', 'float', 'bool']:
            class_name = colorize(obj.__class__.__name__, 'bright_cyan')
            print(f"{spacing}{class_name} {colorize('{', 'white')}")
            print_r(vars(obj), indent + 2, max_depth, current_depth + 1 , ANSI_colors = ANSI_colors)
            print(f"{spacing}{colorize('}', 'white')}")
        else:
            # Handle dataclasses, namedtuples, and other objects
            try:
                if hasattr(obj, '_asdict'):  # namedtuple
                    print(f"{spacing}{colorize(type(obj).__name__, 'bright_cyan')} {colorize('{', 'white')}")
                    print_r(obj._asdict(), indent + 2, max_depth, current_depth + 1)
                    print(f"{spacing}{colorize('}', 'white')}")
                elif hasattr(obj, '__dataclass_fields__'):  # dataclass
                    print(f"{spacing}{colorize(type(obj).__name__, 'bright_cyan')} {colorize('{', 'white')}")
                    print_r({field: getattr(obj, field) for field in obj.__dataclass_fields__}, indent + 2, max_depth, current_depth + 1)
                    print(f"{spacing}{colorize('}', 'white')}")
                else:
                    print(f"{spacing}{format_value(obj)}")
            except Exception:
                # Fallback for any object
                print(f"{spacing}{format_value(obj)}")

