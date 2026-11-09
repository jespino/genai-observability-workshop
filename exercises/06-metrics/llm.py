"""The connection to the model. Configured by llm.env: nothing to change here."""

import os
from urllib.parse import urlparse

from openai import OpenAI

BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.environ.get("LLM_API_KEY", "not-needed")
MODEL = os.environ.get("LLM_MODEL", "gemma4:e2b")
PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")

SERVER = urlparse(BASE_URL)

# No retries, so that a failed request shows up as a failure.
client = OpenAI(base_url=BASE_URL, api_key=API_KEY, max_retries=0, timeout=120)
