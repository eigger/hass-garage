"""Use the actual Home Assistant pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Enable custom component loading for every integration test."""
    yield
