"""Simulation status and control endpoints."""

from fastapi import APIRouter, Request, Response, status

from autobox.logging.logger import LoggerManager
from autobox.schemas.simulation import (
    MetricResponse,
    MetricsResponse,
    SimulationResponse,
)

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
async def abort_simulation(request: Request) -> Response:
    """Abort the currently running simulation.

    Sends an ABORT signal to the orchestrator which will trigger
    a graceful shutdown of all agents. Returns immediately with 202 Accepted.

    Args:
        request: The FastAPI request object

    Returns:
        Response: 202 Accepted status
    """
    logger.info("Abort simulation requested.")

    status_manager = request.app.state.status_manager
    if not status_manager or not status_manager.actor_manager:
        logger.warning("Status manager not initialized, cannot abort.")
        return Response(status_code=status.HTTP_202_ACCEPTED)

    try:
        status_manager.actor_manager.abort_simulation()

        cache = request.app.state.simulation_cache
        cache["status"] = "aborting"
        cache["message"] = "Abort requested - shutting down agents"

        logger.info("Abort signal sent to orchestrator (non-blocking)")

    except Exception as e:
        logger.error(f"Failed to send abort signal: {e}")

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(request: Request) -> MetricsResponse:
    """Get metrics from cache."""
    cache = request.app.state.simulation_cache

    metric_messages = cache.get("metrics", [])
    metric_responses = []

    for msg in metric_messages:
        metric_responses.append(
            MetricResponse(
                name=msg.name,
                description=msg.description,
                type=msg.type,
                unit=msg.unit,
                tags=msg.tags,
                values=msg.values,
            )
        )

    return MetricsResponse(metrics=metric_responses)
