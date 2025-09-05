"""Simulation status and control endpoints."""

from fastapi import APIRouter, Request, Response, status

from autobox.logging.logger import LoggerManager
from autobox.schemas.cache import StatusCache
from autobox.schemas.simulation import SimulationResponse

router = APIRouter(tags=["simulation"])
logger = LoggerManager.get_server_logger()


@router.get("/status", response_model=SimulationResponse)
async def get_status(request: Request) -> SimulationResponse:
    """Get simulation status from cache (non-blocking).

    Args:
        request: The FastAPI request object

    Returns:
        SimulationResponse: Current simulation status from cache
    """
    cache_manager = request.app.state.cache_manager
    cache: StatusCache = (
        cache_manager.get_status()
        if cache_manager
        else request.app.state.simulation_cache
    )

    return SimulationResponse(
        status=cache.status,
        progress=cache.progress,
        summary=cache.summary,
        last_updated=cache.last_updated.isoformat(),
        error=cache.error,
    )


@router.post("/abort", status_code=status.HTTP_202_ACCEPTED)
async def abort_simulation(request: Request) -> Response:
    """Abort the currently running simulation.

    Sends an ABORT signal to the orchestrator which will trigger
    a graceful shutdown of all agents. Returns immediately with 202 Accepted.

    Args:
        request: The FastAPI request object

    Returns:
        Response: 202 Accepted status
    """
    cache_manager = request.app.state.cache_manager
    if not cache_manager or not cache_manager.actor_manager:
        logger.warning("Status manager not initialized, cannot abort.")
        return Response(status_code=status.HTTP_202_ACCEPTED)

    try:
        cache_manager.actor_manager.abort_simulation()

        cache = request.app.state.simulation_cache
        cache["status"] = "aborting"
        cache["message"] = "Abort requested - shutting down agents"

        logger.info("Abort signal sent to orchestrator (non-blocking)")

    except Exception as e:
        logger.error(f"Failed to send abort signal: {e}")

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get("/metrics")
async def get_metrics(request: Request):
    """Get metrics from cache - returns raw metrics data."""
    cache_manager = request.app.state.cache_manager
    cache = (
        cache_manager.get_status()
        if cache_manager
        else request.app.state.simulation_cache
    )
    metric_messages = cache.metrics if hasattr(cache, "metrics") else []
    # TODO: define proper response schema and transformation, we return the raw data for now
    return {"metrics": metric_messages}
