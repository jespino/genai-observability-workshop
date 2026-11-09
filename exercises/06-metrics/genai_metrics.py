"""The GenAI metrics, as the semantic conventions define them."""

from opentelemetry import metrics

from llm import MODEL, PROVIDER, SERVER

AGENT_NAME = "bookshop-assistant"

SECONDS_BUCKETS = [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92]
TOKEN_BUCKETS = [1, 4, 16, 64, 256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304, 16777216, 67108864]
AGENT_SECONDS_BUCKETS = [0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6, 51.2, 102.4, 204.8, 409.6, 900, 1800, 3600, 7200, 14400, 43200, 86400]
CALLS_BUCKETS = [1, 2, 4, 8, 16, 32, 64, 128]

meter = metrics.get_meter("bookshop-agent")

inference_duration = meter.create_histogram(
    "gen_ai.client.inference.duration",
    unit="s",
    description="GenAI client inference operation duration.",
    explicit_bucket_boundaries_advisory=SECONDS_BUCKETS,
)

# TODO 1: create the other eight instruments, following the table in the module.


def inference_attributes(response=None):
    """The attributes that describe one model call."""
    attributes = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": PROVIDER,
        "gen_ai.request.model": MODEL,
        "server.address": SERVER.hostname,
        "server.port": SERVER.port or 443,
    }
    if response is not None:
        attributes["gen_ai.response.model"] = response.model
    return attributes


def with_error(attributes, error):
    """Add error.type if the operation failed."""
    if error is None:
        return attributes
    return {**attributes, "error.type": type(error).__name__}


def record_inference(seconds, response=None, error=None):
    attributes = inference_attributes(response)
    inference_duration.record(seconds, with_error(attributes, error))

    # TODO 2: record the tokens. Read them from response.usage, as prompt_tokens
    # and completion_tokens, and use 0 if there is no response or no usage.
    #  - Both per-call histograms record on every call, with with_error(...).
    #  - Both usage counters add only values above 0, and take the attributes
    #    plus "gen_ai.token.modality": "text", with no error.type.


def record_tool(name, seconds, error=None):
    # TODO 3: record gen_ai.execute_tool.duration, with the attributes
    # gen_ai.tool.name, gen_ai.tool.type ("function") and gen_ai.agent.name,
    # plus error.type if it failed.
    pass


def record_agent(seconds, inference_calls, tool_calls, error=None):
    # TODO 4: record the three invoke_agent metrics. All three take the
    # attributes gen_ai.operation.name ("invoke_agent") and gen_ai.agent.name.
    # The duration also takes gen_ai.request.model, plus error.type if it failed.
    pass
