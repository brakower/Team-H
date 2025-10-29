"""Example tools for the React Agent."""

from typing import List, Dict, Any
import json


def calculator(operation: str, a: float, b: float) -> float:
    """Perform basic arithmetic operations.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
        
    Returns:
        Result of the operation
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float('inf')
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](a, b)


def string_analyzer(text: str) -> Dict[str, Any]:
    """Analyze a string and return statistics.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary with text statistics
    """
    words = text.split()
    return {
        "length": len(text),
        "word_count": len(words),
        "unique_words": len(set(words)),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0
    }


def list_processor(items: List[str], operation: str) -> Any:
    """Process a list of items.
    
    Args:
        items: List of items to process
        operation: Operation to perform (count, sort, reverse, unique)
        
    Returns:
        Processed result
    """
    operations = {
        "count": lambda x: len(x),
        "sort": lambda x: sorted(x),
        "reverse": lambda x: list(reversed(x)),
        "unique": lambda x: list(set(x))
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](items)


def json_formatter(data: Dict[str, Any], indent: int = 2) -> str:
    """Format a dictionary as JSON.
    
    Args:
        data: Dictionary to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent)
