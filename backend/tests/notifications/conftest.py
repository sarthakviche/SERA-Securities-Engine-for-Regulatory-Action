"""
Local conftest for notifications tests.

This directory has its own conftest so that pytest does not try to load
the root conftest (which depends on anthropic, langgraph, etc.).
All notification tests are self-contained with in-memory fakes.
"""

import pytest


# Ensure pytest-asyncio works in auto mode for all tests in this directory
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async",
    )
