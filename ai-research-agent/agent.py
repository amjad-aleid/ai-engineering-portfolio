import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq

from tools import TOOL_SCHEMAS, TOOLS

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are a research assistant with tools for securities research and GitHub "
    "lookup: a securities screener (P/E ratio, dividend yield, expense ratio, and "
    "historical growth), a securities comparison tool (expense ratio, dividend "
    "yield, and 1/3/5-year historical performance for a list of symbols), an "
    "investment return calculator (what a fixed dollar amount would be worth today "
    "if invested N years ago, across multiple symbols and multiple time periods), "
    "and GitHub repository search/lookup. Use the tools whenever the user asks "
    "about specific investments, screening criteria, comparisons between tickers, "
    "hypothetical investment calculations, or GitHub projects. When reporting "
    "results, always use the actual figures returned by the tool."
)


def run_agent(client: Groq, user_input: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return message.content or "(no response text)"

        for call in message.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)

            print(f"[tool] {name}({args})")
            try:
                result = TOOLS[name]["handler"](**args)
                content = json.dumps(result)
            except Exception as exc:
                content = json.dumps({"error": str(exc)})

            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})


def main():
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("Set GROQ_API_KEY in your environment or .env file")

    client = Groq()
    print("AI Research Agent — ask about stocks/ETFs or GitHub repos. Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            reply = run_agent(client, user_input)
        except Exception as exc:
            reply = f"Error: {exc}"

        print(f"\n{reply}")


if __name__ == "__main__":
    main()
