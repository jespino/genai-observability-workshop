# Observing GenAI Applications with OpenTelemetry

A half-day, hands-on workshop. Participants learn OpenTelemetry and semantic
conventions, build a small AI agent, and instrument it with metrics, logs and traces
that follow the GenAI semantic conventions.

**The handouts are at <https://jespino.github.io/genai-observability-workshop/>.**
Start with Module 1, which sets up everything below.

## Taking the workshop

All you need is Docker with the Compose plugin, and optionally a model with an
OpenAI-compatible API, such as Ollama. The agent and the whole telemetry stack run in
containers, so you don't need Python installed.

```bash
git clone https://github.com/jespino/genai-observability-workshop.git
cd genai-observability-workshop/stack
docker compose up -d
./doctor.sh
```

| Directory | What it holds |
|---|---|
| `stack/` | The Compose stack: the agent's container, a stand-in model, the OpenTelemetry Collector, VictoriaMetrics, VictoriaLogs, VictoriaTraces and Grafana. Set your model in `stack/llm.env` |
| `exercises/` | The code for each module, and its solution in `solution/`. You edit these files |
| `modules/` | The handouts, in markdown |

To pull every image before the day:

```bash
cd stack && docker compose pull
```

## Building the site

The site is built with [wsbuilder](https://github.com/jespino/wsbuilder).

```bash
wsbuilder watch   # write with live reload
wsbuilder build   # generate the website in dist/
```
