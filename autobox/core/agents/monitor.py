"""Monitor actor for tracking simulation status without blocking the orchestrator."""

from datetime import datetime

from thespian.actors import ActorAddress, ActorExitRequest

from autobox.core.agents.base import BaseAgent
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.message import (
    InitMonitor,
    Signal,
    SignalMessage,
    StatusRequestSignal,
    StatusSnapshotMessage,
    StatusUpdateMessage,
)
from autobox.schemas.simulation import SimulationStatus


class Monitor(BaseAgent):
    """
    Lightweight actor that maintains simulation status separately from the orchestrator.
    Receives push updates from orchestrator and serves queries from CacheManager.
    """

    def __init__(self):
        """Initialize with a default status snapshot."""
        super().__init__(name="monitor")

        self.status_snapshot = StatusSnapshotMessage(
            status=SimulationStatus.NEW,
            orchestrator_status=ActorStatus.INITIALIZED,
            progress=0,
            summary="Initializing",
            metrics=[],
            last_updated=datetime.now(),
        )

    def receiveMessage(self, message, sender):
        if isinstance(message, InitMonitor):
            self.name = ActorName.MONITOR.value
            self._ack(sender)
            return

        self.memory.add_message(message)

        if isinstance(message, ActorExitRequest):
            return self._handle_exit_signal()

        try:
            if isinstance(message, StatusRequestSignal):
                self._handle_status_request(message, sender)
            elif isinstance(message, SignalMessage):
                self._handle_signal(message, sender)
            elif isinstance(message, StatusUpdateMessage):
                self._handle_status_update(message, sender)
            else:
                self.logger.warning(
                    f"Monitor received unknown message type: {type(message)}"
                )

        except Exception as e:
            self.logger.error(f"Monitor error handling message: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")

            if isinstance(message, StatusRequestSignal):
                self.send(sender, self.status_snapshot)

    def _handle_signal(self, message: SignalMessage, sender: ActorAddress):
        """Handle control signals."""
        if message.type == Signal.STOP:
            self._handle_stop_signal()

    def _handle_status_update(self, message: StatusUpdateMessage, sender: ActorAddress):
        """Store the latest status snapshot from Orchestrator."""
        try:
            from datetime import datetime

            self.status_snapshot = StatusSnapshotMessage(
                status=message.status,
                orchestrator_status=message.orchestrator_status,
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
                orchestrator_status=self.status_snapshot.orchestrator_status,
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
