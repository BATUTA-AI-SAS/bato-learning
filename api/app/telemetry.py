from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .settings import settings


def setup_tracing() -> None:
    provider = TracerProvider(resource=Resource.create({"service.name": "bato-learning-api"}))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.phoenix_collector_endpoint))
    )
    trace.set_tracer_provider(provider)

    try:
        from openinference.instrumentation.anthropic import AnthropicInstrumentor

        AnthropicInstrumentor().instrument(tracer_provider=provider)
    except Exception:
        pass

    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor

        LangChainInstrumentor().instrument(tracer_provider=provider)
    except Exception:
        pass
