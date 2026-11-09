"""One span, one metric and one log record, sent to the Collector."""

from opentelemetry import metrics, trace
from opentelemetry._logs import SeverityNumber, get_logger, set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Who is producing this telemetry. Every signal carries it.
resource = Resource.create({"service.name": "hello-otel"})

# The SDK: providers, and how each signal gets exported. Exporters send to
# the Collector, at the address the stack sets in OTEL_EXPORTER_OTLP_ENDPOINT.
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(tracer_provider)

meter_provider = MeterProvider(
    resource=resource, metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())]
)
metrics.set_meter_provider(meter_provider)

logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
set_logger_provider(logger_provider)

# The API: this is all that instrumented code ever touches.
tracer = trace.get_tracer("hello-otel")
meter = metrics.get_meter("hello-otel")
logger = get_logger("hello-otel")

greetings = meter.create_counter("hello.greetings", unit="{greeting}")


def greet(name):
    with tracer.start_as_current_span("greet") as span:
        span.set_attribute("greeting.name", name)
        greetings.add(1, {"greeting.name": name})
        logger.emit(severity_number=SeverityNumber.INFO, body=f"Greeted {name}")
        print(f"Hello, {name}!")


greet("Ada")
greet("Grace")
