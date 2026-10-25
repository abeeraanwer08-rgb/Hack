"""Sahulat: explains official notices/bills in simple Urdu or English using Qwen on Alibaba Cloud."""
import os

from . import tools

BASE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")
SYSTEM = (
    "You are Sahulat, a helpful assistant for people in Pakistan. Explain notices, bills and "
    "official letters in simple language. Reply in the user's language (Urdu or English). "
    "Give: 1) what it means, 2) what to do next, 3) deadlines. Use tools for fees and helplines; "
    "never invent numbers. You are not a lawyer; suggest verifying with the issuing office."
)
MAX_STEPS = 4


def _client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url=BASE_URL)


def _mock(question: str) -> str:
    """Offline fallback so the demo never dies on stage."""
    q = question.lower()
    if any(w in q for w in ("flood", "emergency", "سیلاب")):
        return f"Emergency help: {tools.find_helpline('emergency')}; relief: {tools.find_helpline('relief')}"
    return "[mock mode: set DASHSCOPE_API_KEY to use Qwen] Paste a notice or bill and ask what to do."


def ask(question: str, history: list | None = None) -> str:
    if not os.environ.get("DASHSCOPE_API_KEY"):
        return _mock(question)
    client = _client()
    messages = [{"role": "system", "content": SYSTEM}, *(history or []), {"role": "user", "content": question}]
    for _ in range(MAX_STEPS):
        msg = client.chat.completions.create(model=MODEL, messages=messages, tools=tools.SCHEMAS).choices[0].message
        if not msg.tool_calls:
            return msg.content
        messages.append(msg)
        for call in msg.tool_calls:
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": tools.run_tool(call.function.name, call.function.arguments)})
    return msg.content or "Sorry, I could not finish. Please rephrase."
