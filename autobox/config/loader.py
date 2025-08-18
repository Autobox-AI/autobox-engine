import json

from autobox.schemas.config import MetricConfig, SimulationConfig


def load_simulation_config(file_path: str) -> SimulationConfig:
    return SimulationConfig(**load_config(file_path))


def load_metrics_config(file_path: str) -> list[MetricConfig]:
    return load_config(file_path)


def load_config(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
