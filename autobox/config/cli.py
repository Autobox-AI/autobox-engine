import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Autobox Engine")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        default="simulation.json",
        help="Path to the simulation configuration file",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        required=False,
        default="metrics.json",
        help="Path to the metrics file (optional)",
    )
    return parser.parse_args()
