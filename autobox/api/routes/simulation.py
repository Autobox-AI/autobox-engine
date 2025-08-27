"""Simulation status and control endpoints."""

from fastapi import APIRouter, Request, Response, status

from autobox.logging.logger import LoggerManager
from autobox.schemas.message import Signal, SignalMessage
from autobox.schemas.simulation import SimulationResponse

router = APIRouter(prefix="/status", tags=["simulation"])
logger = LoggerManager.get_server_logger()


@router.get("", response_model=SimulationResponse)
async def get_status(request: Request) -> SimulationResponse:
    """Get simulation status from cache (non-blocking).

    Args:
        request: The FastAPI request object

    Returns:
        SimulationResponse: Current simulation status from cache
    """
    logger.info("Simulation status requested.")
    cache = request.app.state.simulation_cache

    return SimulationResponse(
        status=cache.get("status", "unknown"),
        progress=cache.get("progress", 0),
        summary=cache.get("summary"),
        last_updated=cache.get("last_updated"),
        error=cache.get("error"),
    )


@router.post("/abort", status_code=status.HTTP_202_ACCEPTED)
async def abort_simulation(request: Request) -> dict:
    """Abort the currently running simulation.

    Sends an ABORT signal to the orchestrator which will trigger
    a graceful shutdown of all agents.

    Args:
        request: The FastAPI request object

    Returns:
        dict: Confirmation message
    """
    logger.info("Abort simulation requested.")

    actor_manager = request.app.state.actor_manager
    if not actor_manager:
        logger.warning("Actor manager not initialized, cannot abort.")
        return {"status": "error", "message": "No active simulation to abort"}

    try:
        abort_signal = SignalMessage(
            from_agent="api", to_agent="orchestrator", type=Signal.ABORT
        )

        response = actor_manager.abort_simulation()

        cache = request.app.state.simulation_cache
        cache["status"] = "aborted"
        cache["error"] = "Simulation aborted by user"

        logger.info("Abort signal sent to orchestrator")

        return Response(status_code=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"Failed to abort simulation: {e}")
        return {"status": "error", "message": f"Failed to abort simulation: {str(e)}"}
