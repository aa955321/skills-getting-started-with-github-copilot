import pytest
import copy
from src.app import app, activities

# Store the original activities data
original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    yield
    # Clean up after test
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
