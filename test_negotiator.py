"""
Basic tests — run with: python -m pytest test_negotiator.py -v
(or just: python test_negotiator.py, which runs them without pytest)
"""

from negotiator.agent import NegotiatorAgent
from negotiator.engine import run_negotiation
from negotiator.protocol import Message, Performative


def test_message_str_includes_price():
    m = Message(sender="A", receiver="B", performative=Performative.PROPOSE, price=100.0, content="hi", round=1)
    assert "$100.00" in str(m)
    assert "PROPOSE" in str(m)


def test_heuristic_negotiation_reaches_deal_when_ranges_overlap():
    buyer = NegotiatorAgent(name="Buyer", role="buyer", item="widget", reservation_price=500, target_price=300)
    seller = NegotiatorAgent(name="Seller", role="seller", item="widget", reservation_price=350, target_price=450)
    result = run_negotiation(buyer, seller, max_rounds=10)
    assert result.deal_reached is True
    assert result.final_price is not None
    assert 350 <= result.final_price <= 500


def test_heuristic_negotiation_can_fail_when_no_overlap():
    buyer = NegotiatorAgent(name="Buyer", role="buyer", item="widget", reservation_price=100, target_price=80)
    seller = NegotiatorAgent(name="Seller", role="seller", item="widget", reservation_price=900, target_price=1000)
    result = run_negotiation(buyer, seller, max_rounds=8)
    assert result.deal_reached is False


def test_agent_falls_back_to_heuristic_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = NegotiatorAgent(name="Buyer", role="buyer", item="widget", reservation_price=100, target_price=80)
    assert agent.is_llm_backed is False


if __name__ == "__main__":
    import sys
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            if "monkeypatch" in t.__code__.co_varnames:
                class _MP:
                    def delenv(self, k, raising=False):
                        import os
                        os.environ.pop(k, None)
                t(_MP())
            else:
                t()
            print(f"PASS: {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
