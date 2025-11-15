import pytest
import student_submission


@pytest.fixture
def data():
    return [10, 5, 8, 12, 3, 7]


@pytest.fixture
def empty():
    return []


# calculate_average
def test_calculate_average_normal(data):
    assert student_submission.calculate_average(data) == pytest.approx(7.5)


def test_calculate_average_empty(empty):
    with pytest.raises(ValueError):
        student_submission.calculate_average(empty)


# find_max
def test_find_max_normal(data):
    assert student_submission.find_max(data) == 12


def test_find_max_empty(empty):
    with pytest.raises(ValueError):
        student_submission.find_max(empty)


# find_min
def test_find_min_normal(data):
    assert student_submission.find_min(data) == 3


def test_find_min_empty(empty):
    with pytest.raises(ValueError):
        student_submission.find_min(empty)


# calculate_median
def test_calculate_median_even(data):
    assert student_submission.calculate_median(data) == 7.5


def test_calculate_median_odd():
    assert student_submission.calculate_median([5, 1, 9]) == 5


def test_calculate_median_empty(empty):
    with pytest.raises(ValueError):
        student_submission.calculate_median(empty)


# calculate_range
def test_calculate_range_normal(data):
    assert student_submission.calculate_range(data) == 9


def test_calculate_range_empty(empty):
    with pytest.raises(ValueError):
        student_submission.calculate_range(empty)

# count_occurrences

def test_count_occurrences_normal():
    assert student_submission.count_occurrences([1, 2, 2, 3, 2], 2) == 3

def test_count_occurrences_zero():
    assert student_submission.count_occurrences([1, 3, 4], 2) == 0

def test_count_occurrences_empty():
    with pytest.raises(ValueError):
        student_submission.count_occurrences([], 1)
