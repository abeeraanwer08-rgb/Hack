"""Sahulat: explains official notices/bills in simple Urdu or English using Qwen on Alibaba Cloud.

Two modes:
  - Live mode (DASHSCOPE_API_KEY set): Qwen drives a tool-calling loop over sahulat.tools.
  - Mock mode (no key): a deterministic, rule-based fallback using the same tools, so the
    demo keeps working on a bad-WiFi stage and in CI without any secret.
"""
import os
import re

from . import tools

BASE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")
SYSTEM = (
    "You are Sahulat, a helpful assistant for people in Pakistan. Explain notices, bills and "
    "official letters in simple language. Reply in the user's language (Urdu or English). "
    "Give: 1) what it means, 2) what to do next, 3) deadlines. Use tools for fees, helplines, "
    "flood risk and relief camps; never invent numbers. You are not a lawyer; suggest verifying "
    "with the issuing office."
)
MAX_STEPS = 4
_URDU_RE = re.compile(r"[؀-ۿ]")
_DISTRICTS = sorted(tools.FLOOD_RISK, key=len, reverse=True)


def _client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url=BASE_URL)


def _is_urdu(text: str) -> bool:
    return bool(_URDU_RE.search(text))


def _find_district(text: str) -> str | None:
    low = text.lower()
    return next((d for d in _DISTRICTS if d in low), None)


def _mock_bill(text: str, urdu: bool) -> str:
    parsed = tools.extract_amount_and_days(text)
    if parsed["amount"] is not None and parsed["days_late"] is not None:
        fee = tools.calc_late_fee(parsed["amount"], parsed["days_late"])
        if urdu:
            return (
                f"یہ ایک بل کا نوٹس لگتا ہے۔ رقم: {fee['amount']:.0f} روپے، "
                f"{fee['days_late']} دن تاخیر سے۔ تخمینی جرمانہ: {fee['late_fee']:.0f} روپے۔ "
                f"کل واجب الادا: {fee['total_due']:.0f} روپے۔ جلد ادائیگی کریں تاکہ سپلائی بند نہ ہو۔"
            )
        return (
            f"This looks like a bill notice. Amount: Rs {fee['amount']:.0f}, "
            f"{fee['days_late']} day(s) late. Estimated late fee: Rs {fee['late_fee']:.0f}. "
            f"Total now due: Rs {fee['total_due']:.0f}. Pay soon to avoid disconnection."
        )
    base = "یہ بل کا نوٹس لگتا ہے۔ رقم اور تاخیر کے دن صاف نہیں مل سکے — براہ کرم چیک کر کے جلد ادائیگی کریں۔" if urdu \
        else "This looks like a bill notice, but I couldn't read the amount and days late clearly. Check them and pay soon."
    return base


def _mock_court(urdu: bool) -> str:
    if urdu:
        return ("یہ عدالتی نوٹس/سمن لگتا ہے۔ آپ کو مقررہ تاریخ پر عدالت میں پیش ہونا ضروری ہے، "
                "ورنہ یکطرفہ فیصلہ ہو سکتا ہے۔ یہ قانونی مشورہ نہیں — براہ کرم وکیل سے رجوع کریں۔")
    return ("This looks like a court notice/summon. You are required to appear on the given date, "
            "or the court may decide without you. This is not legal advice — please consult a lawyer.")


def _mock_tax(urdu: bool) -> str:
    if urdu:
        return ("یہ ٹیکس سے متعلق نوٹس لگتا ہے (غالباً FBR کی طرف سے)۔ مقررہ مدت میں ریٹرن فائل کریں "
                "تاکہ جرمانے سے بچا جا سکے۔ اپنے ٹیکس کنسلٹنٹ یا NADRA/FBR دفتر سے تصدیق کریں۔")
    return ("This looks like a tax notice (likely from FBR). File your return within the given "
            "deadline to avoid a penalty. Confirm details with a tax consultant or your FBR office.")


def _mock_flood(text: str, urdu: bool) -> str:
    district = _find_district(text)
    emergency = tools.find_helpline("emergency")
    relief = tools.find_helpline("relief")
    lines = []
    if urdu:
        lines.append(f"ہنگامی مدد: {emergency['service']} {emergency['number']} | امدادی ادارہ: {relief['service']} {relief['number']}")
    else:
        lines.append(f"Emergency: {emergency['service']} {emergency['number']} | Relief: {relief['service']} {relief['number']}")
    if district:
        risk = tools.flood_risk(district)
        camps = tools.nearest_relief_camp(district)
        if urdu:
            lines.append(f"{district.title()} کے لیے سیلاب کا خطرہ: {risk['risk']} (نمونہ ڈیٹا)۔")
        else:
            lines.append(f"Flood risk for {district.title()}: {risk['risk']} (sample data).")
        if camps["camps"]:
            names = ", ".join(c["name"] for c in camps["camps"])
            lines.append((f"قریبی کیمپ: {names}" if urdu else f"Nearest camp(s): {names}"))
    return " ".join(lines)


def _mock(question: str) -> str:
    """Offline, rule-based fallback so the demo never dies on stage or in CI."""
    urdu = _is_urdu(question)
    doc_type = tools.classify_document(question)["doc_type"]
    if doc_type in ("electricity_bill", "gas_bill"):
        return _mock_bill(question, urdu)
    if doc_type == "court_notice":
        return _mock_court(urdu)
    if doc_type == "tax_notice":
        return _mock_tax(urdu)
    if doc_type == "flood_alert" or any(w in question.lower() for w in ("flood", "emergency")):
        return _mock_flood(question, urdu)
    prefix = "[mock mode — set DASHSCOPE_API_KEY for full Qwen answers] "
    return prefix + ("Paste a bill, court notice, tax notice or flood alert and I'll explain it."
                      if not urdu else "کوئی بل، عدالتی نوٹس، ٹیکس نوٹس یا سیلاب الرٹ بھیجیں۔")


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
