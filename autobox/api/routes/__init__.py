"""API routes module."""

from autobox.api.routes.health import router as health_router
from autobox.api.routes.simulation import router as simulation_router
from autobox.api.routes.instructions import router as instructions_router

__all__ = ["health_router", "simulation_router", "instructions_router"]