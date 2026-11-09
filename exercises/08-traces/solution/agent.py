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
    with tracer.start_as_current_span(
        f"chat {MODEL}",
        kind=SpanKind.CLIENT,
        attributes=inference_attributes(),
        record_exception=False,
    ) as span:
        span.set_attribute("gen_ai.conversation.id", conversation_id)
        if capture_on_spans():
            span.set_attribute("gen_ai.input.messages", input_messages(messages))
            span.set_attribute("gen_ai.tool.definitions", tool_definitions())

        start = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS
            )
        except Exception as error:
            mark_failed(span, error)
            record_inference(time.perf_counter() - start, error=error)
            emit_inference_details(messages, conversation_id, error=error)
            emit_exception("gen_ai.client.inference.exception", error)
            raise

        span.set_attribute("gen_ai.response.model", response.model)
        span.set_attributes(response_attributes(response))
        if capture_on_spans():
            span.set_attribute("gen_ai.output.messages", output_messages(response))

        record_inference(time.perf_counter() - start, response=response)
        emit_inference_details(messages, conversation_id, response=response)
        return response


def call_tool(call, conversation_id):
    """Run one tool call. A failure goes back to the model as the result."""
    name = call.function.name
    with tracer.start_as_current_span(
        f"execute_tool {name}",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": name,
            "gen_ai.tool.type": "function",
            "gen_ai.tool.call.id": call.id,
            "gen_ai.agent.name": AGENT_NAME,
            "gen_ai.conversation.id": conversation_id,
        },
        record_exception=False,
    ) as span:
        start = time.perf_counter()
        failure = None
        try:
            function = FUNCTIONS[name]
            arguments = json.loads(call.function.arguments)
            if capture_on_spans():
                span.set_attribute("gen_ai.tool.call.arguments", arguments)
            result = function(**arguments)
            if capture_on_spans():
                span.set_attribute("gen_ai.tool.call.result", result)
            return json.dumps(result)
        except Exception as error:
            failure = error
            mark_failed(span, error)
            emit_exception("gen_ai.execute_tool.exception", error)
            return json.dumps({"error": str(error)})
        finally:
            record_tool(name, time.perf_counter() - start, failure)


def run_agent(messages, conversation_id):
    """Work on the conversation until the model has a final answer."""
    with tracer.start_as_current_span(
        f"invoke_agent {AGENT_NAME}",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": AGENT_NAME,
            "gen_ai.request.model": MODEL,
            "gen_ai.conversation.id": conversation_id,
        },
        record_exception=False,
    ) as span:
        start = time.perf_counter()
        inference_calls = 0
        tool_calls = 0
        input_tokens = 0
        output_tokens = 0
        failure = None
        try:
            for _ in range(MAX_TURNS):
                response = call_model(messages, conversation_id)
                inference_calls += 1
                if response.usage:
                    input_tokens += response.usage.prompt_tokens
                    output_tokens += response.usage.completion_tokens
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
                    result = call_tool(call, conversation_id)
                    messages.append(
                        {"role": "tool", "tool_call_id": call.id, "content": result}
                    )

            raise TooManyTurns(f"no final answer after {MAX_TURNS} turns")
        except Exception as error:
            failure = error
            mark_failed(span, error)
            raise
        finally:
            span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
            span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
            record_agent(
                time.perf_counter() - start, inference_calls, tool_calls, failure
            )
