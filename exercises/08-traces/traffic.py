"""Sends a batch of questions to the agent, to give the telemetry some data."""

import argparse
import uuid

import telemetry
from agent import new_conversation, run_agent

QUESTIONS = [
    "Is The Trace of Time in stock?",
    "Do you have Spans of Control?",
    "Can I buy A Field Guide to Logs?",
    "How many copies of Cardinality Explosion do you have?",
    "Do you have anything by Priya Raman?",
    "Do you sell Moby Dick?",
]


def main():
    telemetry.setup()

    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=1)
    rounds = parser.parse_args().rounds

    for round_number in range(1, rounds + 1):
        for question in QUESTIONS:
            print(f"[{round_number}/{rounds}] {question}")
            messages = new_conversation()
            messages.append({"role": "user", "content": question})
            try:
                print(f"  {run_agent(messages, str(uuid.uuid4()))}")
            except Exception as error:
                print(f"  failed: {type(error).__name__}")


if __name__ == "__main__":
    main()
