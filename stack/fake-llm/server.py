"""A scripted stand-in for a model, speaking a small part of the OpenAI API.

There is no intelligence here. It looks up a book, checks its stock and reports
what it found, which is all the workshop needs when no real model is available.
"""

import json
import random
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def tool_call(name, arguments):
    return {
        "id": f"call_{uuid.uuid4().hex[:12]}",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }


def next_step(messages):
    """Decide what to do, from the last message only."""
    last = messages[-1]
    if last["role"] == "user":
        return None, tool_call("search_books", {"query": last["content"]})

    result = json.loads(last["content"])
    if result.get("books"):
        return None, tool_call("check_stock", {"book_id": result["books"][0]["id"]})
    if "books" in result:
        return "I can't find that book in our catalog.", None
    if "error" in result:
        return f"Sorry, I couldn't check that: {result['error']}", None
    return f"Yes, we have {result['copies']} copies of that book.", None


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        content, call = next_step(request["messages"])
        time.sleep(random.uniform(0.2, 0.8))

        prompt_size = sum(len(str(m.get("content"))) for m in request["messages"])
        output_size = len(content or json.dumps(call))
        body = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request["model"],
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "tool_calls" if call else "stop",
                    "message": {
                        "role": "assistant",
                        "content": content,
                        **({"tool_calls": [call]} if call else {}),
                    },
                }
            ],
            "usage": {
                "prompt_tokens": prompt_size // 4,
                "completion_tokens": output_size // 4,
                "total_tokens": (prompt_size + output_size) // 4,
            },
        }
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
