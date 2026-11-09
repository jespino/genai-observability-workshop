---
description: Emit GenAI events for each model call and failure, and capture prompts and answers only when you opt in.
part: Instrumenting the agent
duration: 30 min
---

# Logs

Metrics tell you that three tool calls failed. They can't tell you what the error said, or
what the model was asked. That level of detail belongs to logs, one record per thing that
happened. For GenAI, the conventions define those records precisely, as events.

## Learning objectives

By the end of this module, you'll be able to:

- [ ] Explain what an event is, and how it relates to a log record
- [ ] Emit the events that the conventions define
- [ ] Turn messages into the structure that the conventions require
- [ ] Control content capture, and explain the default

## Events

An **event** is a log record with a name. The name, in the `event_name` field, states what
kind of thing happened and what attributes to expect, so that a tool can process it without
parsing any text.

```python
logger.emit(
    event_name="gen_ai.execute_tool.exception",
    severity_number=SeverityNumber.WARN,
    attributes={"exception.type": "WarehouseTimeout"},
)
```

Our agent needs three events:

| Event | When | Severity |
|---|---|---|
| `gen_ai.client.inference.operation.details` | After each model call, whatever the outcome | `DEBUG` |
| `gen_ai.client.inference.exception` | A model call failed | `WARN` |
| `gen_ai.execute_tool.exception` | A tool failed | `WARN` |

### The details event

The details event describes one model call in full. It takes the attributes you recorded on
the metrics, and adds the ones that were too detailed or too high in cardinality for them:

| Attribute | Example |
|---|---|
| `gen_ai.conversation.id` | A UUID, created by `chat.py` |
| `gen_ai.response.id` | `chatcmpl-700` |
| `gen_ai.response.finish_reasons` | `["tool_calls"]` |
| `gen_ai.usage.input_tokens` | `172` |
| `gen_ai.usage.output_tokens` | `419` |
| `error.type` | Only on failure |

If content capture is on, it also takes `gen_ai.input.messages`, `gen_ai.output.messages`
and `gen_ai.tool.definitions`. Our system prompt travels as a message, so it goes in
`gen_ai.input.messages` too. `gen_ai.system_instructions` is for APIs that send it apart
from the chat history.

### The exception events

These hold `exception.type`, `exception.message` and `exception.stacktrace`. The last two can
hold sensitive data, such as a customer's email in an error message, so treat them with the
same care as anything else you log.

## Exercise: emit the events

This module's files are in `exercises/07-logs`. They're your solution from the previous
module, with these additions:

- `telemetry.py` now also sets up logs.
- `chat.py` and `traffic.py` create a conversation ID and pass it to `run_agent`.
- `genai_events.py` holds the new code.

The hard part of `genai_events.py` is done. The function `to_parts` turns the API's messages
into the structure the conventions require, so you can focus on the events:

<!-- include: exercises/07-logs/genai_events.py lines=23-46 -->

The file also has `capture_on_events`, which reads the setting:

<!-- include: exercises/07-logs/genai_events.py lines=14-20 -->

### In `genai_events.py`

1. **TODO 1**: Build the attributes in `emit_inference_details`.
2. **TODO 2**: Add the content, but only if `capture_on_events()` says so.
3. **TODO 3**: Emit the event.

   > [!SOLUTION]
   > <!-- include: exercises/07-logs/solution/genai_events.py lines=76-94 -->

4. **TODO 4**: Finish `emit_exception`.

   > [!SOLUTION]
   > <!-- include: exercises/07-logs/solution/genai_events.py lines=97-106 -->

### In `agent.py`

5. **TODO 5**: Import the two functions.
6. **TODO 6** and **TODO 7**: Emit the details event on both paths in `call_model`, and the
   exception event when it fails.

   > [!SOLUTION]
   > <!-- include: exercises/07-logs/solution/agent.py lines=26-40 -->

7. **TODO 8**: Emit `gen_ai.execute_tool.exception` when a tool fails.

### Run it

First, run it with the default settings:

```bash
docker compose exec agent python 07-logs/traffic.py
docker compose exec -e LLM_BASE_URL=http://localhost:1/v1 agent \
  python 07-logs/chat.py --ask "Is The Trace of Time in stock?"
```

### Verify the result

Open Explore in Grafana, and choose the VictoriaLogs data source. Its queries use LogsQL.

> [!NOTE]
> You'll see a `missing _msg field` message in place of the log text. Events have
> attributes rather than a text body, so there's nothing to show there. Expand a record to
> see its fields.

- [ ] See every kind of event, with its severity:

  ```logsql
  service.name:"bookshop-agent" | stats by (event_name, severity_text) count() events
  ```

- [ ] Find the tool failures and what they said:

  ```logsql
  event_name:"gen_ai.execute_tool.exception" | fields _time, exception.type, exception.message
  ```

  There it is: `warehouse did not answer for bk-004`. It's the first time the failure
  has a reason.

- [ ] Add up tokens per model, straight from the events:

  ```logsql
  event_name:"gen_ai.client.inference.operation.details" | stats by (gen_ai.request.model) sum(gen_ai.usage.input_tokens) input, sum(gen_ai.usage.output_tokens) output
  ```

- [ ] Check that no content was captured. This should find no records at all:

  ```logsql
  gen_ai.input.messages:*
  ```

### Turn on content capture

Now opt in, for one run, and ask a question:

```bash
docker compose exec -e OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT=EVENT_ONLY agent \
  python 07-logs/chat.py --ask "Do you have Spans of Control?"
```

- [ ] Run this query, and read what the model received and returned on each turn:

  ```logsql
  gen_ai.input.messages:* | fields _time, gen_ai.input.messages, gen_ai.output.messages
  ```

Watch the input grow from one record to the next. Each turn sends the whole conversation
again, which is why the input tokens climb.

> [!WARNING]
> You've just written a user's words to your log store. That's fine here. In production,
> everyone who can read those logs can now read those conversations, for as long as you keep
> them.

## Key takeaways

- An event is a log record with a name, which gives it a known structure.
- The details event records one model call in full, including what's too detailed for
  metrics.
- Failures get their own events at `WARN`, with the error message that metrics can't hold.
- Content capture is off by default, and turning it on has consequences.
