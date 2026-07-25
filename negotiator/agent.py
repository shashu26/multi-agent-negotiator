"""
NegotiatorAgent: a single party in the negotiation.

Each agent has a private reservation price (the point past which it will
never go) and a target price (what it's hoping for). It decides its next
move either by calling an LLM (Claude) to reason about the negotiation
history, or — if no API key is configured — by falling back to a simple
concession-curve heuristic so the whole project still runs end-to-end
with zero setup.
"""

import json
import os
import random
from typing import List, Optional

from .protocol import Message, Performative


SYSTEM_PROMPT_TEMPLATE = """You are {name}, a {role} negotiating over: {item}.
Your reservation price (walk-away point) is ${reservation:,.2f}. You must never agree to a deal worse than this for you.
Your target price is ${target:,.2f}.
Your negotiating style is: {style}.

You will be shown the negotiation history so far. Respond with a single JSON object only, no other text:
{{
  "performative": "propose" | "counter" | "accept" | "reject",
  "price": <number or null>,
  "content": "<one short sentence of in-character reasoning to say to the other party>"
}}

Rules:
- Use "accept" only if the other side's last offer is at or better than your reservation price.
- Use "reject" only if you believe no further negotiation is worthwhile.
- Otherwise use "propose" (opening move) or "counter" (responding with a new price).
- Never reveal your exact reservation price in "content".
"""


class NegotiatorAgent:
    def __init__(
        self,
        name: str,
        role: str,
        item: str,
        reservation_price: float,
        target_price: float,
        style: str = "reasonable and cooperative, but firm",
        model: str = "claude-sonnet-4-6",
    ):
        self.name = name
        self.role = role  # "buyer" or "seller"
        self.item = item
        self.reservation_price = reservation_price
        self.target_price = target_price
        self.style = style
        self.model = model
        self._client = self._maybe_build_client()

    def _maybe_build_client(self):
        """Build an Anthropic client if a key is available; otherwise run in heuristic-only mode."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        try:
            import anthropic  # imported lazily so the project runs without the package too
            return anthropic.Anthropic(api_key=api_key)
        except ImportError:
            return None

    @property
    def is_llm_backed(self) -> bool:
        return self._client is not None

    def decide(self, history: List[Message], round_num: int, counterparty: str) -> Message:
        """Decide the next move given the negotiation history so far."""
        if self._client is not None:
            try:
                return self._decide_with_llm(history, round_num, counterparty)
            except Exception as e:  # network/parse errors -> fall back gracefully
                print(f"  [warn] {self.name}: LLM call failed ({e}); using heuristic fallback")
        return self._decide_with_heuristic(history, round_num, counterparty)

    # ---------- LLM-backed strategy ----------

    def _decide_with_llm(self, history: List[Message], round_num: int, counterparty: str) -> Message:
        system = SYSTEM_PROMPT_TEMPLATE.format(
            name=self.name,
            role=self.role,
            item=self.item,
            reservation=self.reservation_price,
            target=self.target_price,
            style=self.style,
        )
        transcript = "\n".join(str(m) for m in history) if history else "(no messages yet — you may open with a proposal)"

        response = self._client.messages.create(
            model=self.model,
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": f"Negotiation so far:\n{transcript}\n\nWhat is your next move?"}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        text = text.strip().strip("```json").strip("```").strip()
        data = json.loads(text)

        return Message(
            sender=self.name,
            receiver=counterparty,
            performative=Performative(data["performative"]),
            price=data.get("price"),
            content=data.get("content", ""),
            round=round_num,
        )

    # ---------- Deterministic fallback strategy (no API key needed) ----------

    def _decide_with_heuristic(self, history: List[Message], round_num: int, counterparty: str) -> Message:
        """
        Simple concession-curve negotiator: starts near its target price and
        concedes a fraction of the gap toward its reservation price each round,
        accepting once the other side's offer crosses its reservation price.
        """
        last_from_other = next((m for m in reversed(history) if m.sender != self.name), None)
        other_name = counterparty

        # Opening move
        if last_from_other is None:
            return Message(
                sender=self.name, receiver=other_name,
                performative=Performative.PROPOSE, price=self.target_price,
                content=f"Here's my opening offer for the {self.item}.",
                round=round_num,
            )

        # Accept if the other side's offer already clears our reservation price
        if self._is_acceptable(last_from_other.price):
            return Message(
                sender=self.name, receiver=other_name,
                performative=Performative.ACCEPT, price=last_from_other.price,
                content="That works for me — deal.",
                round=round_num,
            )

        # Otherwise concede a portion of the remaining gap
        concession_fraction = min(0.15 + 0.05 * round_num, 0.5)
        gap = self.reservation_price - self.target_price
        new_price = self.target_price + gap * concession_fraction * round_num
        new_price = self._clamp_to_reservation(new_price)

        # Stop after too many rounds with no progress
        if round_num >= 8:
            return Message(
                sender=self.name, receiver=other_name,
                performative=Performative.REJECT, price=None,
                content="We're too far apart — I'll walk away from this one.",
                round=round_num,
            )

        return Message(
            sender=self.name, receiver=other_name,
            performative=Performative.COUNTER, price=round(new_price, 2),
            content="Here's a counter — let's find something that works for both of us.",
            round=round_num,
        )

    def _is_acceptable(self, price: Optional[float]) -> bool:
        if price is None:
            return False
        if self.role == "buyer":
            return price <= self.reservation_price
        return price >= self.reservation_price

    def _clamp_to_reservation(self, price: float) -> float:
        if self.role == "buyer":
            return min(price, self.reservation_price)
        return max(price, self.reservation_price)

