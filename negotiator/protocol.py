"""
A minimal Agent-to-Agent (A2A) message protocol for negotiation.

Each message is a structured "performative" — a speech act — inspired by
FIPA-ACL and modern A2A agent-communication patterns. Agents only ever
communicate via these typed messages, never by mutating each other's state
directly, which keeps the two agents fully decoupled.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class Performative(str, Enum):
    PROPOSE = "propose"       # here's an offer
    COUNTER = "counter"       # here's a counter-offer
    ACCEPT = "accept"         # I accept your last offer
    REJECT = "reject"         # I reject and won't continue
    INFORM = "inform"         # side info / justification, non-binding


@dataclass
class Message:
    sender: str
    receiver: str
    performative: Performative
    price: Optional[float]
    content: str
    round: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "performative": self.performative.value,
            "price": self.price,
            "content": self.content,
            "round": self.round,
        }

    def __str__(self) -> str:
        price_str = f" (${self.price:,.2f})" if self.price is not None else ""
        return f"[round {self.round}] {self.sender} -> {self.receiver} :: {self.performative.value.upper()}{price_str}\n    \"{self.content}\""
