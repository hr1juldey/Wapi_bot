"""Pytest configuration and shared fixtures for tests.

Provides common fixtures for database, mocks, and test data.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel



@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async_session_factory = sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_booking_state():
    """Sample booking state for testing."""
    return {
        "name": {"first": "Ravi", "last": "Kumar"},
        "phone": "+919876543210",
        "email": "ravi.kumar@example.com",
        "vehicle": {
            "brand": "Tata",
            "model": "Nexon",
            "number_plate": "MH12AB1234"
        },
        "appointment": {
            "date": "2025-12-25",
            "time": "morning",
            "service_type": "premium wash"
        }
    }


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing."""
    return [
        {"role": "user", "content": "Hi, I need to book a car wash"},
        {"role": "assistant", "content": "I'd be happy to help! May I have your name?"},
        {"role": "user", "content": "My name is Ravi Kumar"},
        {"role": "assistant", "content": "Thank you, Ravi! What's your phone number?"},
    ]


@pytest.fixture
def mock_dspy_response():
    """Mock DSPy module response."""
    class MockDSpyResult:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return MockDSpyResult
