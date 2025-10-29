"""Unit tests for example tools."""

import pytest
from backend.tools import calculator, string_analyzer, list_processor, json_formatter


class TestCalculator:
    """Test cases for calculator tool."""

    def test_add(self):
        """Test addition."""
        result = calculator("add", 5, 3)
        assert result == 8

    def test_subtract(self):
        """Test subtraction."""
        result = calculator("subtract", 10, 4)
        assert result == 6

    def test_multiply(self):
        """Test multiplication."""
        result = calculator("multiply", 6, 7)
        assert result == 42

    def test_divide(self):
        """Test division."""
        result = calculator("divide", 15, 3)
        assert result == 5

    def test_divide_by_zero(self):
        """Test division by zero."""
        result = calculator("divide", 10, 0)
        assert result == float("inf")

    def test_unknown_operation(self):
        """Test unknown operation."""
        with pytest.raises(ValueError, match="Unknown operation"):
            calculator("modulo", 10, 3)


class TestStringAnalyzer:
    """Test cases for string analyzer tool."""

    def test_analyze_simple_text(self):
        """Test analyzing simple text."""
        result = string_analyzer("hello world")

        assert result["length"] == 11
        assert result["word_count"] == 2
        assert result["unique_words"] == 2
        assert result["average_word_length"] == 5.0

    def test_analyze_empty_string(self):
        """Test analyzing empty string."""
        result = string_analyzer("")

        assert result["length"] == 0
        assert result["word_count"] == 0
        assert result["average_word_length"] == 0

    def test_analyze_repeated_words(self):
        """Test analyzing text with repeated words."""
        result = string_analyzer("hello hello world")

        assert result["word_count"] == 3
        assert result["unique_words"] == 2


class TestListProcessor:
    """Test cases for list processor tool."""

    def test_count(self):
        """Test counting items."""
        result = list_processor(["a", "b", "c"], "count")
        assert result == 3

    def test_sort(self):
        """Test sorting items."""
        result = list_processor(["c", "a", "b"], "sort")
        assert result == ["a", "b", "c"]

    def test_reverse(self):
        """Test reversing items."""
        result = list_processor(["a", "b", "c"], "reverse")
        assert result == ["c", "b", "a"]

    def test_unique(self):
        """Test getting unique items."""
        result = list_processor(["a", "b", "a", "c", "b"], "unique")
        assert set(result) == {"a", "b", "c"}

    def test_unknown_operation(self):
        """Test unknown operation."""
        with pytest.raises(ValueError, match="Unknown operation"):
            list_processor(["a", "b"], "filter")


class TestJsonFormatter:
    """Test cases for JSON formatter tool."""

    def test_format_simple_dict(self):
        """Test formatting simple dictionary."""
        data = {"key": "value", "number": 42}
        result = json_formatter(data)

        assert '"key": "value"' in result
        assert '"number": 42' in result

    def test_format_with_custom_indent(self):
        """Test formatting with custom indent."""
        data = {"key": "value"}
        result = json_formatter(data, indent=4)

        # Check that result is valid JSON and properly indented
        assert '"key":' in result
        assert "    " in result  # 4 spaces

    def test_format_nested_dict(self):
        """Test formatting nested dictionary."""
        data = {"outer": {"inner": "value"}}
        result = json_formatter(data)

        assert '"outer"' in result
        assert '"inner"' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
