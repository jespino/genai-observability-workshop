"""The GenAI events, as the semantic conventions define them."""

import json
import os
import traceback

from opentelemetry._logs import SeverityNumber, get_logger

from genai_metrics import inference_attributes
from tools import TOOLS

logger = get_logger("bookshop-agent")

CAPTURE_CONTENT = os.environ.get(
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT", "NO_CONTENT"
).upper()


def capture_on_events():
    return CAPTURE_CONTENT in ("EVENT_ONLY", "SPAN_AND_EVENT")


def to_parts(message):
    """Turn one OpenAI-style message into the parts the conventions define."""
    parts = []
    if message.get("role") == "tool":
        parts.append(
            {
                "type": "tool_call_response",
                "id": message["tool_call_id"],
                "response": json.loads(message["content"]),
            }
        )
        return parts
    if message.get("content"):
        parts.append({"type": "text", "content": message["content"]})
    for call in message.get("tool_calls", []):
        parts.append(
            {
                "type": "tool_call",
                "id": call["id"],
                "name": call["function"]["name"],
                "arguments": json.loads(call["function"]["arguments"]),
            }
        )
    return parts


def input_messages(messages):
    return [{"role": m["role"], "parts": to_parts(m)} for m in messages]


def output_messages(response):
    message = response.choices[0].message.model_dump(exclude_none=True)
    return [{"role": "assistant", "parts": to_parts(message)}]


def tool_definitions():
    return [{"type": tool["type"], **tool["function"]} for tool in TOOLS]


def response_attributes(response):
    """What the response says about the model call."""
    attributes = {
        "gen_ai.response.id": response.id,
        "gen_ai.response.finish_reasons": [
            choice.finish_reason for choice in response.choices
        ],
    }
    if response.usage:
        attributes["gen_ai.usage.input_tokens"] = response.usage.prompt_tokens
        attributes["gen_ai.usage.output_tokens"] = response.usage.completion_tokens
    return attributes


def emit_inference_details(messages, conversation_id, response=None, error=None):
    attributes = inference_attributes(response)
    attributes["gen_ai.conversation.id"] = conversation_id
    if response is not None:
        attributes.update(response_attributes(response))
    if error is not None:
        attributes["error.type"] = type(error).__name__

    if capture_on_events():
        attributes["gen_ai.input.messages"] = input_messages(messages)
        attributes["gen_ai.tool.definitions"] = tool_definitions()
        if response is not None:
            attributes["gen_ai.output.messages"] = output_messages(response)

    logger.emit(
        event_name="gen_ai.client.inference.operation.details",
        severity_number=SeverityNumber.DEBUG,
        attributes=attributes,
    )


def emit_exception(event_name, error):
    logger.emit(
        event_name=event_name,
        severity_number=SeverityNumber.WARN,
        attributes={
            "exception.type": type(error).__name__,
            "exception.message": str(error),
            "exception.stacktrace": "".join(traceback.format_exception(error)),
        },
    )
