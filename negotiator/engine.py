"""The negotiation loop: alternates turns between two agents until a deal, a rejection, or the round cap."""

from typing import List, Tuple

from .agent import NegotiatorAgent
from .protocol import Message, Performative


class NegotiationResult:
    def __init__(self, deal_reached: bool, final_price: float | None, transcript: List[Message], rounds_used: int):
        self.deal_reached = deal_reached
        self.final_price = final_price
        self.transcript = transcript
        self.rounds_used = rounds_used

    def summary(self) -> str:
        if self.deal_reached:
            return f"✅ Deal reached at ${self.final_price:,.2f} after {self.rounds_used} rounds."
        return f"❌ No deal after {self.rounds_used} rounds."


def run_negotiation(agent_a: NegotiatorAgent, agent_b: NegotiatorAgent, max_rounds: int = 10) -> NegotiationResult:
    history: List[Message] = []
    turn_order: Tuple[NegotiatorAgent, NegotiatorAgent] = (agent_a, agent_b)

    for round_num in range(1, max_rounds + 1):
        current = turn_order[(round_num - 1) % 2]
        other = agent_b if current is agent_a else agent_a
        msg = current.decide(history, round_num, other.name)
        history.append(msg)
        print(msg)
        print()

        if msg.performative == Performative.ACCEPT:
            return NegotiationResult(True, msg.price, history, round_num)
        if msg.performative == Performative.REJECT:
            return NegotiationResult(False, None, history, round_num)

    return NegotiationResult(False, None, history, max_rounds)
