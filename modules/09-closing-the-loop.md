---
description: Use all three signals to find a failure the agent hides, then see what changes in production.
part: Wrapping up
duration: 20 min
---

# Closing the Loop

Back in [the chat agent module](04-the-chat-agent.md#verify-the-result), you asked about
*Cardinality Explosion* and got a suspiciously smooth answer. No user would report that as an
error, and no status code would show it. You now have everything you need to find out what
happened, so let's do it, the way you would with a real incident.

## Learning objectives

By the end of this module, you'll be able to:

- [ ] Move from a metric to a log to a trace during an investigation
- [ ] Choose the right signal for each question
- [ ] Name what needs to change before you run this in production

## Exercise: investigate

There are no new files. Keep working in `exercises/08-traces`, and generate some traffic with
content capture on:

```bash
docker compose exec -e OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT=SPAN_ONLY agent \
  python 08-traces/traffic.py --rounds 3
```

### 1. Metrics: notice that something is wrong

Open the **GenAI agent** dashboard. **Failed model calls** covers the last five minutes, and with no
deliberate failures in that window it's at zero, so the model is fine. **Failed tool calls**
isn't, though, and on **Tool duration (p95)** one tool is far slower
than the other.

In Explore, find out which tool, and how it fails:

```promql
sum by (gen_ai_tool_name, error_type) (increase(gen_ai_execute_tool_duration_seconds_count{error_type!=""}[5m]))
```

It's `check_stock`, with `WarehouseTimeout`. Metrics have told you what and how often, and
they can't take you any further.

### 2. Logs: find out why

In VictoriaLogs, read the error, and get a `trace_id`:

```logsql
_time:15m event_name:"gen_ai.execute_tool.exception" | fields _time, trace_id, exception.message
```

Every failure names the same book, `bk-004`. So this isn't the warehouse being flaky: it
fails for one book, every time.

### 3. Traces: see what it did to the user

Paste the `trace_id` into VictoriaTraces, using the **TraceID** query type, and read the run
from top to bottom.

- [ ] How long did the failed `check_stock` span take, compared to the whole run?
- [ ] Open that span. Which book was it checking? Look for `gen_ai.tool.call.arguments.book_id`.
- [ ] Open the last `chat` span. Find the error in `gen_ai.input.messages`, and read what the
      model told the user in `gen_ai.output.messages`.

That last step is the one that matters. The model got an error from the tool, and covered
for it with a polite answer. The user sees no failure, the agent run ends successfully, and
the `invoke_agent` span isn't even marked as failed. **Only the telemetry knows.**

> [!IMPORTANT]
> Look at where you had to go to learn this. The only record that the user got a bad answer
> is in the content you opted in to capture. That's the real trade-off of content capture:
> without it you're safer, but you can see less.

## Which signal for which question

| Question | Signal |
|---|---|
| How much are we spending, and is it growing? | Metrics: the token counters |
| Is the model slow? Are the tools? | Metrics: the duration histograms |
| Is the agent looping more than it used to? | Metrics: `gen_ai.invoke_agent.inference_calls` |
| What was the error? | Logs: the exception events |
| What happened in this particular run? | Traces |
| What did the model see and say? | Traces or logs, with content capture on |

## On the way to production

The workshop took some shortcuts. Before you run this for real, think about these.

- **Content.** Keep capture off, or store content somewhere with its own access controls. The
  conventions define `gen_ai.input.messages_ref` and similar attributes to hold a reference
  to it, rather than the content itself.
- **Redaction.** The Collector can remove or mask attributes before they leave your
  infrastructure, so it's a good place to enforce your rules.
- **Volume.** Traces of agents are large. Use sampling, and consider deciding in the Collector
  once a trace has finished, so that you keep the failed and the slow ones.
- **Export intervals.** Five seconds suits a workshop. The SDK's default is 60.
- **Cost.** Tokens aren't money. The conventions stop at token counts, so you need to
  multiply by your provider's prices, in your dashboards.
- **Instrumentation libraries.** You don't have to write all of this. Libraries exist for
  popular model clients and agent frameworks, such as `opentelemetry-instrumentation-openai-v2`.
  Check which version of the conventions a library follows, because it may be behind.
- **Staying current.** The conventions are still in Development. Keeping names in one place
  makes an update a small change.
- **Checking your telemetry.** [Weaver](https://github.com/open-telemetry/weaver), the
  OpenTelemetry tool behind the conventions, has a `registry live-check` command that compares
  live telemetry to a registry. We used it to check the solutions to this workshop.

## Where to go next

- The [GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai),
  which define streaming metrics, embeddings, retrieval, MCP and more.
- Add a tool to the agent, and see how little of the instrumentation has to change.
- Point the agent at another model, and compare the two on the dashboard.

When you're finished, stop the stack and delete its data:

```bash
docker compose down -v
```

## Key takeaways

- A metric shows that something's wrong, a log says why, and a trace shows what it did.
- Agents can hide their failures from users, so the absence of errors proves nothing.
- Following the conventions gave you all of this with standard names, and it'll work with
  any tool that understands them.

You've taken an application from invisible to observable, with nothing but open standards.
