"""Instructions endpoint for sending commands to agents."""

from fastapi import APIRouter, Request, Response, status

from autobox.logging.logger import LoggerManager
from autobox.schemas.instruction import InstructionRequest

router = APIRouter(prefix="/instructions", tags=["instructions"])
logger = LoggerManager.get_server_logger()


@router.post("/agents/{agent_name}", status_code=status.HTTP_202_ACCEPTED)
async def send_instruction(
    agent_name: str,
    instruction_request: InstructionRequest,
    request: Request
) -> Response:
    """Send instructions to a specific agent.
    
    Args:
        agent_name: Name of the agent to send instructions to
        instruction_request: The instruction payload
        request: The FastAPI request object
        
    Returns:
        Response: 202 Accepted status
    """
    logger.info(f"Sending instructions to agent {agent_name}.")
    
    status_manager = request.app.state.status_manager
    if status_manager and status_manager.actor_manager:
        status_manager.actor_manager.instruct(agent_name, instruction_request.instruction)
    else:
        logger.warning("Actor manager not initialized, instruction not sent.")
        
    return Response(status_code=status.HTTP_202_ACCEPTED)