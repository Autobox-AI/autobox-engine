import argparse
import json

from autobox.schemas.config import Config, MetricConfig, SimulationConfig


def load_config(args: argparse.Namespace) -> Config:
    return Config(
        simulation=_load_simulation_config(args.config),
        metrics=_load_metrics_config(args.metrics),
    )


def _load_simulation_config(file_path: str) -> SimulationConfig:
    return SimulationConfig(**_load_file(file_path))


def _load_metrics_config(file_path: str) -> list[MetricConfig]:
    return _load_file(file_path)


def _load_file(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
