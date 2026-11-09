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
input_tokens_used = meter.create_counter(
    "gen_ai.client.inference.usage.input_tokens",
    unit="{token}",
    description="The number of input (prompt) tokens used.",
)
output_tokens_used = meter.create_counter(
    "gen_ai.client.inference.usage.output_tokens",
    unit="{token}",
    description="The number of output (completion) tokens used.",
)
input_tokens_per_call = meter.create_histogram(
    "gen_ai.client.inference.operation.input_tokens",
    unit="{token}",
    description="The number of input tokens used per inference operation.",
    explicit_bucket_boundaries_advisory=TOKEN_BUCKETS,
)
output_tokens_per_call = meter.create_histogram(
    "gen_ai.client.inference.operation.output_tokens",
    unit="{token}",
    description="The number of output tokens used per inference operation.",
    explicit_bucket_boundaries_advisory=TOKEN_BUCKETS,
)
tool_duration = meter.create_histogram(
    "gen_ai.execute_tool.duration",
    unit="s",
    description="The duration of a single tool execution.",
    explicit_bucket_boundaries_advisory=SECONDS_BUCKETS,
)
agent_duration = meter.create_histogram(
    "gen_ai.invoke_agent.duration",
    unit="s",
    description="The end-to-end duration of a single agent invocation.",
    explicit_bucket_boundaries_advisory=AGENT_SECONDS_BUCKETS,
)
agent_inference_calls = meter.create_histogram(
    "gen_ai.invoke_agent.inference_calls",
    unit="{inference_call}",
    description="The number of model calls in a single agent invocation.",
    explicit_bucket_boundaries_advisory=CALLS_BUCKETS,
)
agent_tool_calls = meter.create_histogram(
    "gen_ai.invoke_agent.tool_calls",
    unit="{tool_call}",
    description="The number of tool calls in a single agent invocation.",
    explicit_bucket_boundaries_advisory=CALLS_BUCKETS,
)


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
    usage = response.usage if response is not None else None
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0

    inference_duration.record(seconds, with_error(attributes, error))
    input_tokens_per_call.record(input_tokens, with_error(attributes, error))
    output_tokens_per_call.record(output_tokens, with_error(attributes, error))

    # Counters take strictly positive contributions, split by modality.
    token_attributes = {**attributes, "gen_ai.token.modality": "text"}
    if input_tokens > 0:
        input_tokens_used.add(input_tokens, token_attributes)
    if output_tokens > 0:
        output_tokens_used.add(output_tokens, token_attributes)


def record_tool(name, seconds, error=None):
    attributes = {
        "gen_ai.tool.name": name,
        "gen_ai.tool.type": "function",
        "gen_ai.agent.name": AGENT_NAME,
    }
    tool_duration.record(seconds, with_error(attributes, error))


def record_agent(seconds, inference_calls, tool_calls, error=None):
    attributes = {
        "gen_ai.operation.name": "invoke_agent",
        "gen_ai.agent.name": AGENT_NAME,
    }
    agent_duration.record(
        seconds,
        with_error({**attributes, "gen_ai.request.model": MODEL}, error),
    )
    agent_inference_calls.record(inference_calls, attributes)
    agent_tool_calls.record(tool_calls, attributes)
