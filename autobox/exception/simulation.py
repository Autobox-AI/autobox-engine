class StopSimulationException(Exception):
    """Exception raised when a simulation should be stopped due to critical errors."""

    def __init__(
        self,
        message: str = "Simulation stopped due to critical errors",
        consecutive_errors: int = None,
        elapsed_time: float = None,
    ):
        self.message = message
        self.consecutive_errors = consecutive_errors
        self.elapsed_time = elapsed_time
        super().__init__(self.message)

    def __str__(self):
        base_msg = f"StopSimulationException: {self.message}"
        if self.consecutive_errors is not None:
            base_msg += f" (consecutive errors: {self.consecutive_errors})"
        if self.elapsed_time is not None:
            base_msg += f" (elapsed time: {self.elapsed_time:.1f}s)"
        return base_msg
