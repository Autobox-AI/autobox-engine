from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class MetricType(str, Enum):
    GAUGE = "GAUGE"
    COUNTER = "COUNTER"
    SUMMARY = "SUMMARY"
    HISTOGRAM = "HISTOGRAM"


class Tag(BaseModel):
    key: str = Field(description="The key of the tag.")
    value: str = Field(description="The value of the tag.")


class TagDefinition(BaseModel):
    tag: str = Field(description="The name of the tag.")
    description: str = Field(description="The description of the tag.")


class MetricDefinition(BaseModel):
    name: str = Field(description="The name of the metric.")
    description: str = Field(description="The description of the metric.")
    type: MetricType = Field(
        description="The type of the metric. This should be one of the following: counter, gauge, histogram, summary."
    )
    unit: str = Field(
        description="The unit of the metric. Example: 'tasks', 'seconds', 'requests', 'bytes', etc."
    )
    tags: List[TagDefinition] = Field(
        description="The tags of the metric. Example: { 'agent_name': 'agent_1' }"
    )


class Metrics(BaseModel):
    metrics: list[MetricDefinition]


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
    values: List[CounterValue | GaugeValue | HistogramValue | SummaryValue]


class MetricValues(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    values: List[CounterValue | GaugeValue | HistogramValue | SummaryValue]


class MetricCalculatorUpdate(BaseModel):
    name: str = Field(description="The name of the metric.")
    value: CounterValue | GaugeValue | HistogramValue | SummaryValue = Field(
        description="The value of the metric based on metric type."
    )
    tags: List[Tag] = Field(
        description="The tags of the metric based on the metric definition. Example: { 'agent_name': 'agent_1' }"
    )
    thinking_process: str


class MetricCalculator(BaseModel):
    update: list[MetricCalculatorUpdate]


class MetricResponse(BaseModel):
    name: str
    description: str
    type: MetricType
    unit: str
    tags: List[TagDefinition]
    values: List[CounterValue | GaugeValue | HistogramValue | SummaryValue]
