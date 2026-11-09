#!/usr/bin/env bash
# Checks every part of the workshop stack, and that the agent can reach its
# model. Run it from this directory, right after `docker compose up -d`: it
# waits for the stack to come up, then prints one line per check.
#
# It starts nothing. If a line is red, the hints at the bottom say where to look.

cd "$(dirname "$0")" || exit 1

if [ -t 1 ]; then GREEN=$'\e[32m' RED=$'\e[31m' DIM=$'\e[2m' OFF=$'\e[0m'; fi
pass=0
fail=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '  %s✓%s  %s\n' "$GREEN" "$OFF" "$label"
    pass=$((pass + 1))
  else
    printf '  %s✗%s  %s\n' "$RED" "$OFF" "$label"
    fail=$((fail + 1))
  fi
}

http()       { curl -fsS --max-time 5 "$1" >/dev/null; }
# An empty OTLP export, sent the way the agent sends one.
otlp_open()  { curl -fsS --max-time 5 -X POST http://localhost:4318/v1/traces \
                 -H 'content-type: application/json' -d '{}' >/dev/null; }
in_agent()   { docker compose exec -T agent "$@"; }
agent_deps() { in_agent python -c 'import openai, opentelemetry.sdk'; }
# The same kind of call the agent makes, from inside its container.
model() {
  in_agent python - <<'CHECK'
import os
from openai import OpenAI

client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"],
                max_retries=0, timeout=120)
client.chat.completions.create(
    model=os.environ["LLM_MODEL"],
    messages=[{"role": "user", "content": "Say hello in three words."}],
)
CHECK
}

ready() {
  http http://localhost:8428/health && http http://localhost:9428/health \
    && http http://localhost:10428/health && otlp_open \
    && http http://localhost:3000/api/health && in_agent test -f /tmp/ready
}

echo
echo "  Workshop doctor"
echo

if [ -z "$(docker compose ps --services --status running 2>/dev/null)" ]; then
  printf '  %sThe stack is not running.%s Start it with: docker compose up -d\n\n' "$RED" "$OFF"
  exit 1
fi

if ! ready >/dev/null 2>&1; then
  printf '  Waiting for the stack to come up'
  for _ in $(seq 1 90); do
    ready >/dev/null 2>&1 && break
    printf '.'; sleep 2
  done
  printf '\n\n'
fi

check "VictoriaMetrics      :8428"   http http://localhost:8428/health
check "VictoriaLogs         :9428"   http http://localhost:9428/health
check "VictoriaTraces       :10428"  http http://localhost:10428/health
check "Collector (OTLP)     :4318"   otlp_open
check "Grafana              :3000"   http http://localhost:3000/api/health
check "Agent dependencies installed" agent_deps

model_label="The model answers ($(in_agent sh -c 'echo "$LLM_MODEL at $LLM_BASE_URL"' 2>/dev/null))"
check "$model_label" model

echo
if [ "$fail" -eq 0 ]; then
  printf '  %sAll %d checks passed.%s You are ready.\n\n' "$GREEN" "$pass" "$OFF"
  echo "  Grafana: http://localhost:3000"
  echo
  exit 0
fi

printf '  %s%d of %d checks failed.%s\n\n' "$RED" "$fail" "$((pass + fail))" "$OFF"
printf '  %sWhere to look:%s\n' "$DIM" "$OFF"
printf '    A service           docker compose ps -a, then docker compose logs SERVICE\n'
printf '    Dependencies        docker compose logs agent (the first start downloads them)\n'
printf '    The model           check llm.env, then run docker compose up -d to apply it\n'
printf '    Ollama on Linux     it listens on 127.0.0.1 only: start it with OLLAMA_HOST=0.0.0.0\n'
printf '    No model at all     switch llm.env to the stand-in, at the bottom of the file\n\n'
exit 1
