import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq
from tabulate import tabulate

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
    "results, always use the actual figures returned by the tool. "
    "Tables for calculate_returns and compare_securities are already printed "
    "directly to the terminal — do NOT reproduce the data in your reply. "
    "Just add a brief commentary below."
)


def _fmt_pct(value) -> str:
    if value is None:
        return "—"
    return f"+{value:.2f}%" if value >= 0 else f"{value:.2f}%"


def _fmt_usd(value, sign=False) -> str:
    if value is None:
        return "—"
    if value < 0:
        return f"-${abs(value):,.0f}"
    return f"+${value:,.0f}" if sign else f"${value:,.0f}"


def print_tool_table(name: str, result) -> None:
    """Pretty-print calculate_returns and compare_securities results as aligned tables."""
    if name == "calculate_returns" and isinstance(result, list):
        rows = []
        headers = None
        for item in result:
            if "error" in item:
                rows.append([item["symbol"], "ERROR", item["error"], "", ""])
                continue
            for period, data in item.get("periods", {}).items():
                if data is None:
                    continue
                if headers is None:
                    headers = ["Symbol", "Name", "Period", "Return %", "Gain / Loss", "End Value"]
                rows.append([
                    item["symbol"],
                    (item.get("name") or "")[:28],
                    period,
                    _fmt_pct(data["total_return_pct"]),
                    _fmt_usd(data["gain_loss"], sign=True),
                    _fmt_usd(data["end_value"]),
                ])
        if rows and headers:
            print()
            print(tabulate(rows, headers=headers, tablefmt="simple", colalign=("left", "left", "left", "right", "right", "right")))

    elif name == "compare_securities" and isinstance(result, list):
        rows = []
        headers = ["Symbol", "Name", "Price", "Exp. Ratio", "Div. Yield", "1y Return", "3y Return", "5y Return"]
        for item in result:
            if "error" in item:
                rows.append([item["symbol"], "ERROR"] + [""] * 6)
                continue
            perf = item.get("historical_performance_pct", {})
            rows.append([
                item["symbol"],
                (item.get("name") or "")[:28],
                _fmt_usd(item.get("price"), sign=False),
                f"{item['expense_ratio_pct']:.4f}%" if item.get("expense_ratio_pct") is not None else "—",
                _fmt_pct(item.get("dividend_yield_pct")),
                _fmt_pct(perf.get("1y")),
                _fmt_pct(perf.get("3y")),
                _fmt_pct(perf.get("5y")),
            ])
        if rows:
            print()
            print(tabulate(rows, headers=headers, tablefmt="simple", colalign=("left", "left", "right", "right", "right", "right", "right", "right")))


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
                print_tool_table(name, result)
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
