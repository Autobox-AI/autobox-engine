#!/usr/bin/env python3
"""Test script to verify the configuration loader works correctly."""

import pytest

from autobox.config.loader import _load_simulation_config as load_simulation_config


def test_loader():
    """Test the configuration loader with the test fixture file."""
    config = load_simulation_config("tests/fixtures/simulations/test_simulation.json")

    assert config.name == "Test Simulation"
    assert config.max_steps == 150
    assert config.timeout_seconds == 300
    assert config.task == "Test task for simulation"

    assert len(config.workers) == 2
    worker_names = [worker.name for worker in config.workers]
    assert "worker_1" in worker_names
    assert "worker_2" in worker_names

    assert config.orchestrator.name == "orchestrator"
    assert config.evaluator.name == "evaluator"
    assert config.reporter.name == "reporter"
    assert config.planner.name == "planner"

    assert not config.logging.verbose
    assert config.logging.log_path is None


def test_loader_with_invalid_path():
    """Test that the loader raises an error for invalid file paths."""
    with pytest.raises(FileNotFoundError):
        load_simulation_config("nonexistent/file.json")
