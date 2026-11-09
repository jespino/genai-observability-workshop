"""A chat in the terminal. Ask one question with: python chat.py --ask "..." """

import argparse

import telemetry
from agent import new_conversation, run_agent
from llm import BASE_URL, MODEL


def ask(messages, text):
    messages.append({"role": "user", "content": text})
    try:
        print(f"assistant> {run_agent(messages)}\n")
    except Exception as error:
        print(f"agent failed> {type(error).__name__}: {error}\n")


def main():
    telemetry.setup()

    parser = argparse.ArgumentParser()
    parser.add_argument("--ask", help="ask one question and exit")
    question = parser.parse_args().ask

    messages = new_conversation()
    if question:
        ask(messages, question)
        return

    print(f"Using {MODEL} at {BASE_URL}. Press Ctrl+D to leave.\n")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if text:
            ask(messages, text)


if __name__ == "__main__":
    main()
