"""Instructions endpoint for sending commands to agents."""

from fastapi import APIRouter, Request, Response, status

from autobox.logging.logger import LoggerManager
from autobox.schemas.instruction import InstructionRequest
from autobox.utils.name_sanitizer import sanitize_agent_name

router = APIRouter(prefix="/instructions", tags=["instructions"])
logger = LoggerManager.get_server_logger()


@router.post("/agents/{agent_name}", status_code=status.HTTP_202_ACCEPTED)
async def send_instruction(
    agent_name: str, instruction_request: InstructionRequest, request: Request
) -> Response:
    """Send instructions to a specific agent.

    Args:
        agent_name: Name of the agent to send instructions to
        instruction_request: The instruction payload
        request: The FastAPI request object

    Returns:
        Response: 202 Accepted status
    """
    sanitized_name = sanitize_agent_name(agent_name.lower())

    logger.info(
        f"Sending instructions to agent {agent_name} (sanitized: {sanitized_name})."
    )

    cache_manager = request.app.state.cache_manager
    if cache_manager and cache_manager.actor_manager:
        cache_manager.actor_manager.instruct(
            sanitized_name, instruction_request.instruction
        )
    else:
        logger.warning("Actor manager not initialized, instruction not sent.")

    return Response(status_code=status.HTTP_202_ACCEPTED)
