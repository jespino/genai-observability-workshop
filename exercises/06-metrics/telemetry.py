"""OpenTelemetry SDK setup. The exporter sends to the Collector, at
the address in OTEL_EXPORTER_OTLP_ENDPOINT, which docker-compose.yml sets."""

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


def setup():
    resource = Resource.create({"service.name": "bookshop-agent"})

    metrics.set_meter_provider(
        MeterProvider(
            resource=resource,
            metric_readers=[
                PeriodicExportingMetricReader(
                    OTLPMetricExporter(), export_interval_millis=5000
                )
            ],
        )
    )
