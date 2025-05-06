import sys
from collections.abc import Callable
from typing import TypeVar
from rich import print as print_func

input_func = input

T = TypeVar("T")


def safe_input(
    text: str, transform: Callable[[str], T], exceptions=(ValueError, IndexError)
) -> T:
    while True:
        try:
            print_func(text, end="")
            output = input_func()
            return transform(output)
        except exceptions:
            pass


def print_selection(choices: list, print_choices=True, exit=True) -> None:
    if len(choices) == 0:
        print_func("[red]No result")
        if exit:
            sys.exit(404)
        return
    if len(choices) == 1:
        print_func(f"-> [blue]{choices[0]}")
        return
    if not print_choices:
        return

    for index, choice in enumerate(choices, start=1):
        line_colors = "yellow" if index % 2 == 0 else "white"
        print_func(
            f"[green][{index:{len(str(len(choices)))}}]",
            f"[{line_colors}]{choice}",
        )


def select_one(choices: list[T], msg="Choose a number", **_) -> T:
    print_selection(choices)
    if len(choices) == 1:
        return choices[0]

    return safe_input(
        f"[white]{msg}[/white]: \033[0;34m", lambda string: choices[int(string) - 1]
    )


def select_range(choices: list[T], msg="Choose a range", print_choices=True) -> list[T]:
    print_selection(choices, print_choices)

    if len(choices) == 1:
        return [choices[0]]

    def transform(string: str) -> list[T]:
        # Return all choices if the user enter '*' symbol
        if string == "*":
            return choices
        # Handle "full" or "X full" format
        if "full" in string.lower():
            parts = string.lower().split()
            if len(parts) == 1:  # just "full"
                return choices
            try:
                index = int(parts[0]) - 1
                if 0 <= index < len(choices):
                    return [choices[index]]
            except (ValueError, IndexError):
                pass
            raise ValueError("Format invalide pour 'full'")
        # Else, detect the string and transform it into a list of choices
        ints_set: set[int] = set()
        for args in string.split(","):
            ints = [int(num) if num.strip() else None for num in args.split("-")]

            if len(ints) == 1 and ints[0] is not None:
                ints_set.add(ints[0])
            elif len(ints) == 2:
                if ints[0] is None:
                    ints[0] = 1
                if ints[1] is None:
                    ints[1] = len(choices)
                ints_set.update(range(ints[0], ints[1] + 1))
            else:
                raise ValueError

        return [choices[i - 1] for i in ints_set]

    return safe_input(
        f"[white]{msg}[/white] [green][1-{len(choices)}][/]: \033[0;34m",
        transform,
    )

import re
from itertools import zip_longest

def remove_some_js_comments(string: str) -> str:
    """Remove multi-line comments and HTML comments from string."""
    # Remove multi-line comments
    string = re.sub(r"/\*[\W\w]*?\*/", "", string)
    # Remove HTML comments
    string = re.sub(r"<!--[\W\w]*?-->", "", string)
    return string

def zip_varlen(*lists):
    """Zip lists of different lengths."""
    return [list(filter(None, item)) for item in zip_longest(*lists)]

def split_and_strip(string: str, seps: tuple[str, ...]) -> list[str]:
    """Split string by multiple separators and strip whitespace."""
    pattern = "|".join(map(re.escape, seps))
    return [item.strip() for item in re.split(pattern, string) if item.strip()]
import re
from collections.abc import Callable
from typing import TypeVar
from rich import print as print_func

input_func = input

T = TypeVar("T")

def safe_input(
    text: str, transform: Callable[[str], T], exceptions=(ValueError, IndexError)
) -> T:
    while True:
        try:
            print_func(text, end="")
            output = input_func()
            return transform(output)
        except exceptions:
            pass

def print_selection(choices: list, print_choices=True, exit=True) -> None:
    if len(choices) == 0:
        print_func("[red]No result")
        if exit:
            sys.exit(404)
        return
    if len(choices) == 1:
        print_func(f"-> [blue]{choices[0]}")
        return
    if not print_choices:
        return

    for index, choice in enumerate(choices, start=1):
        line_colors = "yellow" if index % 2 == 0 else "white"
        print_func(
            f"[green][{index:{len(str(len(choices)))}}]",
            f"[{line_colors}]{choice}",
        )

def select_one(choices: list[T], msg="Choose a number", **_) -> T:
    print_selection(choices)
    if len(choices) == 1:
        return choices[0]

    return safe_input(
        f"[white]{msg}[/white]: \033[0;34m", lambda string: choices[int(string) - 1]
    )

def select_range(choices: list[T], msg="Choose a range", print_choices=True) -> list[T]:
    print_selection(choices, print_choices)

    if len(choices) == 1:
        return [choices[0]]

    def transform(string: str) -> list[T]:
        if string == "*":
            return choices
        ints_set: set[int] = set()
        for args in string.split(","):
            ints = [int(num) if num.strip() else None for num in args.split("-")]

            if len(ints) == 1 and ints[0] is not None:
                ints_set.add(ints[0])
            elif len(ints) == 2:
                if ints[0] is None:
                    ints[0] = 1
                if ints[1] is None:
                    ints[1] = len(choices)
                ints_set.update(range(ints[0], ints[1] + 1))
            else:
                raise ValueError

        return [choices[i - 1] for i in ints_set]

    return safe_input(
        f"[white]{msg}[/white] [green][1-{len(choices)}][/]: \033[0;34m",
        transform,
    )

def remove_some_js_comments(string: str) -> str:
    string = re.sub(r"/\*[\W\w]*?\*/", "", string)
    string = re.sub(r"<!--[\W\w]*?-->", "", string)
    return string

def zip_varlen(*lists):
    return [list(filter(None, item)) for item in zip_longest(*lists)]

def split_and_strip(string: str, seps: tuple[str, ...]) -> list[str]:
    pattern = "|".join(map(re.escape, seps))
    return [item.strip() for item in re.split(pattern, string) if item.strip()]
