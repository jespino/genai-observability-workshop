---
description: What makes AI applications hard to operate, what you'll build, and getting your environment ready.
part: Getting started
duration: 20 min
---

# Introduction

A traditional service usually tells you when it breaks: an exception, a 500, a latency
spike. An AI application can break while looking healthy. Every model call returns
`200 OK` while the agent loops through ten tool calls, spends a dollar on a question worth
a cent, or tells a customer something false in a confident voice.

To run one of these applications you need to see inside it: which models it called, with
how many tokens, which tools it used, and what happened at each step. OpenTelemetry gives
you a vendor-neutral way to produce that data, and the GenAI semantic conventions define
what it should be called, so that your dashboards and tools all understand it.

## Learning objectives

By the end of this module, you'll have:

- [ ] A clear picture of what the workshop covers
- [ ] The telemetry stack running on your machine
- [ ] A working connection to a model

## What you'll do

The first half builds the foundations, and the second half uses them.

1. **OpenTelemetry concepts**: signals, the API and the SDK, the Collector.
2. **Semantic conventions**: why agreeing on names matters so much.
3. **The chat agent**: a small bookshop assistant, with an agent loop and two tools.
4. **GenAI semantic conventions**: how the spec describes that agent.
5. **Metrics, logs and traces**: instrumenting the agent, one signal at a time.
6. **Closing the loop**: using all three to find a problem the agent is hiding.

We instrument everything by hand, on purpose. Libraries can do much of this for you, but
writing it once shows you what the data means and what the libraries are doing.

## Set up your environment

Everything runs in Docker: the telemetry stack, and the agent you'll build. You don't need
Python on your laptop, only Docker with the Compose plugin and about 4 GB of free memory.

Clone the workshop's repository. It has everything: the stack in `stack/`, and the files
for every exercise in `exercises/`, one directory per module.

```bash
git clone https://github.com/jespino/genai-observability-workshop.git
cd genai-observability-workshop/stack
```

### Connect a model

The agent works with anything that speaks the OpenAI API. Open `llm.env`, and uncomment
or edit the values for yours:

| You use | `LLM_BASE_URL` | `LLM_API_KEY` | `LLM_MODEL` | `LLM_PROVIDER` |
|---|---|---|---|---|
| Ollama (the default) | `http://host.docker.internal:11434/v1` | `not-needed` | `gemma4:e2b` | `ollama` |
| OpenAI | `https://api.openai.com/v1` | your key | a model you have access to | `openai` |
| Anything else | its OpenAI-compatible URL | your key, if any | its model name | its name, in lowercase |
| No model at all | `http://fake-llm:8090/v1` | `not-needed` | `fake-model` | `fake` |

The agent runs in a container, where `localhost` is the container itself. That's why a
model on your laptop is at `host.docker.internal`.

With Ollama, get the model first with `ollama pull gemma4:e2b`. Any model that supports
tool calling works.

> [!WARNING] Ollama on Linux
> Ollama only listens on `127.0.0.1` by default, which the container can't reach. Start it
> with `OLLAMA_HOST=0.0.0.0`, or set that variable in its systemd service.

The last row is a scripted stand-in that runs in the stack. It isn't intelligent, but it
calls the tools and reports token usage, so every exercise works with it.

### Start the stack

Still in `stack`:

```bash
docker compose up -d
./doctor.sh
```

This starts seven containers: the agent, the stand-in model, and the five that make up the
telemetry stack, which you'll look at in the [next module](02-opentelemetry-concepts.md).
The first start takes a few minutes, because the agent installs its Python dependencies
and Grafana installs its plugins. `doctor.sh` waits for all of it, then checks each part,
including a call to your model. Every line should be green.

If you change `llm.env` later, run `docker compose up -d` again to apply it.

Open <http://localhost:3000>, where Grafana should appear with no login.

### Run the agent's code

Keep a terminal in `stack` for the whole workshop. Every command runs from there, and runs
the code in `exercises/` inside the agent's container, which sees that directory as its
own:

```bash
docker compose exec agent python 04-the-chat-agent/chat.py
```

You edit the files on your laptop, with your usual editor. The container sees each change
as soon as you save it, so there's nothing to restart. Since it's a git repository,
`git diff` shows what you've changed, and `git checkout -- <file>` puts a file back the way
it was.

## Key takeaways

- AI applications can fail while every request succeeds, so they need more than status
  codes and error rates.
- OpenTelemetry produces the data, and semantic conventions give it a shared meaning.
- Your stack is running, and your model answers. Next, we'll look at what OpenTelemetry is
  made of.
