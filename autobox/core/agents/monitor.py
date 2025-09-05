"""Monitor actor for tracking simulation status without blocking the orchestrator."""

from datetime import datetime

from thespian.actors import Actor, ActorAddress

from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import ActorName
from autobox.schemas.message import (
    InitMonitor,
    Signal,
    SignalMessage,
    StatusRequestSignal,
    StatusSnapshotMessage,
    StatusUpdateMessage,
)
from autobox.schemas.simulation import SimulationStatus
from autobox.schemas.status import StatusSnapshot
from autobox.transformation.status import status_uptate_to_snapshot

logger = LoggerManager.get_runner_logger()


class Monitor(Actor):
    """
    Lightweight actor that maintains simulation status separately from the orchestrator.
    Receives push updates from orchestrator and serves queries from CacheManager.
    """

    def __init__(self):
        super().__init__()
        self.status_snapshot = StatusSnapshot(
            status=SimulationStatus.NEW,
            progress=0,
            summary=None,
            metrics=[],
            last_updated=datetime.now().isoformat(),
        )

    def receiveMessage(self, message, sender):
        """Handle messages based on type."""
        try:
            if isinstance(message, InitMonitor):
                self._ack(sender)
            elif isinstance(message, StatusRequestSignal):
                self._handle_status_request(message, sender)
            elif isinstance(message, SignalMessage):
                self._handle_signal(message, sender)
            elif isinstance(message, StatusUpdateMessage):
                self._handle_status_update(message)
            else:
                logger.warning(
                    f"Monitor received unknown message type: {type(message)}"
                )

        except Exception as e:
            logger.error(f"Monitor error handling message: {e}")
            if isinstance(message, StatusRequestSignal):
                error_status = self.status_snapshot.model_dump()
                error_status["error"] = str(e)
                self.send(sender, error_status)

    def _handle_signal(self, message: SignalMessage, sender):
        """Process control signals."""
        if message.type == Signal.STOP:
            logger.info("Monitor stopping")
            self._ack(sender)

    def _handle_status_update(self, message: StatusUpdateMessage):
        """Update status snapshot from orchestrator."""
        logger.info(f"Status updated: {message.status.value} ({message.progress}%)")
        self.status_snapshot = status_uptate_to_snapshot(message)

    def _handle_status_request(
        self, message: StatusRequestSignal, sender: ActorAddress
    ):
        """Respond immediately with current snapshot to API server."""

        self.send(
            sender,
            StatusSnapshotMessage(
                status=self.status_snapshot.status,
                progress=self.status_snapshot.progress,
                summary=self.status_snapshot.summary,
                metrics=self.status_snapshot.metrics,
                last_updated=self.status_snapshot.last_updated,
            ),
        )

    def _ack(self, sender):
        """Reply with a signal message."""
        self.send(
            sender,
            SignalMessage(
                signal=Signal.ACKED,
                from_agent=ActorName.MONITOR,
                to_agent=ActorName.ORCHESTRATOR,
            ),
        )
