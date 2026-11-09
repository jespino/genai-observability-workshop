"""The agent loop: call the model, run the tools it asks for, repeat."""

import json

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


def call_tool(call):
    """Run one tool call. A failure goes back to the model as the result."""
    try:
        function = FUNCTIONS[call.function.name]
        arguments = json.loads(call.function.arguments)
        return json.dumps(function(**arguments))
    except Exception as error:
        return json.dumps({"error": str(error)})


def run_agent(messages):
    """Work on the conversation until the model has a final answer."""
    # TODO 1: repeat all of this, at most MAX_TURNS times.
    response = client.chat.completions.create(
        model=MODEL, messages=messages, tools=TOOLS
    )
    message = response.choices[0].message
    messages.append(
        message.model_dump(exclude_none=True, include={"role", "content", "tool_calls"})
    )

    # TODO 2: if the model asked for tools (message.tool_calls), run each one
    # with call_tool(call), add its result to the messages, and go round again.
    # A result is a message like this:
    #   {"role": "tool", "tool_call_id": call.id, "content": call_tool(call)}

    return message.content
    # TODO 3: if the loop runs out of turns, raise TooManyTurns.
