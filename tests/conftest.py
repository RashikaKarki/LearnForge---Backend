"""Shared pytest fixtures for all tests.

FIXTURE PHILOSOPHY:
- Put INFRASTRUCTURE here (mock_db, mock_client, test setup)
- Keep TEST DATA in test files (user_data, mission_data, etc.)

This keeps tests self-documenting and easy to read.
"""

from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Configure anyio to only use asyncio (not trio)
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# Add infrastructure fixtures here (mocks, clients, etc.)
# Do NOT add test data fixtures (keep those in individual test files)
