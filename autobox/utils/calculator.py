import math
from datetime import datetime


def calculate_progress(started_at: datetime, timeout: float, iterations: int) -> float:
    current_time = datetime.now()

    # Calculate the elapsed time in seconds since the job started
    elapsed_time = (current_time - started_at).total_seconds()

    # Cap progress at a maximum determined by the timeout
    if elapsed_time >= timeout:
        return 99  # Return a maximum of 99%, allowing 100 to be set elsewhere

    # Adjust alpha to slow down progress earlier
    alpha = 3  # Lower alpha means the progress will slow down earlier

    # Exponential decay calculation with a capped value of 99%
    progress = (1 - math.exp(-alpha * (elapsed_time / timeout))) * 99

    # Optionally adjust with iterations (add or reduce based on iterations)
    adjusted_progress = min(progress + iterations, 99)  # Ensure it never exceeds 99%

    return round(adjusted_progress)
