from typing import Callable, TypeVar, List, Any
from rich import get_console
import sys

T = TypeVar("T")

def safe_input(
    text: str, transform: Callable[[str], T], exceptions=(ValueError, IndexError)
) -> T:
    """
    Safely prompts for input until it can be transformed without raising exceptions.
    
    Args:
        text (str): The prompt text to display
        transform (callable): A function to transform the input
        exceptions (tuple): Exception types to catch and retry
        
    Returns:
        The transformed input value
    """
    while True:
        try:
            return transform(input(text))
        except exceptions as e:
            print(f"Invalid input: {e}", file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...", file=sys.stderr)
            sys.exit(1)


def print_selection(choices: list, print_choices=True, exit=True) -> None:
    """
    Print available choices with indices for selection.
    
    Args:
        choices (list): List of items to display
        print_choices (bool): Whether to print the choices
        exit (bool): Whether to print exit option
    """
    console = get_console()
    
    if not print_choices:
        return
    
    for i, choice in enumerate(choices):
        console.print(f"{i+1}: {choice}")
    
    if exit:
        console.print(f"0: Exit")


def select_one(choices: list[T], msg="Choose a number", **kwargs) -> T:
    """
    Prompt the user to select one item from a list.
    
    Args:
        choices (list): List of items to choose from
        msg (str): Message to display for the selection
        **kwargs: Additional arguments for print_selection
        
    Returns:
        The selected item
    """
    def get_choice() -> T:
        print_selection(choices, **kwargs)
        choice = int(input(f"{msg} (1-{len(choices)}, 0 to exit): "))
        if choice == 0:
            console = get_console()
            console.print("[red]Exiting...")
            sys.exit(0)
        if not 1 <= choice <= len(choices):
            raise ValueError(f"Choice must be between 1 and {len(choices)}")
        return choices[choice - 1]

    return safe_input("", get_choice)


def select_range(choices: list[T], msg="Choose a range", print_choices=True) -> list[T]:
    """
    Prompt the user to select a range of items (e.g., "1-5,7,9").
    
    Args:
        choices (list): List of items to choose from
        msg (str): Message to display for the selection
        print_choices (bool): Whether to print the available choices
        
    Returns:
        List of selected items
    """
    def transform(string: str) -> list[T]:
        if string == "all":
            return choices
        
        result = []
        chunks = [chunk.strip() for chunk in string.split(",")]
        
        for chunk in chunks:
            if "-" in chunk:
                start, end = chunk.split("-")
                start, end = int(start), int(end)
                if not 1 <= start <= len(choices) or not 1 <= end <= len(choices):
                    raise ValueError(f"Indices must be between 1 and {len(choices)}")
                for i in range(start - 1, end):
                    result.append(choices[i])
            else:
                index = int(chunk)
                if not 1 <= index <= len(choices):
                    raise ValueError(f"Index must be between 1 and {len(choices)}")
                result.append(choices[index - 1])
        
        return result

    if print_choices:
        print_selection(choices, exit=False)
    
    return safe_input(
        f"{msg} (e.g., 1-5,7,9 or 'all', 0 to exit): ",
        lambda s: s if s == "0" else transform(s),
    )