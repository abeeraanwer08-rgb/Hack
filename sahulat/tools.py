"""Tools the agent can call. Kept deterministic so answers are verifiable.

Flood-risk levels and relief-camp listings below are SAMPLE/ILLUSTRATIVE data
for demo purposes only -- wire them to NDMA/PDMA feeds before relying on them
for a real emergency.
"""
import json
import re

HELPLINES = {
    "emergency": ("Rescue 1122", "1122"),
    "police": ("Police", "15"),
    "ambulance": ("Edhi Foundation", "115"),
    "relief": ("Alkhidmat Foundation", "0800 44448"),
    "women": ("Women's Helpline", "1099"),
    "child": ("Child Protection (Madadgaar)", "1121"),
}

# Illustrative only -- replace with a live NDMA/PDMA feed for production use.
FLOOD_RISK = {
    "rajanpur": "high", "dera ghazi khan": "high", "jacobabad": "high",
    "kashmore": "high", "sukkur": "medium", "multan": "medium",
    "muzaffargarh": "medium", "karachi": "medium", "lahore": "low",
    "islamabad": "low", "peshawar": "low",
}

RELIEF_CAMPS = {
    "rajanpur": [{"name": "Alkhidmat Relief Camp - Rajanpur City", "capacity": 300}],
    "dera ghazi khan": [{"name": "Alkhidmat Relief Camp - DG Khan", "capacity": 250}],
    "sukkur": [{"name": "Alkhidmat Relief Camp - Sukkur Bypass", "capacity": 400}],
    "jacobabad": [{"name": "Alkhidmat Relief Camp - Jacobabad", "capacity": 200}],
}

DOC_KEYWORDS = {
    "electricity_bill": ["electricity", "wapda", "kwh", "meter reading", "بجلی", "یونٹ"],
    "gas_bill": ["gas bill", "sui gas", "mmbtu", "گیس کا بل"],
    "court_notice": ["court", "hearing", "summon", "adalat", "عدالت", "پیشی"],
    "tax_notice": ["fbr", "income tax", "tax year", "nadra", "ٹیکس"],
    "flood_alert": ["flood", "flooding", "سیلاب", "ندی", "دریا"],
}


def calc_late_fee(amount: float, days_late: int, daily_rate_percent: float = 0.1) -> dict:
    """Simple late-fee estimate: amount * rate% per day."""
    fee = round(amount * (daily_rate_percent / 100) * max(days_late, 0), 2)
    return {"amount": amount, "days_late": days_late, "late_fee": fee, "total_due": round(amount + fee, 2)}


def find_helpline(topic: str) -> dict:
    name, number = HELPLINES.get(topic.lower(), (None, None))
    if not name:
        return {"error": f"unknown topic; choose one of {sorted(HELPLINES)}"}
    return {"service": name, "number": number}


def flood_risk(district: str) -> dict:
    """Illustrative flood-risk lookup. Swap for a live NDMA/PDMA feed in production."""
    level = FLOOD_RISK.get(district.strip().lower())
    if not level:
        return {"district": district, "risk": "unknown", "note": "not in sample data"}
    return {"district": district, "risk": level, "source": "illustrative sample data"}


def nearest_relief_camp(district: str) -> dict:
    """Illustrative relief-camp lookup. Swap for a live NDMA/PDMA feed in production."""
    camps = RELIEF_CAMPS.get(district.strip().lower(), [])
    if not camps:
        return {"district": district, "camps": [], "note": "none in sample data; call the relief helpline"}
    return {"district": district, "camps": camps, "source": "illustrative sample data"}


def classify_document(text: str) -> dict:
    """Keyword-based guess at what kind of notice/bill this is. No AI call needed."""
    low = text.lower()
    scores = {kind: sum(1 for kw in kws if kw in low) for kind, kws in DOC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return {"doc_type": "unknown", "matched_keywords": []}
    matched = [kw for kw in DOC_KEYWORDS[best] if kw in low]
    return {"doc_type": best, "matched_keywords": matched}


def extract_amount_and_days(text: str) -> dict:
    """Best-effort regex pull of an amount (Rs ####) and a day count from free text."""
    amount_m = re.search(r"(?:rs\.?|pkr|rupees)\s*([\d,]+)", text, re.I)
    days_m = re.search(r"(\d+)\s*(?:days?|din|دن)", text, re.I)
    return {
        "amount": float(amount_m.group(1).replace(",", "")) if amount_m else None,
        "days_late": int(days_m.group(1)) if days_m else None,
    }


REGISTRY = {
    "calc_late_fee": calc_late_fee,
    "find_helpline": find_helpline,
    "flood_risk": flood_risk,
    "nearest_relief_camp": nearest_relief_camp,
    "classify_document": classify_document,
}

SCHEMAS = [
    {"type": "function", "function": {
        "name": "calc_late_fee",
        "description": "Estimate the late fee and total due for a bill or notice.",
        "parameters": {"type": "object", "properties": {
            "amount": {"type": "number"},
            "days_late": {"type": "integer"},
            "daily_rate_percent": {"type": "number"}},
            "required": ["amount", "days_late"]}}},
    {"type": "function", "function": {
        "name": "find_helpline",
        "description": "Look up a Pakistani emergency or relief helpline.",
        "parameters": {"type": "object", "properties": {
            "topic": {"type": "string", "enum": sorted(HELPLINES)}},
            "required": ["topic"]}}},
    {"type": "function", "function": {
        "name": "flood_risk",
        "description": "Look up the flood-risk level for a Pakistani district (sample data).",
        "parameters": {"type": "object", "properties": {
            "district": {"type": "string"}}, "required": ["district"]}}},
    {"type": "function", "function": {
        "name": "nearest_relief_camp",
        "description": "Find relief camps in a Pakistani district (sample data).",
        "parameters": {"type": "object", "properties": {
            "district": {"type": "string"}}, "required": ["district"]}}},
    {"type": "function", "function": {
        "name": "classify_document",
        "description": "Classify a pasted notice/bill into a document type.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string"}}, "required": ["text"]}}},
]


def run_tool(name: str, arguments: str) -> str:
    fn = REGISTRY.get(name)
    if not fn:
        return json.dumps({"error": f"unknown tool {name}"})
    try:
        return json.dumps(fn(**json.loads(arguments or "{}")), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        return json.dumps({"error": str(e)})
