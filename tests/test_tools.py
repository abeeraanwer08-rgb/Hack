import json

from sahulat import tools
from sahulat.agent import ask


def test_late_fee():
    assert tools.calc_late_fee(1000, 10)["late_fee"] == 10.0


def test_helpline():
    assert tools.find_helpline("emergency")["number"] == "1122"
    assert "error" in tools.find_helpline("nope")


def test_run_tool_bad_args():
    assert "error" in json.loads(tools.run_tool("calc_late_fee", "{}"))


def test_mock_mode(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    assert "1122" in ask("flood help")
