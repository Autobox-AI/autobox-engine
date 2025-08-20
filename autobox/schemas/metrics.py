from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class MetricType(str, Enum):
    GAUGE = "GAUGE"
    COUNTER = "COUNTER"
    SUMMARY = "SUMMARY"
    HISTOGRAM = "HISTOGRAM"


class MetricDefinition(BaseModel):
    name: str
    description: str
    type: Literal["counter", "gauge", "histogram"]
    unit: str


class Metrics(BaseModel):
    metrics: list[MetricDefinition]


class MetricPanelOptions(BaseModel):
    displayLabels: List[str]


class MetricPanel(BaseModel):
    type: Literal[
        "graph",
        "stat",
        "gauge",
        "heatmap",
        "timeseries",
        "piechart",
        "barchart",
        "bargauge",
    ]
    expression: str
    legend_format: str
    options: Optional[MetricPanelOptions] = None


class MetricValue(BaseModel):
    dt: str = Field(alias="_time", description="Timestamp of the metric value")


class CounterValue(MetricValue):
    value: int


class GaugeValue(MetricValue):
    value: float


class Bucket(MetricValue):
    le: float
    count: int


class HistogramValue(MetricValue):
    count: int
    sum: float
    buckets: List[Bucket]


class Quantile(BaseModel):
    quantile: float
    value: float


class SummaryValue(MetricValue):
    count: int
    sum: float
    quantiles: List[Quantile]


class Metric(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    # description: str
    # type: MetricType
    # unit: str
    values: List[CounterValue | GaugeValue | HistogramValue | SummaryValue]


class MetricCalculatorUpdate(BaseModel):
    metric_name: str
    value: float
    agent_name: str
    thinking_process: str


class MetricCalculator(BaseModel):
    update: list[MetricCalculatorUpdate]


class MetricResponse(BaseModel):
    name: str
    description: str
    type: Literal["counter", "gauge", "histogram"]
    unit: str
    value: float = Field(default=0.0)
