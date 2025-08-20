#!/usr/bin/env python3
"""Test script to verify the configuration loader works correctly."""

import pytest

from autobox.config.loader import load_simulation_config


def test_loader():
    """Test the configuration loader with the test fixture file."""
    config = load_simulation_config("tests/fixtures/simulations/test_simulation.json")

    print(config)

    # Assert configuration loaded correctly
    assert config.name == "Test Simulation"
    assert config.max_steps == 150
    assert config.timeout_seconds == 300
    assert config.task == "Test task for simulation"

    # Check workers
    assert len(config.workers) == 2
    worker_names = [worker.name for worker in config.workers]
    assert "WORKER_1" in worker_names
    assert "WORKER_2" in worker_names

    # Check other components
    assert config.orchestrator.name == "ORCHESTRATOR"
    assert config.evaluator.name == "EVALUATOR"
    assert config.reporter.name == "REPORTER"
    assert config.planner.name == "PLANNER"

    # Check logging config
    assert not config.logging.verbose
    assert config.logging.log_path is None


def test_loader_with_invalid_path():
    """Test that the loader raises an error for invalid file paths."""
    with pytest.raises(FileNotFoundError):
        load_simulation_config("nonexistent/file.json")
