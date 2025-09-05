from datetime import datetime

from autobox.schemas.message import StatusUpdateMessage
from autobox.schemas.status import StatusSnapshot


def status_uptate_to_snapshot(status_update: StatusUpdateMessage) -> StatusSnapshot:
    return StatusSnapshot(
        status=status_update.status,
        progress=status_update.progress,
        summary=status_update.summary,
        metrics=status_update.metrics,
        last_updated=datetime.now(),
    )
