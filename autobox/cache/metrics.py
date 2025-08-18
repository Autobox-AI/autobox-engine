from typing import Dict

from pydantic import BaseModel

from autobox.schemas.metrics import Metric


class MetricsCache(BaseModel):
    metrics: Dict[str, Metric] = {}

    def update(self, metric_name: str, value: float):
        metric = self.metrics.get(metric_name, None)
        if metric is not None:
            metric.value = value
        # TODO: else

    def get_all_values(self):
        return self.metrics
