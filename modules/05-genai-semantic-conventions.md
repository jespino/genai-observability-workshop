---
description: How the conventions describe model calls, tools and agents, in metrics, events and spans.
part: The application
duration: 30 min
---

# GenAI Semantic Conventions

You've seen why shared names matter, and you've seen what an agent does. The GenAI semantic
conventions bring those together. They define how to describe model calls, tool executions
and agent invocations, so that any tool can answer questions about your agent without
knowing how you built it.

## Learning objectives

By the end of this module, you'll be able to:

- [ ] Say how mature the conventions are, and what that means for you
- [ ] Name the operations that the conventions describe
- [ ] Say which signal each piece of information belongs to
- [ ] Explain why prompts and answers aren't recorded by default

## A moving target

> [!WARNING] Read this before searching the web
> The GenAI conventions are in **Development**, and they're changing fast. Most articles,
> including recent ones, describe names that no longer exist.

In 2026, the conventions moved out of the main repository to their own, at
[open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai).
That repository has no tagged release yet, so this workshop follows
[commit `e6658f1`](https://github.com/open-telemetry/semantic-conventions-genai/tree/e6658f1)
of 6 November 2026. Here's what you'll find elsewhere, and what replaced it:

| You may see | Current name |
|---|---|
| `gen_ai.system` | `gen_ai.provider.name` |
| `gen_ai.client.token.usage` | Separate counters and histograms for input and output |
| `gen_ai.client.operation.duration`, for model calls | `gen_ai.client.inference.duration` |
| `gen_ai.user.message` and other per-message events | `gen_ai.client.inference.operation.details` |
| `gen_ai.client.operation.exception`, for model calls | `gen_ai.client.inference.exception` |
| `invoke_workflow` spans | `invoke_agent` spans |

This changes how you should work with them. Keep the names in one place in your code, know
which version you follow, and expect to update it. Attributes borrowed from the stable core
conventions, like `error.type` and `server.address`, won't change.

## The operations

The conventions identify what happened with `gen_ai.operation.name`. Our agent performs
three of the operations they define:

| `gen_ai.operation.name` | What it is | In our code |
|---|---|---|
| `chat` | One call to the model | `client.chat.completions.create` |
| `execute_tool` | One tool running | `call_tool` |
| `invoke_agent` | One whole run of the agent | `run_agent` |

They nest: `invoke_agent` contains every `chat` and `execute_tool` of a run. There are also
conventions for embeddings, retrieval, memory, MCP, and more, which work the same way.

## The core attributes

A few attributes appear almost everywhere:

| Attribute | Example | Meaning |
|---|---|---|
| `gen_ai.operation.name` | `chat` | The operation |
| `gen_ai.provider.name` | `ollama`, `openai` | Who provides the model |
| `gen_ai.request.model` | `gemma4:e2b` | The model you asked for |
| `gen_ai.response.model` | `gemma4:e2b` | The model that actually answered |
| `gen_ai.agent.name` | `bookshop-assistant` | The agent |
| `gen_ai.tool.name` | `check_stock` | The tool |
| `gen_ai.conversation.id` | a UUID | The conversation it belongs to |
| `gen_ai.usage.input_tokens` | `172` | Tokens read by the model |
| `gen_ai.usage.output_tokens` | `419` | Tokens produced by the model |
| `error.type` | `APIConnectionError` | What failed, if anything failed |

The request and response models can differ. You can ask for an alias, and the provider
tells you which version served it.

## One operation, three signals

Each operation is described in all three signals, and each signal has its own job. Here's
how it works for a model call.

| Signal | What the conventions define | Tells you |
|---|---|---|
| Metrics | `gen_ai.client.inference.duration`, token counters and histograms | Totals and trends, cheaply |
| Logs | The `gen_ai.client.inference.operation.details` event | The details of one call, independently of traces |
| Traces | A `gen_ai.client.inference` span, named `chat {model}` | Where the call sits in a run |

Tools and agents follow the same pattern, with their own metrics and spans.

Note how the conventions apply what you learned about cardinality:
`gen_ai.conversation.id` appears on spans and events, but never on metrics. A metric can
hold a model name, but not a conversation.

## Sensitive content

Prompts and answers are the most useful data you can record, and also the most dangerous.
They can hold personal data, they're often large, and they're frequently subject to
regulation. So the conventions make them **Opt-In**: nothing is captured unless someone
asks for it.

| Attribute | Holds |
|---|---|
| `gen_ai.input.messages` | The messages sent to the model |
| `gen_ai.output.messages` | The messages it returned |
| `gen_ai.system_instructions` | System instructions, when sent apart from the messages |
| `gen_ai.tool.call.arguments` | The arguments of a tool call |
| `gen_ai.tool.call.result` | The result of a tool call |

A single setting, the `OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT` environment variable,
controls them:

| Value | Effect |
|---|---|
| `NO_CONTENT` | Captures nothing. This is the default |
| `SPAN_ONLY` | Captures content on spans |
| `EVENT_ONLY` | Captures content on events |
| `SPAN_AND_EVENT` | Captures content on both |

Content isn't stored as text. It has a defined structure, a list of messages with typed
parts, so that tools can display it. Here's a model asking for a tool, as captured from our
agent:

```json
[
  {
    "role": "assistant",
    "parts": [
      {
        "type": "tool_call",
        "id": "call_flzkl9pt",
        "name": "search_books",
        "arguments": { "query": "The Trace of Time" }
      }
    ]
  }
]
```

## Exercise: map the agent to the conventions

This one needs no code, but it's the plan for the next three modules. Think of one run of
the agent answering "Is The Trace of Time in stock?", which you know takes three turns.
With instrumentation in place, work out:

1. How many spans does this run produce, and what are they called? Which is the parent?
2. How many times does `gen_ai.client.inference.duration` get recorded?
3. How many times does `gen_ai.execute_tool.duration` get recorded?
4. `gen_ai.invoke_agent.inference_calls` holds the number of model calls in a run. What
   value does this run record? And `gen_ai.invoke_agent.tool_calls`?
5. A teammate suggests adding `gen_ai.conversation.id` to the duration metric, to compare
   conversations. What do you tell them?
6. Your team wants to read the prompts of failed runs in production. What would you check
   before setting `OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT`?

> [!SOLUTION]
> 1. Six: `invoke_agent bookshop-assistant` is the parent of three `chat {model}` spans,
>    `execute_tool search_books` and `execute_tool check_stock`.
> 2. Three times, once per model call.
> 3. Twice, once per tool call.
> 4. `3` model calls and `2` tool calls.
> 5. No. Each conversation would create new time series, and they would never stop growing.
>    Use it to filter spans and events instead.
> 6. What personal data the prompts can hold, who can read the telemetry, how long it's
>    kept, and how much it'll cost. The conventions recommend storing content in external
>    storage for production, and recording only references to it.

## Key takeaways

- The GenAI conventions are in Development. Pin a version, and trust the repository more
  than any article.
- Three operations describe an agent: `chat`, `execute_tool` and `invoke_agent`.
- Each one appears in metrics, logs and traces, and each signal answers different questions.
- Prompts and answers stay out of telemetry unless you opt in.
