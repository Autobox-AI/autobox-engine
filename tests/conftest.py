"""Global test configuration and fixtures."""

import os

os.environ["POLL_INTERVAL_SECONDS"] = "0.01"
os.environ["MAX_CONSECUTIVE_ERRORS"] = "1"


import asyncio
from unittest.mock import Mock, patch

import pytest
from thespian.actors import ActorAddress

from autobox.schemas.config import AgentConfig, Config, SimulationConfig, WorkerConfig


@pytest.fixture
def mock_actor_address():
    """Create a mock actor address."""
    return Mock(spec=ActorAddress)


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return SimulationConfig(
        id="test-sim",
        name="Test Simulation",
        description="Test simulation for unit tests",
        timeout_seconds=10,
        max_steps=5,
        orchestrator=AgentConfig(
            name="orchestrator",
            model="gpt-4",
            temperature=0.5,
        ),
        planner=AgentConfig(
            name="planner",
            model="gpt-4",
            temperature=0.5,
        ),
        evaluator=AgentConfig(
            name="evaluator",
            model="gpt-4",
            temperature=0.5,
        ),
        reporter=AgentConfig(
            name="reporter",
            model="gpt-4",
            temperature=0.5,
        ),
        workers=[
            WorkerConfig(
                name="worker1",
                role="Test Worker 1",
                backstory="A test worker",
                model="gpt-4",
                temperature=0.5,
            ),
            WorkerConfig(
                name="worker2",
                role="Test Worker 2",
                backstory="Another test worker",
                model="gpt-4",
                temperature=0.5,
            ),
        ],
    )


@pytest.fixture
def mock_config(test_config):
    """Create a mock configuration."""
    return Config(simulation=test_config, metrics=None)


@pytest.fixture
def fast_async_sleep():
    """Mock asyncio.sleep to speed up tests."""

    async def fast_sleep(seconds):
        # Sleep for 1/100th of the requested time
        await asyncio.sleep(seconds / 100)

    with patch("asyncio.sleep", side_effect=fast_sleep):
        yield


@pytest.fixture
def instant_async_sleep():
    """Mock asyncio.sleep to be instant."""

    async def instant_sleep(seconds):
        # Don't sleep at all
        return

    with patch("asyncio.sleep", side_effect=instant_sleep):
        yield
