"""Monitor actor for tracking simulation status without blocking the orchestrator."""

from datetime import datetime

from thespian.actors import Actor, ActorAddress, ActorExitRequest

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

logger = LoggerManager.get_runner_logger()


class Monitor(Actor):
    """
    Lightweight actor that maintains simulation status separately from the orchestrator.
    Receives push updates from orchestrator and serves queries from CacheManager.
    """

    def __init__(self):
        """Initialize with a default status snapshot."""

        self.logger = LoggerManager.get_logger("runner")
        self.status_snapshot = StatusSnapshotMessage(
            status=SimulationStatus.NEW,
            progress=0,
            summary="Initializing",
            metrics=[],
            last_updated=datetime.now(),
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
                self._handle_status_update(message, sender)
            elif isinstance(message, ActorExitRequest):
                self.logger.info("Monitor received ActorExitRequest - terminating")
                pass
            else:
                logger.warning(
                    f"Monitor received unknown message type: {type(message)}"
                )

        except Exception as e:
            self.logger.error(f"Monitor error handling message: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")

            # Still try to respond to status requests even on error
            if isinstance(message, StatusRequestSignal):
                self.send(sender, self.status_snapshot)

    def _handle_signal(self, message: SignalMessage, sender: ActorAddress):
        """Handle control signals."""
        if message.type == Signal.INIT:
            self._ack(sender)
        elif message.type == Signal.STOP:
            if message.to_agent == "monitor" or message.to_agent == ActorName.MONITOR:
                self.logger.info(
                    "Monitor received STOP signal - shutting down gracefully"
                )
                self._ack(sender)
                self.send(self.myAddress, ActorExitRequest())
            else:
                self.logger.debug(
                    f"Monitor ignoring STOP signal for {message.to_agent}"
                )

    def _handle_status_update(self, message: StatusUpdateMessage, sender: ActorAddress):
        """Store the latest status snapshot from Orchestrator."""
        try:
            from datetime import datetime

            # Create a proper StatusSnapshotMessage with current timestamp
            self.status_snapshot = StatusSnapshotMessage(
                status=message.status,
                progress=message.progress,
                summary=message.summary,
                metrics=message.metrics,
                last_updated=datetime.now(),
            )
            self.logger.debug(
                f"Monitor updated status: {message.status.value}, progress: {message.progress}"
            )
        except Exception as e:
            self.logger.error(f"Monitor failed to update status: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")

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
