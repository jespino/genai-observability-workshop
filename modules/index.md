An AI agent can fail while every request succeeds. It can call the wrong tool, loop until
it burns through your budget, or hide a broken dependency behind a polite answer. In this
workshop you'll build a small agent and instrument it so that you can see all of that,
using OpenTelemetry and the GenAI semantic conventions.

## Prerequisites

- Comfortable reading and writing Python
- Docker with the Compose plugin. Everything runs in containers, so you don't need Python
  installed
- Any model with an OpenAI-compatible API: local, hosted or, as a last resort, the
  stand-in included in the workshop

You don't need any experience with OpenTelemetry or with building AI applications.

## How this workshop works

Work through the modules in order. Each one explains an idea and then asks you to try it,
and every instrumentation exercise starts where the previous one finished. If you get
stuck, the hints and solutions are in the module.

<!-- modules -->
