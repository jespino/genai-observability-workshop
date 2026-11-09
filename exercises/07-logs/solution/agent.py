"""The agent loop: call the model, run the tools it asks for, repeat."""

import json
import time

from genai_events import emit_exception, emit_inference_details
from genai_metrics import record_agent, record_inference, record_tool
from llm import MODEL, client
from tools import FUNCTIONS, TOOLS

SYSTEM_PROMPT = """You are the assistant of a small bookshop. Use your tools to
answer questions about the catalog and the stock: never guess. Search for a book
to get its id, then check its stock. Answer in one or two sentences."""

MAX_TURNS = 6


class TooManyTurns(Exception):
    pass


def new_conversation():
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def call_model(messages, conversation_id):
    """Make one model call, then measure it and report it."""
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


def call_tool(call):
    """Run one tool call. A failure goes back to the model as the result."""
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
                    {"role": "tool", "tool_call_id": call.id, "content": call_tool(call)}
                )

        raise TooManyTurns(f"no final answer after {MAX_TURNS} turns")
    except Exception as error:
        failure = error
        raise
    finally:
        record_agent(time.perf_counter() - start, inference_calls, tool_calls, failure)
