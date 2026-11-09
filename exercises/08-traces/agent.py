"""The agent loop: call the model, run the tools it asks for, repeat."""

import json
import time

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

from genai_events import (
    capture_on_spans,
    emit_exception,
    emit_inference_details,
    input_messages,
    output_messages,
    response_attributes,
    tool_definitions,
)
from genai_metrics import (
    AGENT_NAME,
    inference_attributes,
    record_agent,
    record_inference,
    record_tool,
)
from llm import MODEL, client
from tools import FUNCTIONS, TOOLS

SYSTEM_PROMPT = """You are the assistant of a small bookshop. Use your tools to
answer questions about the catalog and the stock: never guess. Search for a book
to get its id, then check its stock. Answer in one or two sentences."""

MAX_TURNS = 6

tracer = trace.get_tracer("bookshop-agent")


class TooManyTurns(Exception):
    pass


def new_conversation():
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def mark_failed(span, error):
    span.set_attribute("error.type", type(error).__name__)
    span.set_status(Status(StatusCode.ERROR, str(error)))


def call_model(messages, conversation_id):
    """Make one model call, then measure it and report it."""
    # TODO 1: run all of this in a CLIENT span named "chat {MODEL}", started with
    # inference_attributes(), record_exception=False, and gen_ai.conversation.id.
    # On failure, call mark_failed. On success, set gen_ai.response.model and
    # response_attributes(response). With capture_on_spans(), also set
    # gen_ai.input.messages, gen_ai.tool.definitions and gen_ai.output.messages.
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
    except Exception as error:
        record_inference(time.perf_counter() - start, error=error)
        emit_inference_details(messages, conversation_id, error=error)
        emit_exception("gen_ai.client.inference.exception", error)
        raise
    record_inference(time.perf_counter() - start, response=response)
    emit_inference_details(messages, conversation_id, response=response)
    return response


def call_tool(call, conversation_id):
    """Run one tool call. A failure goes back to the model as the result."""
    # TODO 2: run all of this in a span named "execute_tool {name}", with the
    # attributes in the module's table, and record_exception=False. Call
    # mark_failed on failure. With capture_on_spans(), also set
    # gen_ai.tool.call.arguments and gen_ai.tool.call.result.
    start = time.perf_counter()
    failure = None
    try:
        function = FUNCTIONS[call.function.name]
        arguments = json.loads(call.function.arguments)
        return json.dumps(function(**arguments))
    except Exception as error:
        failure = error
        emit_exception("gen_ai.execute_tool.exception", error)
        return json.dumps({"error": str(error)})
    finally:
        record_tool(call.function.name, time.perf_counter() - start, failure)


def run_agent(messages, conversation_id):
    """Work on the conversation until the model has a final answer."""
    # TODO 3: run all of this in a span named "invoke_agent {AGENT_NAME}", with the
    # attributes in the module's table, and record_exception=False. Add up the
    # tokens of every model call, and set them as gen_ai.usage.input_tokens and
    # gen_ai.usage.output_tokens at the end. Call mark_failed on failure.
    start = time.perf_counter()
    inference_calls = 0
    tool_calls = 0
    failure = None
    try:
        for _ in range(MAX_TURNS):
            response = call_model(messages, conversation_id)
            inference_calls += 1
            message = response.choices[0].message
            messages.append(
                message.model_dump(
                    exclude_none=True, include={"role", "content", "tool_calls"}
                )
            )

            if not message.tool_calls:
                return message.content

            for call in message.tool_calls:
                tool_calls += 1
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": call_tool(call, conversation_id)}
                )

        raise TooManyTurns(f"no final answer after {MAX_TURNS} turns")
    except Exception as error:
        failure = error
        raise
    finally:
        record_agent(time.perf_counter() - start, inference_calls, tool_calls, failure)
