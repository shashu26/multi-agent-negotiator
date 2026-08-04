# multi-agent-negotiator

Two autonomous agents negotiate a deal over a simple **agent-to-agent (A2A)
message protocol** — no shared state, no direct function calls between them,
just typed messages passed back and forth until they reach a deal, one side
walks away, or a round cap is hit.

Each agent can be **LLM-backed** (uses Claude to reason about strategy each
turn) or fall back to a **deterministic concession-curve heuristic** with zero
setup, so the whole thing runs out of the box with no API key required.

## Why this exists

This is a small, self-contained demo of agentic AI patterns — structured
inter-agent messaging (A2A), autonomous decision-making under private
constraints, and graceful degradation when an LLM isn't available — built as
a portfolio project.

## Quickstart

```bash
pip install -r requirements.txt   # only needed for LLM-backed mode
python -m negotiator.cli
```

Example output:

```
Starting negotiation over: a vintage acoustic guitar
Mode: heuristic fallback (no ANTHROPIC_API_KEY found)

[round 1] BuyerAgent -> SellerAgent :: PROPOSE ($300.00)
    "Here's my opening offer for the a vintage acoustic guitar."

[round 2] SellerAgent -> BuyerAgent :: COUNTER ($440.00)
    "Here's a counter — let's find something that works for both of us."

[round 3] BuyerAgent -> SellerAgent :: ACCEPT ($440.00)
    "That works for me — deal."

✅ Deal reached at $440.00 after 3 rounds.
```

## Run with a real LLM

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m negotiator.cli --item "a 2018 Honda Civic" \
  --buyer-target 12000 --buyer-max 15000 \
  --seller-target 17000 --seller-min 13500
```

With a key set, each agent calls Claude to reason about the negotiation
history and decide its next move — still returning the same structured
protocol messages, so the transcript format stays identical either way.

## Protocol

Every message is one of:

| Performative | Meaning |
|---|---|
| `propose` | Opening offer |
| `counter` | A revised offer in response to the other side |
| `accept` | Accepts the other side's last offer — ends the negotiation |
| `reject` | Walks away — ends the negotiation |
| `inform` | Non-binding side information |

See [`negotiator/protocol.py`](negotiator/protocol.py) for the full schema.

## Project structure

```
negotiator/
  protocol.py   # Message + Performative definitions (the A2A wire format)
  agent.py      # NegotiatorAgent — LLM-backed strategy + heuristic fallback
  engine.py     # Turn-taking negotiation loop
  cli.py        # Command-line entry point
test_negotiator.py
```

## Possible extensions

- Multi-issue negotiation (price + delivery date + warranty, not just price)
- Three or more agents negotiating simultaneously
- Persisting transcripts and visualizing concession curves over rounds
- Swapping in other model providers behind the same `NegotiatorAgent` interface

## License

MIT
