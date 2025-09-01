"""Background process for updating simulation status cache."""

import asyncio
import multiprocessing
import pickle
import time
from datetime import datetime
from multiprocessing import Process, Queue
from typing import Any, Dict, Optional

from autobox.actor.manager import ActorManager
from autobox.logging.logger import LoggerManager
from autobox.schemas.message import (
    CompleteStatusRequest,
    CompleteStatusResponse,
    MetricsSignal,
    SimulationSignal,
)
from autobox.schemas.actor import ActorName


class StatusUpdaterProcess:
    """Separate process for updating status to avoid blocking the API server."""
    
    UPDATE_INTERVAL_SECONDS = 1.0
    
    def __init__(self, orchestrator_address, agent_ids_by_name: dict, status_queue: Queue, command_queue: Queue):
        """Initialize the status updater process.
        
        Args:
            orchestrator_address: The orchestrator actor address
            agent_ids_by_name: Mapping of agent names to IDs
            status_queue: Queue for sending status updates to main process
            command_queue: Queue for receiving commands from main process
        """
        self.orchestrator_address = orchestrator_address
        self.agent_ids_by_name = agent_ids_by_name
        self.status_queue = status_queue
        self.command_queue = command_queue
        self.logger = LoggerManager.get_server_logger()
        self.should_stop = False
        
    def run(self):
        """Main loop for the background process."""
        # Create actor manager in this process
        self.actor_manager = ActorManager(
            agent_ids_by_name=self.agent_ids_by_name,
            orchestrator_address=self.orchestrator_address
        )
        
        while not self.should_stop:
            # Check for stop command
            try:
                command = self.command_queue.get_nowait()
                if command == "STOP":
                    self.should_stop = True
                    break
            except:
                pass  # No command available
                
            # Fetch status from orchestrator
            try:
                status_data = self._fetch_complete_status()
                if status_data:
                    # Send update to main process via queue
                    self.status_queue.put(status_data)
                    
                    # Check if simulation is in terminal state
                    if self._is_terminal_state(status_data.get("status", {})):
                        self.logger.info(f"Simulation in terminal state. Stopping updater.")
                        break
                        
            except Exception as e:
                self.logger.error(f"Error fetching status: {e}")
                
            time.sleep(self.UPDATE_INTERVAL_SECONDS)
            
    def _fetch_complete_status(self) -> Optional[Dict[str, Any]]:
        """Fetch complete status from orchestrator."""
        try:
            response = self.actor_manager.ask(
                CompleteStatusRequest(
                    from_agent=ActorName.SIMULATOR,
                    to_agent=ActorName.ORCHESTRATOR,
                )
            )
            
            if isinstance(response, CompleteStatusResponse):
                return {
                    "status": {
                        "status": str(response.simulation_status) if response.simulation_status else "new",
                        "progress": response.progress,
                        "summary": response.summary,
                        "last_updated": datetime.now().isoformat(),
                        "error": None,
                    },
                    "metrics": [m.model_dump() for m in response.metrics] if response.metrics else []
                }
        except Exception as e:
            self.logger.error(f"Failed to fetch complete status: {e}")
            return None
            
    def _is_terminal_state(self, status: str) -> bool:
        """Check if the simulation is in a terminal state."""
        terminal_states = ["completed", "failed", "aborted", "stopped", "timeout"]
        return status in terminal_states


class BackgroundStatusUpdater:
    """Manager for the background status updater process."""
    
    def __init__(self, actor_manager: Optional[ActorManager], cache: Dict[str, Any]):
        """Initialize the background updater manager.
        
        Args:
            actor_manager: The actor manager instance
            cache: The shared cache dictionary
        """
        self.actor_manager = actor_manager
        self.cache = cache
        self.logger = LoggerManager.get_server_logger()
        self.process: Optional[Process] = None
        self.status_queue: Optional[Queue] = None
        self.command_queue: Optional[Queue] = None
        self._update_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the background updater process."""
        if not self.actor_manager:
            self.logger.warning("No actor manager provided, skipping background updater")
            return
            
        self.logger.info("Starting background status updater process...")
        
        # Create queues for inter-process communication
        self.status_queue = multiprocessing.Queue()
        self.command_queue = multiprocessing.Queue()
        
        # Get orchestrator address and agent IDs from actor manager
        orchestrator_address = self.actor_manager.orchestrator_actor.address
        agent_ids_by_name = self.actor_manager.agent_ids_by_name
        
        # Create and start the background process
        updater = StatusUpdaterProcess(
            orchestrator_address=orchestrator_address,
            agent_ids_by_name=agent_ids_by_name,
            status_queue=self.status_queue,
            command_queue=self.command_queue
        )
        
        self.process = Process(target=updater.run)
        self.process.start()
        
        # Start async task to read from queue and update cache
        self._update_task = asyncio.create_task(self._read_updates())
        
        self.logger.info("Background status updater process started")
        
    async def _read_updates(self) -> None:
        """Read updates from the queue and update the cache."""
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Check for updates from background process (non-blocking)
                status_data = await loop.run_in_executor(
                    None, 
                    self._get_from_queue_with_timeout
                )
                
                if status_data:
                    # Update the cache with new data
                    self.cache["status"].update(status_data["status"])
                    self.cache["metrics"].clear()
                    self.cache["metrics"].extend(status_data["metrics"])
                    
                    self.logger.debug(
                        f"Cache updated: {status_data['status']['status']} - "
                        f"{status_data['status']['progress']}%"
                    )
                    
                await asyncio.sleep(0.1)  # Small delay to avoid busy waiting
                
            except Exception as e:
                if "stopped" in str(e).lower():
                    break
                self.logger.error(f"Error reading updates: {e}")
                
    def _get_from_queue_with_timeout(self) -> Optional[Dict[str, Any]]:
        """Get item from queue with timeout."""
        try:
            return self.status_queue.get(timeout=0.1)
        except:
            return None
            
    async def stop(self) -> None:
        """Stop the background updater process."""
        self.logger.info("Stopping background status updater process...")
        
        if self.command_queue:
            self.command_queue.put("STOP")
            
        if self.process:
            self.process.join(timeout=2.0)
            if self.process.is_alive():
                self.process.terminate()
                
        if self._update_task:
            self._update_task.cancel()
            
        self.logger.info("Background status updater process stopped")