import logging
import sys
from typing import Optional

from autobox.utils.normalizer import value_to_id


class Logger:
    _instance: Optional["Logger"] = None
    simulation_id: str = None

    def __init__(
        self,
        name: str = "autobox",
        verbose: bool = False,
        log_path: Optional[str] = None,
        log_file: Optional[str] = None,
    ):
        self.name = name
        self.verbose = verbose
        self.log_path = log_path
        self.log_file = log_file

        # Get the logger and prevent propagation to avoid duplicate logs
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False  # This prevents duplicate logging

        # Clear any existing handlers
        self._logger.handlers.clear()

        # Create and configure stdout handler
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)

        # Create custom formatter
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stdout_handler.setFormatter(fmt)
        self._logger.addHandler(stdout_handler)

        # Add file handler if log_path is specified
        if self.log_path:
            if self.log_file is None:
                self.log_file = f"{value_to_id(self.name)}.log"

            file_handler = logging.FileHandler(f"{self.log_path}/{self.log_file}")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(fmt)
            self._logger.addHandler(file_handler)

        Logger._instance = self

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str, exception: Exception = None):
        self._logger.error(message, exc_info=exception)

    def print_banner(self):
        self._logger.info(
            """\n
    █████╗ ██╗   ██╗████████╗ ██████╗ ██████╗  ██████╗ ██╗  ██╗
    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██╔═══██╗╚██╗██╔╝
    ███████║██║   ██║   ██║   ██║   ██║██████╔╝██║   ██║ ╚███╔╝
    ██╔══██║██║   ██║   ██║   ██║   ██║██╔══██╗██║   ██║ ██╔██╗
    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██████╔╝╚██████╔╝██╔╝ ██╗
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝
    """
        )

    @classmethod
    def get_instance(cls, **kwargs) -> "Logger":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def log(cls, message: str):
        logger = cls.get_instance()
        logger.info(message)
