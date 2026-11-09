"""The agent loop: call the model, run the tools it asks for, repeat."""

import json

from llm import MODEL, client
from tools import FUNCTIONS, TOOLS

# TODO 5: import what you need from genai_metrics, and the time module.

SYSTEM_PROMPT = """You are the assistant of a small bookshop. Use your tools to
answer questions about the catalog and the stock: never guess. Search for a book
to get its id, then check its stock. Answer in one or two sentences."""

MAX_TURNS = 6


class TooManyTurns(Exception):
    pass


def new_conversation():
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def call_model(messages):
    """Make one model call."""
    # TODO 6: measure this call with time.perf_counter(), and report it with
    # record_inference, both when it works and when it raises.
    return client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)


def call_tool(call):
    """Run one tool call. A failure goes back to the model as the result."""
    # TODO 7: measure this call and report it with record_tool. A `finally`
    # block covers both ways out of the function.
    try:
        function = FUNCTIONS[call.function.name]
        arguments = json.loads(call.function.arguments)
        return json.dumps(function(**arguments))
    except Exception as error:
        return json.dumps({"error": str(error)})


def run_agent(messages):
    """Work on the conversation until the model has a final answer."""
    # TODO 8: measure the whole invocation, count the model and tool calls, and
    # report them with record_agent, also when the loop raises.
    for _ in range(MAX_TURNS):
        response = call_model(messages)
        message = response.choices[0].message
        messages.append(
            message.model_dump(
                exclude_none=True, include={"role", "content", "tool_calls"}
            )
        )

        if not message.tool_calls:
            return message.content

        for call in message.tool_calls:
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": call_tool(call)}
            )

    raise TooManyTurns(f"no final answer after {MAX_TURNS} turns")
