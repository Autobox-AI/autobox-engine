"""Health check endpoints."""

from fastapi import APIRouter, Request

from autobox.logging.logger import LoggerManager

router = APIRouter(tags=["health"])
logger = LoggerManager.get_server_logger()


@router.get("/ping")
async def ping() -> str:
    """Simple ping endpoint for connectivity check.
    
    Returns:
        str: "pong" response
    """
    logger.info("Ping received.")
    return "pong"


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Health check endpoint with detailed status information.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Health status information including server status,
              actor connection, and cache status
    """
    cache = request.app.state.simulation_cache
    actor_manager = request.app.state.actor_manager
    
    return {
        "server": "healthy",
        "actor_connected": actor_manager is not None,
        "cache_status": "active" if cache.get("last_updated") else "waiting",
        "last_cache_update": cache.get("last_updated"),
    }