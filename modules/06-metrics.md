---
description: Record durations, token usage, and agent behavior, using the metrics the conventions define.
part: Instrumenting the agent
duration: 35 min
---

# Metrics

Metrics answer the questions you ask about a whole system: how many tokens did we use
today, how slow is the model, how often do tools fail. They're the cheapest signal to keep,
which makes them what you put on dashboards and alert on. We start with them for that
reason, and because this is where the cost of an agent becomes visible.

## Learning objectives

By the end of this module, you'll be able to:

- [ ] Create instruments that follow the conventions
- [ ] Explain why tokens get both a counter and a histogram
- [ ] Attach the right attributes to each metric, including on failure
- [ ] Query the results and read them on a dashboard

## The metrics we'll record

The conventions define these nine metrics for what our agent does. Each one is a histogram
except for the two usage counters.

| Metric | Type | Unit | Records |
|---|---|---|---|
| `gen_ai.client.inference.duration` | Histogram | `s` | The time of each model call |
| `gen_ai.client.inference.usage.input_tokens` | Counter | `{token}` | Total input tokens |
| `gen_ai.client.inference.usage.output_tokens` | Counter | `{token}` | Total output tokens |
| `gen_ai.client.inference.operation.input_tokens` | Histogram | `{token}` | Input tokens per model call |
| `gen_ai.client.inference.operation.output_tokens` | Histogram | `{token}` | Output tokens per model call |
| `gen_ai.execute_tool.duration` | Histogram | `s` | The time of each tool call |
| `gen_ai.invoke_agent.duration` | Histogram | `s` | The time of each agent run |
| `gen_ai.invoke_agent.inference_calls` | Histogram | `{inference_call}` | Model calls per run |
| `gen_ai.invoke_agent.tool_calls` | Histogram | `{tool_call}` | Tool calls per run |

There are other metrics we skip, like cached tokens, which this workshop leaves out, and
time to first chunk, which only applies to streaming responses.

### A counter and a histogram for tokens

Tokens get two kinds of instrument, because they answer different questions.

- The **counters** add up usage, so they tell you how much you spent. Use them for totals
  and rates.
- The **histograms** describe individual calls, so they tell you what a typical or an
  expensive call looks like. Use them for percentiles and for spotting outliers.

The conventions are firm about this: don't use the histograms to calculate totals or costs.

### Attributes

| Metric | Attributes |
|---|---|
| Model calls: duration and token histograms | `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `server.address`, `server.port`, and `error.type` on failure |
| Token counters | The same, without `error.type`, and with `gen_ai.token.modality` |
| Tool duration | `gen_ai.tool.name`, `gen_ai.tool.type`, `gen_ai.agent.name`, and `error.type` on failure |
| Agent duration | `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.request.model`, and `error.type` on failure |
| Agent call counts | `gen_ai.operation.name`, `gen_ai.agent.name` |

`gen_ai.token.modality` says what kind of token it was, such as `text` or `audio`. Ours are
all `text`.

### Buckets

A histogram sorts values into buckets. Tokens and durations have very different ranges, so
the default buckets don't suit them, and the conventions list which ones to use. You pass
them as advice when you create the instrument. They're already in the starter file.

### Failed calls

Failures need care, because a metric that ignores them lies to you:

- Record the duration of a failed call, with `error.type` set.
- Record the per-call token histograms too, with `0` if there's no usage to report.
- Don't add to the counters, which only take values above zero.

## Exercise: instrument the agent

This module's files are in `exercises/06-metrics`. They contain the finished agent from
before, and three new things:

- `telemetry.py` sets up the SDK. It exports metrics every five seconds, which is good for
  a workshop, and more often than you'd want in production.
- `genai_metrics.py` is where the metrics live.
- `traffic.py` sends a batch of questions, so that you have data to look at.

The starting point has one metric finished, as a model for the others:

<!-- include: exercises/06-metrics/genai_metrics.py lines=16-21 -->

Keeping the names in one file, away from the agent, is deliberate. These names will change,
and when they do you'll want one place to fix them.

The file also has the attributes of a model call, ready to use, and a helper that adds
`error.type`:

<!-- include: exercises/06-metrics/genai_metrics.py lines=26-45 -->

### In `genai_metrics.py`

1. **TODO 1**: Create the other eight instruments, using the table above. Tool durations use
   `SECONDS_BUCKETS`, agent durations `AGENT_SECONDS_BUCKETS`, the per-call tokens
   `TOKEN_BUCKETS`, and the call counts `CALLS_BUCKETS`.

   > [!SOLUTION]
   > <!-- include: exercises/06-metrics/solution/genai_metrics.py lines=22-67 -->

2. **TODO 2**: Finish `record_inference`, which records the tokens of a model call.

   > [!SOLUTION]
   > <!-- include: exercises/06-metrics/solution/genai_metrics.py lines=91-106 -->

3. **TODO 3** and **TODO 4**: Finish `record_tool` and `record_agent`.

   > [!SOLUTION]
   > <!-- include: exercises/06-metrics/solution/genai_metrics.py lines=109-128 -->

### In `agent.py`

4. **TODO 5**: Add the imports.
5. **TODO 6**: In `call_model`, measure the call with `time.perf_counter()`, and call
   `record_inference`, whether it works or raises. Raise the error again afterwards, because
   the caller still needs to know.

   > [!SOLUTION]
   > <!-- include: exercises/06-metrics/solution/agent.py lines=25-36 -->

6. **TODO 7**: Do the same in `call_tool`. This function catches its own errors, so a
   `finally` block is the simplest way to record once, whichever way it ends.

   > [!SOLUTION]
   > <!-- include: exercises/06-metrics/solution/agent.py lines=39-51 -->

7. **TODO 8**: In `run_agent`, count the model and tool calls, and call `record_agent` when
   the run ends, in any way.

   > [!SOLUTION]
   > <!-- include: exercises/06-metrics/solution/agent.py lines=54-85 -->

> [!HINT] Measuring in a function with several exits
> Set `failure = None` before the `try`, assign to it in the `except`, and do your
> recording in the `finally`. This works even with a `return` inside the `try`.

### Run it

```bash
docker compose exec agent python 06-metrics/traffic.py --rounds 2
```

Then make a model call fail, so that you have an error to look at. This points the agent at
a port where nothing is listening, for one command:

```bash
docker compose exec -e LLM_BASE_URL=http://localhost:1/v1 agent \
  python 06-metrics/chat.py --ask "Is The Trace of Time in stock?"
```

### Verify the result

The metrics are in VictoriaMetrics now, under slightly different names, which is the
conversion you saw in [module 2](02-opentelemetry-concepts.md#verify-the-result):

| In the code | In VictoriaMetrics |
|---|---|
| `gen_ai.client.inference.duration` | `gen_ai_client_inference_duration_seconds_bucket`, `_sum` and `_count` |
| `gen_ai.client.inference.usage.input_tokens` | `gen_ai_client_inference_usage_input_tokens_total` |
| `gen_ai.request.model` | `gen_ai_request_model` |

In Grafana's Explore, using the VictoriaMetrics data source, run these queries:

- [ ] How many tokens have you used, by model?

  ```promql
  sum by (gen_ai_request_model) (gen_ai_client_inference_usage_input_tokens_total)
  ```

- [ ] How do the tools compare at the 95th percentile?

  ```promql
  histogram_quantile(0.95, sum by (le, gen_ai_tool_name) (rate(gen_ai_execute_tool_duration_seconds_bucket[5m])))
  ```

- [ ] Which calls failed? You should see `APIConnectionError`.

  ```promql
  sum by (error_type) (gen_ai_client_inference_duration_seconds_count{error_type!=""})
  ```

- [ ] How many model calls does a run take, on average?

  ```promql
  sum(rate(gen_ai_invoke_agent_inference_calls_sum[5m])) / sum(rate(gen_ai_invoke_agent_inference_calls_count[5m]))
  ```

Now open the **GenAI agent** dashboard, under **Dashboards** in Grafana. It's built on these
same names, and it was written before your code existed. It works anyway, because your
telemetry follows the conventions, and so would any other agent's. That's what you get in
return for the care over names.

> [!TIP]
> Do you see a failed tool on the dashboard? `check_stock` has failed calls, even though no
> one reported an error. Keep that in mind.

## Key takeaways

- Keep metric names in one place, because they're still changing.
- Token counters are for totals and cost, and token histograms are for percentiles.
- Record failures too, with `error.type`, or your numbers will look better than they are.
- Following the conventions means that a dashboard can exist before your code does.
