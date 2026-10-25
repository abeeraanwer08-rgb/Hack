import json

from sahulat import tools
from sahulat.agent import ask
from sahulat.demo_data import EXAMPLES


def test_late_fee():
    assert tools.calc_late_fee(1000, 10)["late_fee"] == 10.0


def test_helpline():
    assert tools.find_helpline("emergency")["number"] == "1122"
    assert "error" in tools.find_helpline("nope")


def test_run_tool_bad_args():
    assert "error" in json.loads(tools.run_tool("calc_late_fee", "{}"))


def test_flood_risk_known_and_unknown():
    assert tools.flood_risk("Rajanpur")["risk"] == "high"
    assert tools.flood_risk("Nowhereistan")["risk"] == "unknown"


def test_nearest_relief_camp():
    camps = tools.nearest_relief_camp("Sukkur")["camps"]
    assert camps and "Sukkur" in camps[0]["name"]


def test_classify_document():
    assert tools.classify_document("Your electricity bill, meter reading enclosed")["doc_type"] == "electricity_bill"
    assert tools.classify_document("")["doc_type"] == "unknown"


def test_extract_amount_and_days():
    parsed = tools.extract_amount_and_days("Amount due: Rs. 8,450, 12 days late")
    assert parsed["amount"] == 8450.0
    assert parsed["days_late"] == 12


def test_mock_mode_flood(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    assert "1122" in ask("There is a flood emergency near us")


def test_mock_mode_bill(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    reply = ask("FINAL NOTICE - electricity bill. Amount due: Rs. 8,450. 12 days late.")
    assert "8450" in reply or "8,450" in reply


def test_mock_mode_court(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    reply = ask("You must appear in court for the hearing, a summon was issued")
    assert "court" in reply.lower()


def test_mock_mode_unknown_bilingual(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    assert "mock mode" in ask("hello").lower()


def test_lang_param_overrides_autodetect(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    bill = "Electricity bill. Amount due: Rs. 8,450. 12 days late."
    assert "روپے" in ask(bill, lang="ur")  # force Urdu on an English notice
    assert "Rs" in ask(bill, lang="en")     # force English explicitly


def test_demo_examples_cover_all_doc_types():
    detected = {tools.classify_document(ex["text"])["doc_type"] for ex in EXAMPLES}
    assert {"electricity_bill", "court_notice", "flood_alert", "tax_notice"} <= detected
