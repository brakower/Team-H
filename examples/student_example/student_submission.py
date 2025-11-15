"""
Student Submission: Data Analysis Functions
Author: Jane Doe
Date: November 13, 2025

This module contains functions for basic data analysis operations.
"""

def calculate_average(numbers):
    """Calculate the average of a list of numbers.
    
    Args:
        numbers: A list of numeric values
        
    Returns:
        float: The arithmetic mean of the input numbers
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    return sum(numbers) / len(numbers)


def find_max(numbers):
    """Find the maximum value in a list.
    
    Args:
        numbers: A list of comparable values
        
    Returns:
        The maximum value from the list
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot find max of empty list")
    
    return max(numbers)


def find_min(numbers):
    """Find the minimum value in a list.
    
    Args:
        numbers: A list of comparable values
        
    Returns:
        The minimum value from the list
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot find min of empty list")
    
    return min(numbers)


def calculate_median(numbers):
    """Calculate the median of a list of numbers.
    
    Args:
        numbers: A list of numeric values
        
    Returns:
        float: The median value
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate median of empty list")
    
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    
    # If odd length, return middle element
    if n % 2 == 1:
        return sorted_nums[n // 2]
    
    # If even length, return average of two middle elements
    mid1 = sorted_nums[n // 2 - 1]
    mid2 = sorted_nums[n // 2]
    return (mid1 + mid2) / 2.0


def calculate_range(numbers):
    """Calculate the range (max - min) of a list of numbers.
    
    Args:
        numbers: A list of numeric values
        
    Returns:
        float: The difference between max and min values
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate range of empty list")
    
    return max(numbers) - min(numbers)


# Helper function for testing
if __name__ == "__main__":
    # Sample test data
    test_data = [10, 5, 8, 12, 3, 7]
    
    print("Test Data:", test_data)
    print(f"Average: {calculate_average(test_data)}")
    print(f"Max: {find_max(test_data)}")
    print(f"Min: {find_min(test_data)}")
    print(f"Median: {calculate_median(test_data)}")
    print(f"Range: {calculate_range(test_data)}")


def count_occurrences(lst, value):
    # BUGGY VERSION for testing autograder
    # Returns the length of the list instead of counting occurrences 🤦
    if not lst:
        return 0   # Also wrong: should raise ValueError
    return len(lst)
