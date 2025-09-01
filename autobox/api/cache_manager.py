"""Cache manager for simulation status with TTL (Time To Live)."""

import time
from typing import Any, Dict, Optional
from datetime import datetime

from autobox.actor.manager import ActorManager
from autobox.logging.logger import LoggerManager
from autobox.schemas.message import (
    CompleteStatusRequest,
    CompleteStatusResponse,
)
from autobox.schemas.actor import ActorName


class CacheManager:
    """Manages cached simulation data with TTL to reduce actor system calls."""
    
    def __init__(self, actor_manager: Optional[ActorManager], ttl_seconds: float = 1.0):
        """Initialize the cache manager.
        
        Args:
            actor_manager: The actor manager instance
            ttl_seconds: Time to live for cached data in seconds
        """
        self.actor_manager = actor_manager
        self.ttl_seconds = ttl_seconds
        self.logger = LoggerManager.get_server_logger()
        
        # Cache storage
        self._cache: Dict[str, Any] = {
            "status": {
                "status": "new",
                "progress": 0,
                "summary": None,
                "last_updated": datetime.now().isoformat(),
                "error": None,
            },
            "metrics": [],
        }
        self._last_fetch_time: float = 0
        self._fetching: bool = False  # Prevent concurrent fetches
        
    async def get_status(self) -> Dict[str, Any]:
        """Get simulation status, using cache if still valid."""
        await self._refresh_if_needed()
        return self._cache["status"]
        
    async def get_metrics(self) -> list:
        """Get metrics data, using cache if still valid."""
        await self._refresh_if_needed()
        return self._cache["metrics"]
        
    async def get_all(self) -> Dict[str, Any]:
        """Get all cached data, refreshing if needed."""
        await self._refresh_if_needed()
        return self._cache
        
    async def _refresh_if_needed(self) -> None:
        """Refresh cache if TTL has expired."""
        current_time = time.time()
        
        # Check if cache is still valid
        if current_time - self._last_fetch_time < self.ttl_seconds:
            return
            
        # Prevent concurrent fetches
        if self._fetching:
            # Wait a bit for the other fetch to complete
            await asyncio.sleep(0.1)
            return
            
        self._fetching = True
        try:
            await self._fetch_and_update()
            self._last_fetch_time = current_time
        finally:
            self._fetching = False
            
    async def _fetch_and_update(self) -> None:
        """Fetch fresh data from orchestrator and update cache."""
        if not self.actor_manager:
            self._cache["status"]["error"] = "Actor system not initialized"
            return
            
        try:
            # Run the blocking actor call in executor
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                self._fetch_complete_status
            )
            
            if response:
                # Update cache with fresh data
                self._cache["status"].update({
                    "status": response.get("status", "new"),
                    "progress": response.get("progress", 0),
                    "summary": response.get("summary"),
                    "last_updated": datetime.now().isoformat(),
                    "error": None,
                })
                
                self._cache["metrics"] = response.get("metrics", [])
                
                self.logger.debug(
                    f"Cache refreshed: {response.get('status')} - {response.get('progress')}%"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to refresh cache: {e}")
            self._cache["status"]["error"] = str(e)
            
    def _fetch_complete_status(self) -> Optional[Dict[str, Any]]:
        """Fetch complete status from orchestrator (blocking call)."""
        try:
            response = self.actor_manager.ask(
                CompleteStatusRequest(
                    from_agent=ActorName.SIMULATOR,
                    to_agent=ActorName.ORCHESTRATOR,
                )
            )
            
            if isinstance(response, CompleteStatusResponse):
                return {
                    "status": str(response.simulation_status) if response.simulation_status else "new",
                    "progress": response.progress,
                    "summary": response.summary,
                    "metrics": [m.model_dump() for m in response.metrics] if response.metrics else []
                }
                
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to fetch complete status: {e}")
            return None
            
    def invalidate(self) -> None:
        """Invalidate the cache, forcing refresh on next access."""
        self._last_fetch_time = 0