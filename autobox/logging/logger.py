import logging
import sys
from typing import Optional

from autobox.logging import banner
from autobox.utils.normalizer import value_to_id


class Logger:
    """A single logger instance with configurable output modes."""

    def __init__(
        self,
        name: str = "autobox",
        verbose: bool = False,
        log_path: Optional[str] = None,
        log_file: Optional[str] = None,
        console: bool = True,
        file: bool = False,
    ):
        """
        Initialize a logger with flexible output configuration.

        Args:
            name: Logger name (used for identification and default file naming)
            verbose: Enable verbose logging
            log_path: Directory path for log files (required if file=True)
            log_file: Specific log file name (auto-generated if not provided)
            console: Enable console output
            file: Enable file output
        """
        self.name = name
        self.verbose = verbose
        self.log_path = log_path
        self.log_file = log_file
        self.console = console
        self.file = file

        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        self._logger.propagate = False  # Prevents duplicate logging
        self._logger.handlers.clear()

        fmt = logging.Formatter(
            f"%(asctime)s | {name} | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if console:
            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
            stdout_handler.setFormatter(fmt)
            self._logger.addHandler(stdout_handler)

        if file:
            if not log_path:
                raise ValueError(
                    f"log_path is required when file output is enabled for logger '{name}'"
                )

            if self.log_file is None:
                self.log_file = f"{value_to_id(self.name)}.log"

            file_handler = logging.FileHandler(f"{self.log_path}/{self.log_file}")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(fmt)
            self._logger.addHandler(file_handler)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str, exception: Exception = None):
        self._logger.error(message, exc_info=exception)

    def debug(self, message: str):
        self._logger.debug(message)

    def print_banner(self):
        """Print the AUTOBOX banner."""
        banner_text = banner.get()
        if self.console:
            print(banner_text)
        if self.file and self._logger.handlers:
            for handler in self._logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.stream.write(banner_text + "\n")
                    handler.stream.flush()


class LoggerManager:
    """Manages multiple named logger instances."""

    _loggers: dict[str, Logger] = {}

    @classmethod
    def get_logger(
        cls,
        name: str,
        verbose: bool = False,
        log_path: Optional[str] = None,
        log_file: Optional[str] = None,
        console: bool = True,
        file: bool = False,
        force_new: bool = False,
    ) -> Logger:
        """
        Get or create a named logger instance.

        Args:
            name: Logger name (e.g., 'app', 'server', 'runner')
            verbose: Enable verbose logging
            log_path: Directory path for log files
            log_file: Specific log file name
            console: Enable console output
            file: Enable file output
            force_new: Force creation of a new logger even if one exists

        Returns:
            Logger instance
        """
        if force_new or name not in cls._loggers:
            cls._loggers[name] = Logger(
                name=name,
                verbose=verbose,
                log_path=log_path,
                log_file=log_file,
                console=console,
                file=file,
            )
        return cls._loggers[name]

    @classmethod
    def get_app_logger(cls, **kwargs) -> Logger:
        """Get the application logger (for banner, startup messages)."""
        return cls.get_logger("app", **kwargs)

    @classmethod
    def get_server_logger(cls, **kwargs) -> Logger:
        """Get the HTTP server logger."""
        return cls.get_logger("server", **kwargs)

    @classmethod
    def get_runner_logger(cls, **kwargs) -> Logger:
        """Get the simulation runner logger."""
        return cls.get_logger("runner", **kwargs)

    @classmethod
    def clear_all(cls):
        """Clear all logger instances."""
        cls._loggers.clear()


# Backward compatibility - keep singleton pattern for legacy code
class SingletonLogger(Logger):
    """Legacy singleton logger for backward compatibility."""

    _instance: Optional["SingletonLogger"] = None
    simulation_id: str = None

    @classmethod
    def get_instance(cls, **kwargs) -> "SingletonLogger":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def log(cls, message: str):
        logger = cls.get_instance()
        logger.info(message)
