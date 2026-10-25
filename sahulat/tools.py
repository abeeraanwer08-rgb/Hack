"""Tools the agent can call. Kept deterministic so answers are verifiable."""
import json

HELPLINES = {
    "emergency": ("Rescue 1122", "1122"),
    "police": ("Police", "15"),
    "ambulance": ("Edhi Foundation", "115"),
    "relief": ("Alkhidmat Foundation", "0800 44448"),
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


REGISTRY = {"calc_late_fee": calc_late_fee, "find_helpline": find_helpline}

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
]


def run_tool(name: str, arguments: str) -> str:
    fn = REGISTRY.get(name)
    if not fn:
        return json.dumps({"error": f"unknown tool {name}"})
    try:
        return json.dumps(fn(**json.loads(arguments or "{}")), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        return json.dumps({"error": str(e)})
